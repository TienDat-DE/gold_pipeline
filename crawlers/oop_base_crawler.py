import argparse
import time
import sys
import tls_client
import logging
from datetime import datetime

from database.oop_connection import DatabaseManagerOOP
from database.queries import web_response_query, pipeline_log_query, error_log_query

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class BaseCrawlerOOP:
    def __init__(self, job_name, store_id, api_url):
        self.job_name = job_name
        self.store_id = store_id
        self.api_url = api_url
        self.db = DatabaseManagerOOP()
        
        self.formatted_date, self.run_id, self.date_key = self.parse_arguments()
        self.max_retry = 5
        self.timeout_sec = 60

        self.session = tls_client.Session(client_identifier="chrome_120", random_tls_extension_order=True)
        self.headers = {'Accept': '*/*', 'User-Agent': 'Mozilla/5.0 Chrome/148.0.0.0'}

    def parse_arguments(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--date', type=str, default=datetime.now().strftime('%Y%m%d'))
        args = parser.parse_known_args()[0]
        
        if len(args.date) != 8 or not args.date.isdigit():
            logging.error("Ngày không hợp lệ! Dùng YYYYMMDD.")
            sys.exit(1)
            
        fmt_date = f"{args.date[6:8]}/{args.date[4:6]}/{args.date[0:4]}"
        run_id = f"{args.date}_{self.job_name}"
        date_key = int(args.date) # VD: 20260420
        return fmt_date, run_id, date_key

    def log_pipeline(self, status, message=""):
        # CHUẨN HÓA THAM SỐ CHO BẢNG pipeline_log
        # Sơ đồ: run_id, store_id, gold_type_id, job_name, step, status, message, start_time, end_time, source_url, date_key
        values = (
            self.run_id,          # run_id
            self.store_id,        # store_id
            None,                 # gold_type_id (Crawler cào chung nên chưa phân loại)
            self.job_name,        # job_name
            'crawl',              # step
            status,               # status (success/fail/running)
            message,              # message
            datetime.now(),       # start_time
            None,                 # end_time (để trống khi mới start)
            self.api_url,         # source_url
            self.date_key         # date_key
        )
        self.db.execute_query(pipeline_log_query, values)

    def fetch_data(self, params):
        retry_count = 0
        while retry_count < self.max_retry:
            try:
                response = self.session.get(self.api_url, params=params, headers=self.headers, timeout_seconds=self.timeout_sec)
                body = response.text
                if "CẢNH BÁO HỆ THỐNG" in body or response.status_code != 200:
                    retry_count += 1; time.sleep(5); continue
                return response.status_code, body, 'success', retry_count
            except Exception as e:
                retry_count += 1; time.sleep(5)
        return 500, None, 'fail', retry_count

    def run(self):
        self.log_pipeline('running', 'Bắt đầu cào dữ liệu')
        
        params, actual_url = self.build_request_params()
        status_code, body, status, retries = self.fetch_data(params)
        
        # CHUẨN HÓA THAM SỐ CHO BẢNG web_responses
        # Sơ đồ: run_id, store_id, response_code, response_body, status, source_url, retry_count
        web_values = (
            self.run_id,          # run_id
            self.store_id,        # store_id
            status_code,          # response_code
            body,                 # response_body
            status,               # status
            actual_url,           # source_url
            retries               # retry_count
        )
        self.db.execute_query(web_response_query, web_values)
        
        if status == 'fail':
            # CHUẨN HÓA THAM SỐ CHO BẢNG error_log
            # Sơ đồ: run_id, raw_id, store_id, gold_type_id, job_name, error_type, error_message, stack_trace, source_url
            err_values = (
                self.run_id,      # run_id
                None,             # raw_id (Chưa có vì cào mạng xịt)
                self.store_id,    # store_id
                None,             # gold_type_id
                self.job_name,    # job_name
                'network',        # error_type (Dựa theo sơ đồ)
                'Mất kết nối mạng hoặc bị WAF chặn', # error_message
                '',               # stack_trace
                actual_url        # source_url
            )
            self.db.execute_query(error_log_query, err_values)
            self.log_pipeline('fail', 'Lỗi mạng')
            sys.exit(1)
        else:
            self.log_pipeline('success', 'Tải dữ liệu thành công')

    def build_request_params(self):
        raise NotImplementedError("Class Con phải tự định nghĩa Params!")