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
    def __init__(self,job_name, store_id, api_url):
        self.job_name = job_name
        self.store_id = store_id
        self.api_url = api_url
        self.db = DatabaseManagerOOP()
        
        self.formatted_date, self.run_id = self.parse_arguments()
        self.max_retry = 5
        self.timeout_sec = 60
        
        self.session = tls_client.Session(client_identifier="chrome_120", random_tls_extension_order= True)
        self.headers = {
            'Accept': '*/*', 'Accept-Language': 'vi', 'Connection': 'keep-alive',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/148.0.0.0'
        }
    
    def parse_arguments(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--date', type=str, default=datetime.now().strftime('%Y%m%d'))
        args = parser.parse_known_args()[0]
        
        if len(args.date) != 8 or not args.date.isdigit():
            logging.error(f"Ngày '{args.date}' không hợp lệ! Dùng định dạng YYYYMMDD.") 
            sys.exit(1)
            
        fmt_date = f"{args.date[6:8]}/{args.date[4:6]}/{args.date[0:4]}" 
        run_id = f"OOP_{args.date}_{self.job_name}"
        return fmt_date, run_id
    
    def log_pipeline(self, status):
        self.db.execute_query(pipeline_log_query, (self.run_id, self.job_name, status))
    
    def fetch_data(self, params):
        retry_count = 0
        while retry_count < self.max_retry:
            try:
                logging.info(f"[{self.job_name}] Attemp: {retry_count + 1}/{self.max_retry}...")
                response = self.session.get(self.api_url, params = params, headers = self.headers, timeout_seconds = self.timeout_sec)
                
                body = response.text
                if "CẢNH BÁO HỆ THỐNG" in body or "Object moved" in body or response.status_code !=200:
                    logging.warning("Phản hồi lỗi WAF. Thử lại sau 5s...")
                    retry_count +=1
                    time.sleep(5)
                    continue
                
                return response.status_code, body, 'success', retry_count
            
            except Exception as e:
                logging.error(f"Lỗi mạng: {e}")                                                           
                retry_count +=1
                time.sleep(5)
                
        return None, None, 'fail', retry_count
    
    def run(self):
        logging.info(f"\n[START OOP] Phiên: {self.run_id} | Ngày: {self.formatted_date}")    
        self.log_pipeline("running")
        params, actual_url = self.build_request_params()
        status_code, body, status, retries = self.fetch_data(params)
        
        web_values = (self.run_id, self.store_id, status_code, body, status, actual_url, retries)
        self.db.execute_query(web_response_query, web_values)
        
        if status == 'fail':
            err_values = (self.run_id, None, self.store_id, None, self.job_name,
                          'CRAWL_FAILED', f'OOP Thất bại ngày {self.formatted_date}', '', actual_url)
            self.db.execute_query(error_log_query, err_values)
            self.log_pipeline('failed')
            sys.exit(1)
        else:
            self.log_pipeline('success')
            logging.info('==== HOÀN TẤT PHIÊN OOP THÀNH CÔNG ====')
            
    def build_request_params(self):
        raise NotImplementedError('Class Con phải tự định nghĩa Params!')    
            
            
            
            
            
            
            