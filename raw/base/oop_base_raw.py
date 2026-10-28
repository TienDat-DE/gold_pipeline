import logging
from datetime import datetime
from database.oop_connection import DatabaseManagerOOP
from database.queries import pipeline_log_query, error_log_query

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
        # Lấy dữ liệu từ bảng web_responses
        query = "SELECT response_id, response_body, source_url, created_at FROM web_responses WHERE run_id = %s"
        result = self.db.fetch_all(query, (run_id,))
        if result:
            return result[0] # Trả về (response_id, response_body, source_url, crawl_time)
        return None

    def process(self, run_id, date_key, data_date_str):
        # 1. Lấy dữ liệu HTML/JSON từ web_responses dựa trên run_id
        record = self.get_web_response(run_id)
        if not record:
            self.log_pipeline(run_id, 'fail', f'Không tìm thấy dữ liệu crawl cho {run_id}', date_key)
            logging.error(f"Không tìm thấy run_id: {run_id} trong bảng web_responses.")
            return False
            
        response_id, response_body, source_url, crawl_time = record
        self.log_pipeline(run_id, 'running', 'Bắt đầu bóc tách payload', date_key, source_url)
        
        # 2. Thực hiện bóc tách Payload thông qua logic của Class Con (BTMC)
        raw_payload = self.extract_payload(response_body)
        
        if raw_payload:
            status = 'success'
        else:
            status = 'fail'
            raw_payload = 'Lỗi trích xuất JSON'

        # 3. Insert dữ liệu thô vào raw_gold_price
        # CHÚ Ý: Bỏ qua raw_id (AUTO_INCREMENT) và created_at (DEFAULT_GENERATED)
        raw_query = """
            INSERT INTO raw_gold_price 
            (run_id, response_id, store_id, source_url, crawl_time, data_date, raw_payload, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        raw_values = (
            run_id, 
            response_id, 
            self.store_id, 
            source_url, 
            crawl_time, 
            data_date_str, 
            raw_payload, 
            status
        )
        self.db.execute_query(raw_query, raw_values)

        # 4. Ghi lỗi nếu quá trình bóc tách thất bại
        if status == 'fail':
            err_values = (
                run_id, None, self.store_id, None, self.job_name, 'parser', 
                'Payload rỗng hoặc lỗi bóc tách', '', source_url
            )
            self.db.execute_query(error_log_query, err_values)
            self.log_pipeline(run_id, 'fail', 'Bóc tách thất bại', date_key, source_url)
            return False
            
        self.log_pipeline(run_id, 'success', 'Bóc tách Raw thành công', date_key, source_url)
        return True

    def extract_payload(self, response_body):
        # Hàm này sẽ bị ghi đè bởi BtmcRawOOP
        raise NotImplementedError("Class Con phải tự viết logic parse!")