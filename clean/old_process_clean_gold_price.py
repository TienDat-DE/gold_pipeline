import json
import argparse
import sys  
from datetime import datetime
from database.connection import connection, cursor

from clean.clean_btmc_raw import process_clean_raw_json
from clean.validate_basic import validate_basic, insert_validation_error
from clean.normalize_price import normalize_price
from clean.validate_business import validate_business

def save_gold_staging_data(run_id, raw_id, store_id, source_url, data_date, product_results):
    """Ghi dữ liệu thô đã phân tách vào bảng staging_gold_price"""
    print(f"\n ->  Tiến hành lưu tầng trung gian (Staging) cho raw_id: {raw_id}")
    
    staging_insert_query = """
        INSERT INTO staging_gold_price (
            run_id, raw_id, store_id, gold_type_id, source_url, 
            data_date, buy_price, sell_price, normalized_unit, quality_flag
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    success_count = 0
    for prod in product_results:
        g_name = prod['gold_type_name']
        g_id = prod['gold_type_id']
        buy = prod['buy_price']
        sell = prod['sell_price']
        flag = prod['quality_flag']
        
        staging_values = (
            run_id, raw_id, store_id, g_id, source_url,        
            data_date, buy, sell, 'VND/lượng', flag               
        )
        try:
            cursor.execute(staging_insert_query, staging_values)
            success_count += 1
            print(f"    [STAGING OK] Đã nạp lịch sử: '{g_name}' | Trạng thái: [{flag.upper()}]")
        except Exception as db_err:
            print(f"    [LỖI STAGING DATABASE] Không thể insert '{g_name}': {db_err}")
            connection.rollback()
            return False
            
    if success_count > 0:
        connection.commit()
        return True
    return False

def save_gold_dim_data(data_date, product_results):
    """Ghi dữ liệu sạch tinh gọn vào bảng dim_gold_price sử dụng UPSERT thông minh"""
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
    success_count = 0
    
    for prod in product_results:
        store_name = "Bảo Tín Minh Châu"
        g_name = prod['gold_type_name']
        buy = prod['buy_price']
        sell = prod['sell_price']
        
        # Chỉ xử lý đồng bộ dữ liệu nếu sản phẩm đó không bị đánh dấu trống (missing)
        if prod['quality_flag'] != 'missing':
            dim_values = (data_date, store_name, g_name, buy, sell, 'VND/lượng', now_str)
            try:
                cursor.execute(dim_upsert_query, dim_values)
                success_count += 1
                print(f"    [DIM COORD] Thực thi UPSERT thành công cho loại hình: '{g_name}'")
            except Exception as db_err:
                print(f"    [LỖI DIM DATABASE] Không thể xử lý dữ liệu sạch '{g_name}': {db_err}")
                connection.rollback()
                return False
                
    if success_count > 0:
        connection.commit()
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Điều phối luồng nạp dữ liệu sạch clean_gold_price theo Run ID")
    parser.add_argument('--run_id', type=str, required=True, help="20260518_BTMC")
    args = parser.parse_args()

    # 1. Lấy dữ liệu mạng thô nguyên bản từ (raw_gold_price)
    query = "SELECT raw_id, run_id, store_id, source_url, raw_payload FROM raw_gold_price WHERE run_id = %s AND status = 'success' ORDER BY raw_id DESC LIMIT 1"
    cursor.execute(query, (args.run_id,))
    row = cursor.fetchone()

    if row:
        r_id, run_id_val, store_id_val, source_url_val, raw_payload_str = row[0], row[1], row[2], row[3], row[4]
        
        try:
            date_part = run_id_val.split('_')[0]
            data_date_val = datetime.strptime(date_part, '%Y%m%d').strftime('%Y-%m-%d')
        except:
            data_date_val = datetime.now().strftime('%Y-%m-%d')
            
        print(f"\n [PIPELINE START] Khởi động luồng làm sạch cho RUN_ID: {run_id_val}")
        print(f"--------------------------------------------------------------------")
        
        # Cấu trúc lưu trữ trạng thái cuối cùng của 2 sản phẩm vàng để chuẩn bị ghi DB
        final_products = [
            {'gold_type_id': 1, 'gold_type_name': 'Vàng SJC', 'buy_price': None, 'sell_price': None, 'quality_flag': 'good'},
            {'gold_type_id': 2, 'gold_type_name': 'Vàng nhẫn trơn', 'buy_price': None, 'sell_price': None, 'quality_flag': 'good'}
        ]

        # 1: Dọn dẹp thẻ HTML ngầm trên RAM
        cleaned_str = process_clean_raw_json(raw_payload_str)
        print(" [1/4]  Clean HTML Tags    -> Hoàn tất bóc tách thẻ <b> từ JSON thô.")
        
        try:
            cleaned_data = json.loads(cleaned_str) if cleaned_str else {}
        except:
            cleaned_data = {}

        # 2: KIỂM TRA VALIDATE BASIC CHO TỪNG SẢN PHẨM RIÊNG BIỆT
        # Tách biệt kiểm tra để nếu 1 trong 2 lỗi thì loại còn lại vẫn được chạy tiếp
        sjc_payload = json.dumps({'sjcmua': cleaned_data.get('sjcmua'), 'sjcban': cleaned_data.get('sjcban'), 'btmcvangnhanmua': '1', 'btmcvangnhanban': '1'}) # Trick pass required_keys độc lập
        nhan_payload = json.dumps({'sjcmua': '1', 'sjcban': '1', 'btmcvangnhanmua': cleaned_data.get('btmcvangnhanmua'), 'btmcvangnhanban': cleaned_data.get('btmcvangnhanban')})
        
        # SỬA LỖI NONE: Truyền tham số source_url_val trực tiếp vào hàm kiểm tra định dạng số/null
        sjc_basic_ok = validate_basic(run_id=run_id_val, raw_id=r_id, cleaned_payload_str=sjc_payload, source_url=source_url_val, is_debug=False)
        nhan_basic_ok = validate_basic(run_id=run_id_val, raw_id=r_id, cleaned_payload_str=nhan_payload, source_url=source_url_val, is_debug=False)
        
        # Xử lý gắn cờ hạ cấp chất lượng nếu sản phẩm bị lỗi
        if not sjc_basic_ok:
            final_products[0]['quality_flag'] = 'missing'
            insert_validation_error(run_id_val, r_id, 'DATA_MISSING_WARNING', "Sản phẩm Vàng SJC bị trống hoặc chứa ký tự lỗi số.", source_url_val)
            
        if not nhan_basic_ok:
            final_products[1]['quality_flag'] = 'missing'
            insert_validation_error(run_id_val, r_id, 'DATA_MISSING_WARNING', "Sản phẩm Vàng nhẫn trơn bị trống hoặc chứa ký tự lỗi số.", source_url_val)

        # Thông báo trạng thái Validate Basic 
        if final_products[0]['quality_flag'] == 'missing' and final_products[1]['quality_flag'] == 'missing':
            print(" [2/4]  Validate Basic     ->  THẤT BẠI: Cả 2 sản phẩm đều rỗng/lỗi số. Đã ghi error_log.")
        else:
            print(f" [2/4]  Validate Basic     -> Hoàn tất kiểm tra định dạng số (SJC: {'OK' if sjc_basic_ok else 'MISSING'} | Nhẫn: {'OK' if nhan_basic_ok else 'MISSING'}).")

        # 3: CHUẨN HÓA GIÁ NORMALIZE PRICE (CHỈ CHẠY CHO SẢN PHẨM KHÔNG BỊ MISSING)
        # Gọi hàm normalize gốc để bẻ mảng và nhân tiền 10,000
        normalized_list = normalize_price(run_id=run_id_val, raw_id=r_id, cleaned_payload_str=cleaned_str, is_debug=False)
        
        if normalized_list:
            for item in normalized_list:
                name = item['gold_type_name']
                if name == 'Vàng SJC' and final_products[0]['quality_flag'] != 'missing':
                    final_products[0]['buy_price'] = item['buy_price']
                    final_products[0]['sell_price'] = item['sell_price']
                elif name == 'Vàng nhẫn trơn' and final_products[1]['quality_flag'] != 'missing':
                    final_products[1]['buy_price'] = item['buy_price']
                    final_products[1]['sell_price'] = item['sell_price']
                    
        if final_products[0]['quality_flag'] == 'missing' and final_products[1]['quality_flag'] == 'missing':
            print(" [3/4]  Normalize Price    ->  BỎ QUA: Không có dữ liệu số hợp lệ để tính toán.")
        else:
            print(" [3/4]  Normalize Price    -> Hoàn tất chuẩn hoá")

        # 4: KIỂM TRA NGHIỆP VỤ VALIDATE BUSINESS (CHỈ CHẠY NẾU CÓ ÍT NHẤT 1 SẢN PHẨM CÓ GIÁ TRỊ)
        has_valid_data_for_business = any(p['buy_price'] is not None for p in final_products)
        
        if not has_valid_data_for_business:
            print(" [4/4]  Validate Business  ->  BỎ QUA: Không có sản phẩm nào đủ điều kiện check nghiệp vụ tài chính.")
        else:
            # Lọc ra danh sách sản phẩm tốt để ném vào hàm check business 
            valid_list_for_check = [
                {'gold_type_name': p['gold_type_name'], 'buy_price': p['buy_price'], 'sell_price': p['sell_price']}
                for p in final_products if p['buy_price'] is not None
            ]
            
            # Gọi hàm check trùng ngày tương lai, check giá trần sàn, check mua > bán
            business_ok = validate_business(run_id=run_id_val, raw_id=r_id, normalized_data_list=valid_list_for_check, is_debug=False)
            
            if not business_ok:
                print(" [4/4]  Validate Business  ->  PHÁT HIỆN DỊ THƯỜNG: Dữ liệu bị hạ cấp xuống [SUSPICIOUS].")
                # Nếu sai logic tài chính, toàn bộ các sản phẩm đang từ 'good' sẽ bị chuyển thành 'suspicious'
                for p in final_products:
                    if p['quality_flag'] == 'good':
                        p['quality_flag'] = 'suspicious'
            else:
                print(" [4/4]  Validate Business  -> Hoàn tất kiểm tra (Logic tài chính).")
                
        print(f"--------------------------------------------------------------------")
        
        # 5: LUÔN LUÔN CÁN ĐÍCH - GHI NHẬN KẾT QUẢ VÀO HAI TẦNG DATABASE MỚI
        # Bước 5.1: Nạp toàn bộ lịch sử biến động dữ liệu vào bảng Staging
        stg_success = save_gold_staging_data(
            run_id=run_id_val, raw_id=r_id, store_id=store_id_val,
            source_url=source_url_val, data_date=data_date_val, product_results=final_products
        )
        
        # Bước 5.2: Thực hiện UPSERT thông minh đẩy dữ liệu sạch sang bảng Dim
        dim_success = save_gold_dim_data(data_date=data_date_val, product_results=final_products)
        
        # Trả trạng thái Log tổng cho Hệ thống Pipeline Airflow
        if stg_success and dim_success:
            all_flags = [p['quality_flag'] for p in final_products]
            if 'good' in all_flags:
                try:
                    cursor.execute("UPDATE pipeline_log SET status = 'success' WHERE run_id = %s", (run_id_val,))
                    connection.commit()
                except: pass
            print(f" [HOÀN THÀNH] Tiến trình xử lý kết thúc thành công.")
            cursor.close()
            connection.close()
            print(f"====================================================================\n")
            sys.exit(0) # Trả về mã thành công 0 cho Airflow dắt luồng đi tiếp
        else:
            print(f" [THẤT BẠI] Quy trình gặp lỗi trong thao tác lưu dữ liệu tầng cuối.")
            cursor.close()
            connection.close()
            sys.exit(1) # Trả về mã lỗi 1 cho Airflow báo đỏ
        
    else:
        print(f"[THẤT BẠI] Không tìm thấy dữ liệu thô 'success' nào của ngày '{args.run_id}' trong DB.")
        cursor.close()
        connection.close()
        sys.exit(1) # Trả về mã lỗi 1 cho Airflow