import argparse
import logging
import sys
from datetime import datetime
from raw.sites.BTMC.oop_btmc_raw import BtmcRawOOP

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class JobBtmcRaw:
    def __init__(self):
        self.raw_processor = BtmcRawOOP()

    def run_job(self):
        parser = argparse.ArgumentParser(description="Xử lý dữ liệu từ web_responses sang raw_gold_price")
        parser.add_argument('--date', type=str, default=datetime.now().strftime('%Y%m%d'))
        args = parser.parse_known_args()[0]
        
        run_id = f"{args.date}_BTMC"
        date_key = int(args.date)
        data_date_str = f"{args.date[0:4]}-{args.date[4:6]}-{args.date[6:8]}"
        
        logging.info(f"\n[HỆ THỐNG] Đang lấy dữ liệu JSON để xử lý thô cho RUN_ID: {run_id}")
        
        # Bắt kết quả trả về từ quá trình bóc tách
        success = self.raw_processor.process(run_id, date_key, data_date_str)
        
        if success:
            sys.exit(0) # Báo hiệu tiến trình thành công
        else:
            sys.exit(1) # Báo hiệu thất bại (Dừng Airflow Task)

if __name__ == "__main__":
    job = JobBtmcRaw()
    job.run_job()