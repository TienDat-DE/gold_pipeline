import argparse
import logging
from datetime import datetime
from raw.sites.BTMC.oop_btmc_raw import BtmcRawOOP

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class JobBtmcRaw:
    def __init__(self):
        self.raw_processor = BtmcRawOOP()

    def run_job(self):
        # 1. Bóc tách tham số ngày từ Terminal
        parser = argparse.ArgumentParser()
        parser.add_argument('--date', type=str, default=datetime.now().strftime('%Y%m%d'))
        args = parser.parse_known_args()[0]
        
        # 2. Định dạng lại tham số chuẩn xác với thiết kế MySQL
        run_id = f"{args.date}_BTMC"
        date_key = int(args.date)
        data_date_str = f"{args.date[0:4]}-{args.date[4:6]}-{args.date[6:8]}"
        
        logging.info(f"========== BẮT ĐẦU BÓC TÁCH RAW DATA ({run_id}) ==========")
        
        # 3. Kích hoạt cỗ máy bóc tách
        self.raw_processor.process(run_id, date_key, data_date_str)
        
        logging.info("========== HOÀN TẤT TIẾN TRÌNH RAW DATA ==========")

if __name__ == "__main__":
    job = JobBtmcRaw()
    job.run_job()