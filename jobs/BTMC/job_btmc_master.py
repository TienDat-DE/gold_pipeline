import sys
import subprocess
import logging
import argparse
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [MASTER] - %(message)s')

class JobBtmcMasterPipeline:
    def __init__(self):
        # 1. Khởi tạo bộ đọc tham số từ Terminal
        parser = argparse.ArgumentParser(description="Chạy Master Pipeline cho ngày bất kỳ")
        parser.add_argument('--date', type=str, default=datetime.now().strftime('%Y%m%d'), help="Định dạng YYYYMMDD, vd: 20261025")
        
        # Chỉ lấy parse_known_args để tránh lỗi nếu truyền thừa tham số
        args = parser.parse_known_args()[0]
        
        self.today_str = args.date
        self.run_id = f"{self.today_str}_BTMC"
        
        # 2. Cấu hình 6 bước của Pipeline với tham số động theo ngày truyền vào
        self.pipeline_steps = [
            {
                "name": "1. Crawl Data", 
                "module": "jobs.BTMC.crawler.job_btmc_crawl", 
                "args": []
            },
            {
                "name": "2. Save Raw Data", 
                "module": "jobs.BTMC.raw.job_btmc_raw", 
                "args": ["--date", self.today_str]
            },
            {
                "name": "3. Check Validate & Clean", 
                "module": "jobs.BTMC.clean.job_btmc_clean_pipeline", 
                "args": ["--run_id", self.run_id]
            },
            {
                "name": "4. Create Hash & Track", 
                "module": "jobs.BTMC.hash.job_btmc_hash", 
                "args": ["--run_id", self.run_id]
            },
            {
                "name": "5. SCD Type 2 Logic", 
                "module": "jobs.BTMC.load_history.job_btmc_scd2", 
                "args": ["--run_id", self.run_id]
            },
            {
                "name": "6. Output Final Backup", 
                "module": "jobs.BTMC.export.job_btmc_export", 
                "args": []
            }
        ]

    def run_pipeline(self):
        logging.info(f"==================================================")
        logging.info(f" KHỞI ĐỘNG MASTER PIPELINE (6 STEPS) | RUN_ID: {self.run_id}")
        logging.info(f"==================================================")

        for step in self.pipeline_steps:
            logging.info(f">>> Đang kích hoạt: {step['name']}...")
            
            # Khởi tạo lệnh chạy dưới dạng module chuẩn của Python (-m)
            command = [sys.executable, "-m", step["module"]]
            
            # Gắn thêm tham số (nếu có)
            if step["args"]:
                command.extend(step["args"])
            
            try:
                # Thực thi script con. check=True sẽ tự động quăng lỗi nếu returncode != 0
                subprocess.run(command, check=True, text=True)
                logging.info(f"[THÀNH CÔNG] Bước {step['name']} đã hoàn tất.\n")
                
            except subprocess.CalledProcessError as e:
                # Bắt lỗi khi script con dùng sys.exit(1)
                logging.error(f"[THẤT BẠI] Pipeline vỡ tại bước: {step['name']}")
                logging.error(f"Mã lỗi (Return code): {e.returncode}. Toàn bộ tiến trình phía sau bị hủy.")
                sys.exit(1) 
            except Exception as e:
                # Bắt lỗi hệ thống (thiếu file, sai đường dẫn thư mục...)
                logging.error(f"[LỖI HỆ THỐNG] Không thể gọi module {step['module']}: {e}")
                sys.exit(1)

        logging.info(f"==================================================")
        logging.info(f" [HOÀN TẤT] MASTER PIPELINE ĐÃ CHẠY THÀNH CÔNG 100%")
        logging.info(f"==================================================")

if __name__ == "__main__":
    master_job = JobBtmcMasterPipeline()
    master_job.run_pipeline()