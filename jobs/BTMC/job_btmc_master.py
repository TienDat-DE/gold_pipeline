import sys
import subprocess
import logging
import argparse
from datetime import datetime, timedelta
from database.oop_connection import DatabaseManagerOOP

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [MASTER] - %(message)s')

class JobBtmcMasterPipeline:
    def __init__(self):
        # 1. Khởi tạo bộ đọc tham số (Hỗ trợ chạy 1 khoảng thời gian)
        parser = argparse.ArgumentParser(description="Chạy Master Pipeline Backfill dữ liệu")
        parser.add_argument('--start_date', type=str, default=datetime.now().strftime('%Y%m%d'), help="Ngày bắt đầu (YYYYMMDD)")
        parser.add_argument('--end_date', type=str, default=None, help="Ngày kết thúc (YYYYMMDD). Bỏ trống = chỉ chạy start_date")
        
        args = parser.parse_known_args()[0]
        self.start_date_str = args.start_date
        self.end_date_str = args.end_date if args.end_date else self.start_date_str
        
        self.db = DatabaseManagerOOP()
        self.store_id = 1
        self.source_url = "https://btmc.vn/"

    def generate_date_list(self):
        """Hàm sinh ra danh sách các ngày từ start_date đến end_date"""
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

    def log_job_start(self, run_id):
        query = """
            INSERT INTO job_run (run_id, store_id, job_name, run_time, status, source_url)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        try:
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            job_run_id = self.db.execute_query(query, (
                run_id, self.store_id, 'BTMC_MASTER_PIPELINE', now_str, 'RUNNING', self.source_url
            ))
            return job_run_id
        except Exception as e:
            logging.error(f"[JOB_RUN] Lỗi khởi tạo bảng job_run: {e}")
            return None

    def log_job_end(self, run_id, job_run_id, final_status):
        if not job_run_id: return
            
        total, success, failed = 0, 0, 0
        try:
            q_stats = "SELECT quality_flag, COUNT(*) FROM staging_gold_price WHERE run_id = %s GROUP BY quality_flag"
            stats = self.db.fetch_all(q_stats, (run_id,))
            if stats:
                for row in stats:
                    flag, count = row[0], row[1]
                    total += count
                    if flag == 'good': success += count
                    else: failed += count
        except Exception as e:
            logging.warning(f"[JOB_RUN] Không đếm được record thống kê: {e}")
            
        try:
            u_query = """
                UPDATE job_run 
                SET status = %s, total_records = %s, success_records = %s, failed_records = %s
                WHERE job_id = %s
            """
            self.db.execute_query(u_query, (final_status, total, success, failed, job_run_id))
            logging.info(f"[JOB_RUN] Chốt trạng thái '{final_status}' (Total: {total} | Success: {success} | Fail: {failed})")
        except Exception as e:
            logging.error(f"[JOB_RUN] Lỗi cập nhật kết thúc: {e}")

    def run_pipeline(self):
        dates_to_run = self.generate_date_list()
        
        logging.info(f"==================================================")
        logging.info(f" KÍCH HOẠT CHẠY BACKFILL DỮ LIỆU ({len(dates_to_run)} NGÀY)")
        logging.info(f" TỪ {self.start_date_str} ĐẾN {self.end_date_str}")
        logging.info(f"==================================================")

        for target_date in dates_to_run:
            run_id = f"{target_date}_BTMC"
            logging.info(f"\n--- BẮT ĐẦU XỬ LÝ CHO NGÀY: {target_date} (RUN_ID: {run_id}) ---")
            
            job_run_id = self.log_job_start(run_id)
            
            # Khởi tạo config các bước nằm TRONG vòng lặp để gán đúng target_date
            pipeline_steps = [
                {"name": "1. Crawl Data", "module": "jobs.BTMC.crawler.job_btmc_crawl", "args": ["--date", target_date]},
                {"name": "2. Save Raw Data", "module": "jobs.BTMC.raw.job_btmc_raw", "args": ["--date", target_date]},
                {"name": "3. Check Validate & Clean", "module": "jobs.BTMC.clean.job_btmc_clean_pipeline", "args": ["--run_id", run_id]},
                {"name": "4. Create Hash & Track", "module": "jobs.BTMC.hash.job_btmc_hash", "args": ["--run_id", run_id]},
                {"name": "5. SCD Type 2 Logic", "module": "jobs.BTMC.load_history.job_btmc_scd2", "args": ["--run_id", run_id]},
                {"name": "6. Output Final Backup", "module": "jobs.BTMC.export.job_btmc_export", "args": []}
            ]
            
            step_failed = False
            for step in pipeline_steps:
                logging.info(f">>> Đang kích hoạt: {step['name']}...")
                command = [sys.executable, "-m", step["module"]]
                if step["args"]: command.extend(step["args"])
                
                try:
                    subprocess.run(command, check=True, text=True)
                except subprocess.CalledProcessError as e:
                    logging.error(f"[THẤT BẠI] Vỡ tại bước: {step['name']}. Hủy các bước sau của ngày {target_date}.")
                    self.log_job_end(run_id, job_run_id, 'FAILED')
                    step_failed = True
                    break # Bỏ qua các bước còn lại, nhảy sang chạy ngày tiếp theo
                except Exception as e:
                    logging.error(f"[LỖI] Không thể gọi {step['module']}: {e}")
                    self.log_job_end(run_id, job_run_id, 'FAILED')
                    step_failed = True
                    break
                    
            if not step_failed:
                self.log_job_end(run_id, job_run_id, 'SUCCESS')
                logging.info(f"--- HOÀN TẤT TRỌN VẸN NGÀY {target_date} ---")

        logging.info(f"==================================================")
        logging.info(f" [HOÀN TẤT] CHIẾN DỊCH CHẠY BACKFILL KẾT THÚC.")
        logging.info(f"==================================================")

if __name__ == "__main__":
    master_job = JobBtmcMasterPipeline()
    master_job.run_pipeline()