import sys
import json
import argparse
import logging
from database.oop_connection import DatabaseManagerOOP

from clean.sites.btmc.oop_btmc_cleaner import BtmcCleanerOOP
from clean.sites.btmc.oop_btmc_normalizer import BtmcNormalizerOOP

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class JobTestNormalize:
    def __init__(self):
        self.db = DatabaseManagerOOP()
        self.cleaner = BtmcCleanerOOP()
        self.normalizer = BtmcNormalizerOOP()

    def run_dry_test(self, run_id):
        logging.info(f"--- [DEBUG NORMALIZE PRICE] RUN_ID: {run_id} ---[cite: 6]")
        
        query = "SELECT raw_id, raw_payload FROM raw_gold_price WHERE run_id = %s ORDER BY raw_id DESC LIMIT 1[cite: 6]"
        records = self.db.fetch_all(query, (run_id,))
        
        if not records:
            logging.info("Không tìm thấy dữ liệu thô cho RUN_ID này.")
            sys.exit(1)

        row = records[0]
        raw_id = row[0]
        raw_payload_str = row[1]
        
        logging.info(f" -> Đang tiến hành xử lý cho raw_id: {raw_id}[cite: 6]")

        # 1. Gọt HTML
        clean_json_str = self.cleaner.process_clean_raw_json(raw_payload_str)
        if not clean_json_str:
            logging.error(" -> [THẤT BẠI] Lỗi gọt HTML.")
            sys.exit(1)
            
        text_dict = json.loads(clean_json_str)
        logging.info(f" -> Dữ liệu sau Clean: {text_dict}")

        # 2. Chuẩn hóa số nguyên & Nhân hệ số
        is_ok, normalized_dict, msg = self.normalizer.normalize_payload(text_dict)
        
        if is_ok:
            logging.info(" [NORMALIZE PRICE SUCCESS] Quy đổi hệ số nhân 10.000 thành công.[cite: 6]")
            logging.info(f" -> Dữ liệu đầu ra:\n{json.dumps(normalized_dict, ensure_ascii=False, indent=4)}")
            sys.exit(0)
        else:
            # Ở Job Tổng, lệnh INSERT xuống bảng error_log sẽ được viết tại đây[cite: 6]
            logging.error(f" -> [THẤT BẠI LÚC NORMALIZE] {msg}")
            sys.exit(1)

if __name__ == "__main__":
    # Nhận tham số truyền vào từ Terminal giống hệt file cũ của bạn[cite: 6]
    parser = argparse.ArgumentParser(description="Debug độc lập bước Normalize Price[cite: 6]")
    parser.add_argument('--run_id', type=str, required=True)
    args = parser.parse_args()

    job = JobTestNormalize()
    job.run_dry_test(args.run_id)