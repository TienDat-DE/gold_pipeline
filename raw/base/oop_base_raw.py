import logging
import sys
import traceback
from datetime import datetime
from database.oop_connection import DatabaseManagerOOP
from database.queries import pipeline_log_query, error_log_query

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class BaseRawOOP:
    def __init__(self, job_name, store_id):
        self.job_name = job_name
        self.store_id = store_id
        self.db = DatabaseManagerOOP()

    def log_pipeline(self, run_id, status, message, date_key, source_url=None):
        values = (
            run_id, self.store_id, None, self.job_name, 'raw', 
            status, message, datetime.now(), None, source_url, date_key
        )
        self.db.execute_query(pipeline_log_query, values)

    def get_web_response(self, run_id):
        # Nâng cấp: Luôn lấy bản ghi mới nhất theo đúng thiết kế cũ
        query = """
            SELECT response_id, response_body, source_url, created_at 
            FROM web_responses 
            WHERE run_id = %s 
            ORDER BY response_id DESC 
            LIMIT 1
        """
        result = self.db.fetch_all(query, (run_id,))
        if result:
            return result[0] # (response_id, response_body, source_url, crawl_time)
        return None

    def process(self, run_id, date_key, data_date_str):
        record = self.get_web_response(run_id)
        if not record:
            self.log_pipeline(run_id, 'fail', f'Không tìm thấy web_responses cho {run_id}', date_key)
            logging.error(f"[THẤT BẠI] Không tìm thấy dữ liệu mạng của ngày '{run_id}' trong bảng web_responses.")
            return False
            
        response_id, response_body, source_url, crawl_time = record
        self.log_pipeline(run_id, 'running', 'Bắt đầu bóc tách payload', date_key, source_url)
        
        raw_payload = None
        status = 'success'
        error_msg = ''
        stack_trace = None

        # Đẩy việc bắt lỗi ra Class Base để lấy được traceback chuẩn
        try:
            raw_payload = self.extract_payload(response_body)
            if not raw_payload:
                status = 'fail'
                error_msg = 'Payload trích xuất từ key Data bị rỗng'
        except Exception as e:
            status = 'fail'
            error_msg = f'Lỗi giải nén chuỗi JSON: {e}'
            stack_trace = traceback.format_exc()

        # Insert vào raw_gold_price
        raw_query = """
            INSERT INTO raw_gold_price 
            (run_id, response_id, store_id, source_url, crawl_time, data_date, raw_payload, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        try:
            self.db.execute_query(raw_query, (run_id, response_id, self.store_id, source_url, crawl_time, data_date_str, raw_payload, status))
        except Exception as db_err:
            logging.error(f" -> Lỗi database khi ghi raw_gold_price: {db_err}")
            return False

        if status == 'fail':
            err_values = (
                run_id, None, self.store_id, None, self.job_name, 'JSON_PARSE_ERROR', 
                error_msg, stack_trace, source_url
            )
            self.db.execute_query(error_log_query, err_values)
            self.log_pipeline(run_id, 'fail', 'Bóc tách thất bại', date_key, source_url)
            return False
            
        self.log_pipeline(run_id, 'success', 'Bóc tách Raw thành công', date_key, source_url)
        logging.info(" -> Trích xuất khối JSON Data thô thành công.")
        return True

    def extract_payload(self, response_body):
        raise NotImplementedError