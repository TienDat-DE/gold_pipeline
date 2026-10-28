import traceback
import logging
from datetime import datetime
from database.oop_connection import DatabaseManagerOOP
from database.queries import error_log_query

class BaseValidateBusinessOOP:
    def __init__(self, store_id, job_name, min_price=10000000, max_price=500000000):
        self.store_id = store_id
        self.job_name = job_name
        self.min_price = min_price
        self.max_price = max_price
        self.db = DatabaseManagerOOP()

    def log_error(self, run_id, raw_id, error_type, error_msg, source_url):
        """Ghi lỗi cứng (sai ngày, nhảy vọt) vào error_log"""
        error_values = (
            run_id, raw_id, self.store_id, None, 
            self.job_name, error_type, error_msg, traceback.format_exc(), source_url
        )
        self.db.execute_query(error_log_query, error_values)
        logging.error(f" -> [LOG ERROR_LOG] {error_type}: {error_msg} | Source: {source_url}")

    def log_anomaly(self, run_id, raw_id, source_url, data_date, value, expected_range, anomaly_type):
        """Ghi cảnh báo bất thường vào anomaly_log (NẾU CẦN)"""
        # (record_hash_id để trống do bước này chưa chạy tới Hash)
        query = """
            INSERT INTO anomaly_log 
            (run_id, record_hash_id, store_id, gold_type_id, source_url, data_date, value, expected_range, anomaly_type, transaction_type)
            VALUES (%s, NULL, %s, NULL, %s, %s, %s, %s, %s, NULL)
        """
        values = (run_id, self.store_id, source_url, data_date, value, expected_range, anomaly_type)
        self.db.execute_query(query, values)
        logging.warning(f" -> [LOG ANOMALY] {anomaly_type}: Giá trị {value} nằm ngoài khoảng {expected_range}")

    def get_pairs_to_check(self):
        raise NotImplementedError("Class Con phải khai báo các cặp [Mua, Bán]!")

    def validate(self, run_id, raw_id, normalized_dict, source_url, is_debug=False):
        if is_debug:
            logging.info(f" -> Đang tiến hành validate_business cho raw_id: {raw_id}")

        # 1. DATETIME_FORMAT_MISMATCH
        try:
            date_part = run_id.split('_')[0]
            data_date = datetime.strptime(date_part, '%Y%m%d')
            data_date_str = data_date.strftime('%Y-%m-%d')
        except Exception as e:
            self.log_error(run_id, raw_id, 'DATETIME_FORMAT_MISMATCH', f'Mã run_id sai cấu trúc: {e}', source_url)
            return False

        # 2. WRONG_DATE_ERROR
        if data_date.date() > datetime.now().date():
            self.log_error(run_id, raw_id, 'WRONG_DATE_ERROR', f'Dữ liệu ngày {data_date_str} thuộc về tương lai.', source_url)
            return False

        # 3. PRICE_OUT_OF_BOUNDS (Ghi theo code cũ của bạn là ném vào error_log)
        pairs = self.get_pairs_to_check()
        for buy_key, sell_key in pairs:
            buy = normalized_dict.get(buy_key, 0)
            sell = normalized_dict.get(sell_key, 0)

            if not (self.min_price <= buy <= self.max_price) or not (self.min_price <= sell <= self.max_price):
                msg = f"Giá cặp '{buy_key}/{sell_key}' nhảy vọt vô lý: Mua {buy} | Bán {sell}"
                self.log_error(run_id, raw_id, 'PRICE_OUT_OF_BOUNDS', msg, source_url)
                return False
                
            if buy > sell:
                msg = f"Lỗi logic cửa hàng: Giá mua ({buy}) cao hơn bán ({sell}) tại '{buy_key}/{sell_key}'"
                self.log_error(run_id, raw_id, 'PRICE_OUT_OF_BOUNDS', msg, source_url)
                return False

        if is_debug:
            logging.info(" [VALIDATE BUSINESS SUCCESS] Dữ liệu an toàn logic tài chính. \n")
        return True