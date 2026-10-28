import sys
import json
import argparse
import logging
from database.oop_connection import DatabaseManagerOOP

from clean.sites.BTMC.oop_btmc_cleaner import BtmcCleanerOOP
from clean.validate_basic.sites.BTMC.oop_btmc_validate_basic import BtmcValidateBasicOOP
from clean.normalize.sites.BTMC.oop_btmc_normalizer import BtmcNormalizerOOP
from clean.validate_business.sites.BTMC.oop_btmc_validate_business import BtmcValidateBusinessOOP

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class JobTestValidateBusiness:
    def __init__(self):
        self.db = DatabaseManagerOOP()
        self.cleaner = BtmcCleanerOOP()
        self.basic_validator = BtmcValidateBasicOOP()
        self.normalizer = BtmcNormalizerOOP()
        self.business_validator = BtmcValidateBusinessOOP()

    def run_dry_test(self, run_id):
        logging.info(f"--- [DEBUG VALIDATE BUSINESS] RUN_ID: {run_id} ---")
        
        # Bổ sung source_url để truyền xuống hệ thống log
        query = "SELECT raw_id, source_url, raw_payload FROM raw_gold_price WHERE run_id = %s ORDER BY raw_id DESC LIMIT 1"
        records = self.db.fetch_all(query, (run_id,))
        
        if not records:
            logging.info("Không tìm thấy dữ liệu thô cho RUN_ID này.")
            sys.exit(1)

        row = records[0]
        raw_id = row[0]
        source_url = row[1]
        raw_payload_str = row[2]

        # 1. Clean
        clean_json_str = self.cleaner.process_clean_raw_json(raw_payload_str)
        if not clean_json_str:
            sys.exit(1)
        text_dict = json.loads(clean_json_str)

        # 2. Validate Basic (Tự động lưu error_log nếu trượt)
        is_basic_ok = self.basic_validator.validate(run_id, raw_id, clean_json_str, source_url)
        if not is_basic_ok:
            sys.exit(1)

        # 3. Normalize
        normalized_dict = self.normalizer.normalize_payload(text_dict)

        # 4. Validate Business (Tự động lưu error_log/anomaly_log nếu trượt)
        is_biz_ok = self.business_validator.validate(
            run_id=run_id, 
            raw_id=raw_id, 
            normalized_dict=normalized_dict, 
            source_url=source_url, 
            is_debug=True
        )
        
        if is_biz_ok:
            sys.exit(0)
        else:
            sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Debug độc lập bước Validate Business")
    parser.add_argument('--run_id', type=str, required=True)
    args = parser.parse_args()

    job = JobTestValidateBusiness()
    job.run_dry_test(args.run_id)