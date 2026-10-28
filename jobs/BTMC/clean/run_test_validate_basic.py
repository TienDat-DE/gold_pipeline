import sys
import argparse
import logging
from database.oop_connection import DatabaseManagerOOP
from clean.sites.BTMC.oop_btmc_cleaner import BtmcCleanerOOP
from clean.validate_basic.sites.BTMC.oop_btmc_validate_basic import BtmcValidateBasicOOP

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class JobTestValidateBasic:
    def __init__(self):
        self.db = DatabaseManagerOOP()
        self.cleaner = BtmcCleanerOOP()
        self.basic_validator = BtmcValidateBasicOOP()

    def run_job(self):
        parser = argparse.ArgumentParser(description="Debug độc lập bước Validate Basic")
        parser.add_argument('--run_id', type=str, required=True)
        args = parser.parse_known_args()[0]

        logging.info(f"\n[DEBUG VALIDATE BASIC] RUN_ID: {args.run_id}")
        
        # Truy vấn giống file gốc
        query = """
            SELECT raw_id, run_id, store_id, source_url, raw_payload 
            FROM raw_gold_price 
            WHERE run_id = %s AND status = 'success' 
            ORDER BY raw_id DESC LIMIT 1
        """
        rows = self.db.fetch_all(query, (args.run_id,))

        if rows:
            record = rows[0]
            raw_id = record[0]
            run_id = record[1]
            source_url = record[3]
            raw_payload = record[4]

            # 1. Gọt HTML (Clean) để lấy chuỗi chuẩn
            cleaned_str = self.cleaner.process_clean_raw_json(raw_payload)
            
            # 2. Chạy bài Test Basic, log lỗi sẽ tự động bắn vào Database
            success = self.basic_validator.validate(
                run_id=run_id, 
                raw_id=raw_id, 
                cleaned_payload_str=cleaned_str, 
                source_url=source_url, 
                is_debug=True
            )
            
            if success:
                sys.exit(0)
            else:
                sys.exit(1)
        else:
            logging.error(f"[LỖI] Không tìm thấy dữ liệu trong raw_gold_price cho run_id: {args.run_id}.")
            sys.exit(1)

if __name__ == "__main__":
    job = JobTestValidateBasic()
    job.run_job()