import sys
import json
import argparse
import logging
from datetime import datetime
from database.oop_connection import DatabaseManagerOOP

# Kéo 4 cỗ máy xử lý OOP vào hệ thống
from clean.sites.BTMC.oop_btmc_cleaner import BtmcCleanerOOP
from clean.sites.BTMC.oop_btmc_validate_basic import BtmcValidateBasicOOP
from clean.sites.BTMC.oop_btmc_normalizer import BtmcNormalizerOOP
from clean.sites.BTMC.oop_btmc_validate_business import BtmcValidateBusinessOOP

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class JobBtmcCleanPipeline:
    def __init__(self):
        self.db = DatabaseManagerOOP()
        self.cleaner = BtmcCleanerOOP()
        self.basic_validator = BtmcValidateBasicOOP()
        self.normalizer = BtmcNormalizerOOP()
        self.biz_validator = BtmcValidateBusinessOOP()
        
        self.store_name = "Bảo Tín Minh Châu"

    def run_pipeline(self):
        parser = argparse.ArgumentParser(description="Điều phối luồng nạp dữ liệu sạch clean_gold_price theo Run ID")
        parser.add_argument('--run_id', type=str, required=True, help="Ví dụ: 20261028_BTMC")
        args = parser.parse_known_args()[0]
        run_id = args.run_id

        # Lấy dữ liệu mạng thô nguyên bản từ raw_gold_price
        query = """
            SELECT raw_id, store_id, source_url, raw_payload 
            FROM raw_gold_price 
            WHERE run_id = %s AND status = 'success' 
            ORDER BY raw_id DESC LIMIT 1
        """
        records = self.db.fetch_all(query, (run_id,))

        if not records:
            logging.error(f"[THẤT BẠI] Không tìm thấy dữ liệu thô 'success' nào của ngày '{run_id}' trong DB.")
            sys.exit(1)

        raw_id = records[0][0]
        store_id = records[0][1]
        source_url = records[0][2]
        raw_payload_str = records[0][3]

        try:
            date_part = run_id.split('_')[0]
            data_date = datetime.strptime(date_part, '%Y%m%d').strftime('%Y-%m-%d')
        except:
            data_date = datetime.now().strftime('%Y-%m-%d')
            
        print(f"\n [PIPELINE START] Khởi động luồng làm sạch cho RUN_ID: {run_id}")
        print(f"--------------------------------------------------------------------")
        
        # Cấu trúc lưu trữ trạng thái cuối cùng để chuẩn bị ghi DB
        final_products = [
            {'gold_type_id': 1, 'gold_type_name': 'Vàng SJC', 'buy_price': None, 'sell_price': None, 'quality_flag': 'good', 'keys': ('sjcmua', 'sjcban')},
            {'gold_type_id': 2, 'gold_type_name': 'Vàng nhẫn tròn trơn', 'buy_price': None, 'sell_price': None, 'quality_flag': 'good', 'keys': ('btmcvangnhanmua', 'btmcvangnhanban')}
        ]

        # ==========================================
        # BƯỚC 1: DỌN DẸP HTML
        # ==========================================
        cleaned_str = self.cleaner.process_clean_raw_json(raw_payload_str)
        print(" [1/4]  Clean HTML Tags    -> Hoàn tất bóc tách HTML từ JSON thô.")
        
        try:
            cleaned_data = json.loads(cleaned_str) if cleaned_str else {}
        except:
            cleaned_data = {}

        # ==========================================
        # BƯỚC 2: VALIDATE BASIC (Bắt rỗng, null, sai format)
        # ==========================================
        sjc_payload = json.dumps({'sjcmua': cleaned_data.get('sjcmua'), 'sjcban': cleaned_data.get('sjcban'), 'btmcvangnhanmua': '1', 'btmcvangnhanban': '1'})
        nhan_payload = json.dumps({'sjcmua': '1', 'sjcban': '1', 'btmcvangnhanmua': cleaned_data.get('btmcvangnhanmua'), 'btmcvangnhanban': cleaned_data.get('btmcvangnhanban')})
        
        sjc_basic_ok = self.basic_validator.validate(run_id, raw_id, sjc_payload, source_url, is_debug=False)
        nhan_basic_ok = self.basic_validator.validate(run_id, raw_id, nhan_payload, source_url, is_debug=False)
        
        if not sjc_basic_ok: final_products[0]['quality_flag'] = 'missing'
        if not nhan_basic_ok: final_products[1]['quality_flag'] = 'missing'

        if not sjc_basic_ok and not nhan_basic_ok:
            print(" [2/4]  Validate Basic     ->  THẤT BẠI: Cả 2 sản phẩm đều rỗng/lỗi số. (Đã ghi error_log).")
        else:
            print(f" [2/4]  Validate Basic     -> Hoàn tất kiểm tra định dạng (SJC: {'OK' if sjc_basic_ok else 'MISSING'} | Nhẫn: {'OK' if nhan_basic_ok else 'MISSING'}).")

        # ==========================================
        # BƯỚC 3: NORMALIZE (CHỈ ÉP KIỂU SẢN PHẨM ĐÃ PASS BƯỚC 2)
        # ==========================================
        valid_data_to_normalize = {}
        for prod in final_products:
            # Lọc phân luồng: Bỏ qua đồ hư hỏng (missing), chỉ gắp đồ sạch (good) nhét vào Normalizer
            if prod['quality_flag'] != 'missing':
                valid_data_to_normalize[prod['keys'][0]] = cleaned_data.get(prod['keys'][0])
                valid_data_to_normalize[prod['keys'][1]] = cleaned_data.get(prod['keys'][1])
                
        if not valid_data_to_normalize:
            print(" [3/4]  Normalize Price    ->  BỎ QUA: Không có dữ liệu số hợp lệ để tính toán.")
        else:
            normalized_dict = self.normalizer.normalize_payload(valid_data_to_normalize)
            for prod in final_products:
                if prod['quality_flag'] != 'missing':
                    prod['buy_price'] = normalized_dict.get(prod['keys'][0])
                    prod['sell_price'] = normalized_dict.get(prod['keys'][1])
            print(" [3/4]  Normalize Price    -> Hoàn tất chuẩn hoá số nguyên.")

        # ==========================================
        # BƯỚC 4: VALIDATE BUSINESS (LOGIC GIÁ CẢ)
        # ==========================================
        has_valid_data = any(p['quality_flag'] != 'missing' for p in final_products)
        
        if not has_valid_data:
            print(" [4/4]  Validate Business  ->  BỎ QUA: Không có sản phẩm nào đủ điều kiện check nghiệp vụ.")
        else:
            valid_norm_dict = {}
            for prod in final_products:
                if prod['quality_flag'] != 'missing':
                    valid_norm_dict[prod['keys'][0]] = prod['buy_price']
                    valid_norm_dict[prod['keys'][1]] = prod['sell_price']
            
            business_ok = self.biz_validator.validate(run_id, raw_id, valid_norm_dict, source_url, is_debug=False)
            
            if not business_ok:
                print(" [4/4]  Validate Business  ->  PHÁT HIỆN DỊ THƯỜNG: Dữ liệu bị hạ cấp xuống [SUSPICIOUS].")
                for p in final_products:
                    if p['quality_flag'] == 'good':
                        p['quality_flag'] = 'suspicious'
            else:
                print(" [4/4]  Validate Business  -> Hoàn tất kiểm tra (Logic tài chính an toàn).")
                
        print(f"--------------------------------------------------------------------")
        
        # ==========================================
        # BƯỚC 5: ĐỔ DỮ LIỆU XUỐNG DB TẦNG CUỐI
        # ==========================================
        stg_success = self.save_gold_staging_data(run_id, raw_id, store_id, source_url, data_date, final_products)
        dim_success = self.save_gold_dim_data(data_date, final_products)
        
        if stg_success and dim_success:
            print(f" [HOÀN THÀNH] Tiến trình xử lý kết thúc thành công.")
            print(f"====================================================================\n")
            sys.exit(0)
        else:
            print(f" [THẤT BẠI] Quy trình gặp lỗi trong thao tác lưu dữ liệu tầng cuối.")
            sys.exit(1)

    def save_gold_staging_data(self, run_id, raw_id, store_id, source_url, data_date, product_results):
        print(f"\n ->  Tiến hành lưu tầng trung gian (Staging) cho raw_id: {raw_id}")
        
        staging_insert_query = """
            INSERT INTO staging_gold_price (
                run_id, raw_id, store_id, gold_type_id, source_url, 
                data_date, buy_price, sell_price, normalized_unit, quality_flag
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        success_count = 0
        for prod in product_results:
            try:
                staging_values = (
                    run_id, raw_id, store_id, prod['gold_type_id'], source_url,        
                    data_date, prod['buy_price'], prod['sell_price'], 'VND/lượng', prod['quality_flag']               
                )
                self.db.execute_query(staging_insert_query, staging_values)
                success_count += 1
                print(f"    [STAGING OK] Đã nạp dữ liệu: '{prod['gold_type_name']}' | Trạng thái: [{prod['quality_flag'].upper()}]")
            except Exception as db_err:
                print(f"    [LỖI STAGING DATABASE] Không thể insert '{prod['gold_type_name']}': {db_err}")
                return False
                
        return success_count > 0

    def save_gold_dim_data(self, data_date, product_results):
        print(f" ->  Tiến hành kiểm tra đồng bộ sang kho dữ liệu dim_gold_price...")
        
        dim_upsert_query = """
            INSERT INTO dim_gold_price (data_date, store, gold_type_name, buy_price, sell_price, normalized_unit, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                updated_at = IF(buy_price != VALUES(buy_price) OR sell_price != VALUES(sell_price), VALUES(updated_at), updated_at),
                buy_price = IF(buy_price != VALUES(buy_price) OR sell_price != VALUES(sell_price), VALUES(buy_price), buy_price),
                sell_price = IF(buy_price != VALUES(buy_price) OR sell_price != VALUES(sell_price), VALUES(sell_price), sell_price);
        """
        
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for prod in product_results:
            if prod['quality_flag'] != 'missing':
                try:
                    dim_values = (data_date, self.store_name, prod['gold_type_name'], prod['buy_price'], prod['sell_price'], 'VND/lượng', now_str)
                    self.db.execute_query(dim_upsert_query, dim_values)
                    print(f"    [DIM COORD] Thực thi UPSERT thành công cho loại hình: '{prod['gold_type_name']}'")
                except Exception as db_err:
                    print(f"    [LỖI DIM DATABASE] Không thể xử lý dữ liệu sạch '{prod['gold_type_name']}': {db_err}")
                    return False
        return True

if __name__ == "__main__":
    job = JobBtmcCleanPipeline()
    job.run_pipeline()