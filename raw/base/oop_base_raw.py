import logging
import sys
import traceback
from datetime import datetime
from database.oop_connection import DatabaseManagerOOP

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class BaseRawOOP:
    def __init__(self, job_name, store_id):
        self.job_name = job_name
        self.store_id = store_id
        self.db = DatabaseManagerOOP()

    def get_web_response(self, run_id):
        query = """
            SELECT response_id, response_body, source_url, created_at 
            FROM web_responses 
            WHERE run_id = %s 
            ORDER BY response_id DESC 
            LIMIT 1
        """
        result = self.db.fetch_all(query, (run_id,))
        if result:
            return result[0]
        return None

    def process(self, run_id, date_key, data_date_str):
        record = self.get_web_response(run_id)
        if not record:
            logging.error(f"[THẤT BẠI] Không tìm thấy dữ liệu mạng của ngày '{run_id}'.")
            return False
            
        response_id, response_body, source_url, crawl_time = record
        
        raw_payload = None
        status = 'success'
        error_msg = ''
        stack_trace = None

        try:
            raw_payload = self.extract_payload(response_body)
            if not raw_payload:
                status = 'fail'
                error_msg = 'Payload trích xuất bị rỗng'
        except Exception as e:
            status = 'fail'
            error_msg = f'Lỗi giải nén JSON: {e}'
            stack_trace = traceback.format_exc()

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
            err_query = """
                INSERT INTO error_log 
                (run_id, store_id, job_name, error_type, error_message, stack_trace, source_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            err_values = (run_id, self.store_id, self.job_name, 'JSON_PARSE_ERROR', error_msg, stack_trace, source_url)
            self.db.execute_query(err_query, err_values)
            return False
            
        logging.info(" -> Trích xuất khối JSON Data thô thành công.")
        return True

    def extract_payload(self, response_body):
        raise NotImplementedError