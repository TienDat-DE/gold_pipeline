import sys
import subprocess
import logging
import argparse
from datetime import datetime, timedelta
from database.oop_connection import DatabaseManagerOOP

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [MASTER] - %(message)s')

class JobBtmcMasterPipeline:
    def __init__(self):
        parser = argparse.ArgumentParser(description="Chạy Master Pipeline Backfill dữ liệu")
        parser.add_argument('--start_date', type=str, default=datetime.now().strftime('%Y%m%d'))
        parser.add_argument('--end_date', type=str, default=None)
        parser.add_argument('--date', type=str, default=None)
        
        args = parser.parse_known_args()[0]
        self.start_date_str = args.date if args.date else args.start_date
        self.end_date_str = args.end_date if args.end_date else self.start_date_str
        
        self.db = DatabaseManagerOOP()
        self.store_id = 1
        self.source_url = "https://btmc.vn/"

    def generate_date_list(self):
        start = datetime.strptime(self.start_date_str, '%Y%m%d')
        end = datetime.strptime(self.end_date_str, '%Y%m%d')
        if start > end:
            logging.error("[LỖI] start_date không thể lớn hơn end_date!")
            sys.exit(1)
        date_list = []
        current = start
        while current <= end:
            date_list.append(current.strftime('%Y%m%d'))
            current += timedelta(days=1)
        return date_list

    def log_job_start(self, run_id, date_key_str):
        date_key_formatted = datetime.strptime(date_key_str, '%Y%m%d').strftime('%Y-%m-%d')
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        query_pipeline = """
            INSERT INTO pipeline_log (run_id, store_id, job_name, start_time, source_url, date_key)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                start_time = VALUES(start_time),
                step = NULL, status = NULL
        """
        try:
            self.db.execute_query(query_pipeline, (
                run_id, self.store_id, 'BTMC_MASTER_PIPELINE', now_str, self.source_url, date_key_formatted
            ))
        except Exception as e:
            logging.error(f"[PIPELINE_LOG] Lỗi khởi tạo log hệ thống: {e}")

    def log_pipeline_step(self, run_id, step_name, status):
        self.step_history.append(step_name)
        self.status_history.append(status)

        step_str = " / ".join(self.step_history)
        status_str = " / ".join(self.status_history)
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        query = """
            UPDATE pipeline_log 
            SET step = %s, status = %s, end_time = %s
            WHERE run_id = %s
        """
        try:
            self.db.execute_query(query, (step_str, status_str, now_str, run_id))
        except Exception as e:
            logging.error(f"[PIPELINE_LOG] Lỗi nối chuỗi cập nhật log: {e}")

    def run_pipeline(self):
        dates_to_run = self.generate_date_list()
        
        logging.info(f"==================================================")
        logging.info(f" KÍCH HOẠT CHẠY BACKFILL DỮ LIỆU ({len(dates_to_run)} NGÀY)")
        logging.info(f"==================================================")

        for target_date in dates_to_run:
            run_id = f"{target_date}_BTMC"
            logging.info(f"\n--- BẮT ĐẦU XỬ LÝ CHO NGÀY: {target_date} (RUN_ID: {run_id}) ---")
            
            self.step_history = []
            self.status_history = []

            # Khởi tạo log (không cần lấy job_run_id nữa)
            self.log_job_start(run_id, target_date)
            
            pipeline_steps = [
                {"name": "1. Crawl Data", "short_name": "crawl", "module": "jobs.BTMC.crawler.job_btmc_crawl", "args": ["--date", target_date]},
                {"name": "2. Save Raw Data", "short_name": "raw", "module": "jobs.BTMC.raw.job_btmc_raw", "args": ["--date", target_date]},
                {"name": "3. Check Validate & Clean", "short_name": "clean", "module": "jobs.BTMC.clean.job_btmc_clean_pipeline", "args": ["--run_id", run_id]},
                {"name": "4. Create Hash & Track", "short_name": "hash", "module": "jobs.BTMC.hash.job_btmc_hash", "args": ["--run_id", run_id]},
                {"name": "5. SCD Type 2 Logic", "short_name": "scd2", "module": "jobs.BTMC.load_history.job_btmc_scd2", "args": ["--run_id", run_id]},
                {"name": "6. Output Final Backup", "short_name": "export", "module": "jobs.BTMC.export.job_btmc_export", "args": ["--run_id", run_id]}
            ]
            
            step_failed = False
            for step in pipeline_steps:
                full_name = step['name']
                short_name = step['short_name']
                logging.info(f">>> Đang kích hoạt: {full_name}...")
                
                command = [sys.executable, "-m", step["module"]]
                if step["args"]: command.extend(step["args"])
                
                try:
                    subprocess.run(command, check=True, text=True)
                    self.log_pipeline_step(run_id, short_name, 'success')
                except subprocess.CalledProcessError as e:
                    logging.error(f"[THẤT BẠI] Vỡ tại bước: {full_name}.")
                    self.log_pipeline_step(run_id, short_name, 'fail')
                    step_failed = True
                    break 
                except Exception as e:
                    self.log_pipeline_step(run_id, short_name, 'fail')
                    step_failed = True
                    break
                    
            if not step_failed:
                logging.info(f"--- HOÀN TẤT TRỌN VẸN NGÀY {target_date} ---")

        logging.info(f"==================================================")
        logging.info(f" [HOÀN TẤT] CHIẾN DỊCH CHẠY BACKFILL KẾT THÚC.")
        logging.info(f"==================================================")

if __name__ == "__main__":
    master_job = JobBtmcMasterPipeline()
    master_job.run_pipeline()