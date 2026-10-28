import argparse
import time
import sys
import traceback
import tls_client
import logging
from datetime import datetime

from database.oop_connection import DatabaseManagerOOP

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class BaseCrawlerOOP:
    def __init__(self, job_name, store_id, store_name, api_url):
        self.job_name = job_name
        self.store_id = store_id
        self.store_name = store_name
        self.api_url = api_url
        self.db = DatabaseManagerOOP()
        
        self.formatted_date, self.run_id, self.date_key = self.parse_arguments()
        self.max_retry = 5
        self.timeout_sec = 60

        self.session = tls_client.Session(client_identifier="chrome_120", random_tls_extension_order=True)
        # Class con sẽ ghi đè headers riêng
        self.headers = {} 

    def parse_arguments(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--date', type=str, default=datetime.now().strftime('%Y%m%d'))
        args = parser.parse_known_args()[0]
        
        if len(args.date) != 8 or not args.date.isdigit():
            logging.error(f"[LỖI NGHIÊM TRỌNG] Ngày truyền vào '{args.date}' không hợp lệ!")
            sys.exit(1)
            
        fmt_date = f"{args.date[6:8]}/{args.date[4:6]}/{args.date[0:4]}"
        run_id = f"{args.date}_{self.store_name}" 
        date_key = int(args.date) 
        return fmt_date, run_id, date_key       

    def log_pipeline(self, status, message=""):
        query = """
            INSERT INTO pipeline_log 
            (run_id, store_id, gold_type_id, job_name, step, status, message, start_time, source_url, date_key)
            VALUES (%s, %s, NULL, %s, 'crawl', %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE status = VALUES(status), message = VALUES(message)
        """
        values = (self.run_id, self.store_id, self.job_name, status, message, datetime.now(), self.api_url, self.date_key)
        self.db.execute_query(query, values)

    def log_error(self, error_type, error_msg, stack_trace, source_url):
        """Khớp 100% cấu trúc error_log. Ở phase Crawl, raw_id và gold_type_id = NULL"""
        query = """
            INSERT INTO error_log 
            (run_id, raw_id, store_id, gold_type_id, job_name, error_type, error_message, stack_trace, source_url)
            VALUES (%s, NULL, %s, NULL, %s, %s, %s, %s, %s)
        """
        values = (self.run_id, self.store_id, self.job_name, error_type, error_msg, stack_trace, source_url)
        self.db.execute_query(query, values)

    def run(self):
        self.log_pipeline('running', f'Khởi động phiên chạy: {self.run_id}')
        params, actual_url = self.build_request_params()
        
        retry_count = 0
        status = 'fail'
        response_code = None
        response_body = None
        last_error = None

        # ======================
        # LUỒNG CÀO MẠNG XỬ LÝ LỖI & THỬ LẠI
        # ======================
        while retry_count < self.max_retry:
            try:
                logging.info(f"Attempt: {retry_count + 1}/{self.max_retry} | Gửi request tới API...")
                response = self.session.get(self.api_url, params=params, headers=self.headers, timeout_seconds=self.timeout_sec)
                
                response_code = response.status_code
                response_body = response.text
                
                if "CẢNH BÁO HỆ THỐNG" in response_body or "Object moved" in response_body or response_code != 200:
                    logging.warning("-> [CẢNH BÁO] Phản hồi lỗi hệ thống. Thử lại sau 5 giây...")
                    retry_count += 1
                    time.sleep(5)
                    continue
                    
                status = 'success'
                logging.info("-> [THÀNH CÔNG] Đã lấy trọn vẹn chuỗi JSON lịch sử!")
                break
                
            except Exception as error:
                retry_count += 1
                last_error = traceback.format_exc() # Bắt chính xác stack trace chi tiết
                logging.warning(f"-> [LỖI MẠNG CHẬP CHỜN]: {error}. Đang thử lại...")
                time.sleep(5)

        # ======================
        # LƯU VÀO WEB_RESPONSES
        # ======================
        try:
            web_query = """
                INSERT INTO web_responses 
                (run_id, store_id, response_code, response_body, status, source_url, retry_count)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            self.db.execute_query(web_query, (self.run_id, self.store_id, response_code, response_body, status, actual_url, retry_count))
        except Exception as e:
            logging.error(f"[LỖI DATABASE] Không thể lưu web_responses: {e}")
            sys.exit(1)

        # ======================
        # GHI ERROR_LOG NẾU THẤT BẠI HOÀN TOÀN
        # ======================
        if status == 'fail':
            error_msg = f'Thất bại hoàn toàn sau {self.max_retry} lần cào ngày {self.formatted_date}'
            self.log_error('CRAWL_FAILED', error_msg, last_error, actual_url)
            self.log_pipeline('fail', 'Thất bại cào dữ liệu')
            logging.error("-> [NGUY HIỂM] Đã ghi nhận log lỗi chi tiết vào bảng error_log.")
            sys.exit(1) # Ngắt tiến trình cho Airflow nhận diện lỗi
        else:
            self.log_pipeline('success', 'Tải dữ liệu thành công')
            sys.exit(0) # Trả về thành công tuyệt đối cho Airflow

    def build_request_params(self):
        raise NotImplementedError("Class Con phải tự định nghĩa Params!")