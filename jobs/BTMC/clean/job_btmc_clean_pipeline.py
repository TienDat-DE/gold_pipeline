import sys
import json
import logging
from datetime import datetime
from database.oop_connection import DatabaseManagerOOP

# Import 4 cỗ máy xử lý
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
        
        self.store_id = 1 # ID của BTMC
        self.source_url = "https://btmc.vn"

    def run_pipeline(self, run_id):
        logging.info(f"========== BẮT ĐẦU CLEAN PIPELINE | RUN_ID: {run_id} ==========")
        
        # 1. Lấy dữ liệu thô chưa xử lý
        query_raw = "SELECT raw_id, raw_payload, data_date FROM raw_gold_price WHERE run_id = %s AND status = 'success'"
        records = self.db.fetch_all(query_raw, (run_id,))
        
        if not records:
            logging.info("Không có dữ liệu thô cần xử lý.")
            return

        for row in records:
            raw_id, raw_payload_str, data_date = row[0], row[1], row[2]
            
            # ==========================================
            # BƯỚC 1 & 2: GỌT HTML & VALIDATE BASIC
            # ==========================================
            clean_json_str = self.cleaner.process_clean_raw_json(raw_payload_str)
            if not clean_json_str:
                self.log_error(run_id, raw_id, 'CLEAN_ERROR', 'Không thể bóc tách HTML')
                continue
                
            text_dict = json.loads(clean_json_str)
            
            is_basic_ok, basic_msg = self.basic_validator.validate(text_dict)
            if not is_basic_ok:
                # Bắn vào ERROR_LOG (Lỗi rỗng, lỗi sai format)
                self.log_error(run_id, raw_id, 'VALIDATE_BASIC_ERROR', basic_msg)
                continue

            # ==========================================
            # BƯỚC 3: NORMALIZE (ÉP KIỂU SỐ)
            # ==========================================
            is_norm_ok, normalized_dict, norm_msg = self.normalizer.normalize_payload(text_dict)
            if not is_norm_ok:
                # Bắn vào ERROR_LOG
                self.log_error(run_id, raw_id, 'NORMALIZE_ERROR', norm_msg)
                continue

            # ==========================================
            # BƯỚC 4: VALIDATE BUSINESS (LOGIC GIÁ)
            # ==========================================
            is_biz_ok, err_code, biz_msg = self.biz_validator.validate(run_id, normalized_dict)
            if not is_biz_ok:
                # Bắn vào ANOMALY_LOG (Lỗi nhảy giá bất thường, giá âm)
                self.log_anomaly(run_id, raw_id, data_date, err_code, biz_msg)
                continue

            # ==========================================
            # BƯỚC 5: LƯU STAGING VÀ DIM_GOLD_PRICE
            # ==========================================
            # Tách Dictionary thành các cặp Mua/Bán riêng biệt để lưu DB
            gold_pairs = [
                {'type_id': 'SJC', 'name': 'Vàng SJC', 'buy': normalized_dict.get('sjcmua'), 'sell': normalized_dict.get('sjcban')},
                {'type_id': 'NHAN', 'name': 'Vàng nhẫn trơn', 'buy': normalized_dict.get('btmcvangnhanmua'), 'sell': normalized_dict.get('btmcvangnhanban')}
            ]

            for item in gold_pairs:
                # Insert Staging
                self.insert_staging(run_id, raw_id, item['type_id'], data_date, item['buy'], item['sell'])
                
                # Insert Dim Gold Price (Bảng sạch rút gọn)
                self.insert_dim_price(data_date, item['name'], item['buy'], item['sell'])

            logging.info(f" -> [THÀNH CÔNG] RAW_ID {raw_id} đã được lưu vào Staging và Dim.")

    # ---------------------------------------------------------
    # CÁC HÀM HỖ TRỢ GHI DATABASE
    # ---------------------------------------------------------
    def log_error(self, run_id, raw_id, error_type, message):
        query = """
            INSERT INTO error_log (run_id, raw_id, store_id, job_name, error_type, error_message, created_at, source_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        self.db.execute_query(query, (run_id, raw_id, self.store_id, 'CLEAN_PIPELINE', error_type, message, datetime.now(), self.source_url))
        logging.error(f" [ERROR_LOG] {error_type}: {message}")

    def log_anomaly(self, run_id, raw_id, data_date, anomaly_type, message):
        query = """
            INSERT INTO anomaly_log (run_id, raw_id, store_id, source_url, data_date, anomaly_type, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        # Lưu ý: Ở đây ta lưu message vào một cột (có thể bạn cần thêm cột message vào bảng anomaly_log nếu chưa có)
        self.db.execute_query(query, (run_id, raw_id, self.store_id, self.source_url, data_date, anomaly_type, datetime.now()))
        logging.warning(f" [ANOMALY_LOG] {anomaly_type}: {message}")

    def insert_staging(self, run_id, raw_id, gold_type_id, data_date, buy, sell):
        query = """
            INSERT INTO staging_gold_price 
            (run_id, raw_id, store_id, gold_type_id, source_url, data_date, buy_price, sell_price, normalized_unit, quality_flag, create_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        self.db.execute_query(query, (
            run_id, raw_id, self.store_id, gold_type_id, self.source_url, data_date, 
            buy, sell, 'VND/lượng', 'good', datetime.now()
        ))

    def insert_dim_price(self, data_date, gold_type_name, buy, sell):
        query = """
            INSERT INTO dim_gold_price 
            (data_date, store, gold_type_name, buy_price, sell_price, normalized_unit, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        self.db.execute_query(query, (
            data_date, 'BTMC', gold_type_name, buy, sell, 'VND/lượng', datetime.now()
        ))

if __name__ == "__main__":
    # Test chạy Job
    job = JobBtmcCleanPipeline()
    job.run_pipeline(run_id="20261026_BTMC_01")