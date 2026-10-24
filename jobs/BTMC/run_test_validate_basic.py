import sys
import json
import logging
from database.oop_connection import DatabaseManagerOOP

# Chỉ kéo 2 cỗ máy: Clean và Validate Basic
from clean.sites.BTMC.oop_btmc_cleaner import BtmcCleanerOOP
from clean.sites.BTMC.oop_btmc_validate_basic import BtmcValidateBasicOOP

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class JobTestValidateBasic:
    def __init__(self):
        self.db = DatabaseManagerOOP()
        self.cleaner = BtmcCleanerOOP()
        self.basic_validator = BtmcValidateBasicOOP()

    def run_dry_test(self, record_limit=3):
        logging.info("--- BẮT ĐẦU TEST LUỒNG: CLEAN -> VALIDATE BASIC ---")
        
        query = "SELECT id, raw_payload FROM raw_gold_price ORDER BY id DESC LIMIT %s"
        records = self.db.fetch_all(query, (record_limit,))
        
        if not records:
            logging.info("Không có dữ liệu thô để test.")
            return

        for row in records:
            record_id = row[0]
            raw_payload_str = row[1]
            logging.info(f"\n[RECORD ID: {record_id}]")

            # 1. Gọt HTML (Clean)
            clean_json_str = self.cleaner.process_clean_raw_json(raw_payload_str)
            if not clean_json_str:
                logging.error(" -> [DỪNG LUỒNG] Lỗi bóc tách cấu trúc web.")
                continue
            
            # Dịch chuỗi thành Từ điển
            text_dict = json.loads(clean_json_str)
            logging.info(f" -> Dữ liệu sau Clean: {text_dict}")

            # 2. Kiểm duyệt trực tiếp trên dữ liệu chữ (Validate Basic)
            is_valid, message = self.basic_validator.validate(text_dict)
            
            if is_valid:
                logging.info(" -> KẾT QUẢ: [ĐẠT] - Đủ điều kiện gửi đi Normalize.")
            else:
                # Trong Job tổng, lệnh này sẽ kèm theo sys.exit(1) để hủy toàn bộ Job
                logging.error(f" -> KẾT QUẢ: [BỊ CHẶN DỪNG LUỒNG] - {message}")

if __name__ == "__main__":
    job = JobTestValidateBasic()
    job.run_dry_test(record_limit=2)