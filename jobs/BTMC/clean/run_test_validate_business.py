import sys
import json
import argparse
import logging
from database.oop_connection import DatabaseManagerOOP

# Kéo công cụ vào (Chú ý thư mục BTMC viết hoa theo yêu cầu)
from clean.sites.BTMC.oop_btmc_cleaner import BtmcCleanerOOP
from clean.sites.BTMC.oop_btmc_validate_basic import BtmcValidateBasicOOP
from clean.sites.BTMC.oop_btmc_normalizer import BtmcNormalizerOOP
from clean.sites.BTMC.oop_btmc_validate_business import BtmcValidateBusinessOOP

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class JobTestValidateBusiness:
    def __init__(self):
        self.db = DatabaseManagerOOP()
        self.cleaner = BtmcCleanerOOP()
        self.basic_validator = BtmcValidateBasicOOP()
        self.normalizer = BtmcNormalizerOOP()
        self.business_validator = BtmcValidateBusinessOOP()

    def run_dry_test(self, run_id):
        logging.info(f"--- [DEBUG VALIDATE BUSINESS] RUN_ID: {run_id} ---[cite: 7]")
        
        # Truy xuất bản ghi từ raw_gold_price[cite: 7]
        query = "SELECT raw_id, raw_payload FROM raw_gold_price WHERE run_id = %s ORDER BY raw_id DESC LIMIT 1[cite: 7]"
        records = self.db.fetch_all(query, (run_id,))
        
        if not records:
            logging.info("Không tìm thấy dữ liệu thô cho RUN_ID này.")
            sys.exit(1)

        row = records[0]
        raw_id = row[0]
        raw_payload_str = row[1]
        
        logging.info(f" -> Đang tiến hành xử lý cho raw_id: {raw_id}[cite: 7]")

        # BƯỚC 1: Clean
        clean_json_str = self.cleaner.process_clean_raw_json(raw_payload_str)
        if not clean_json_str:
            logging.error(" -> [THẤT BẠI] Lỗi gọt HTML.")
            sys.exit(1)
            
        text_dict = json.loads(clean_json_str)

        # BƯỚC 2: Validate Basic
        is_basic_ok, basic_msg = self.basic_validator.validate(text_dict)
        if not is_basic_ok:
            logging.error(f" -> [BỊ CHẶN Ở BASIC] {basic_msg}")
            sys.exit(1)

        # BƯỚC 3: Normalize
        is_norm_ok, normalized_dict, norm_msg = self.normalizer.normalize_payload(text_dict)
        if not is_norm_ok:
            logging.error(f" -> [BỊ CHẶN Ở NORMALIZE] {norm_msg}")
            sys.exit(1)
            
        # BƯỚC 4: Validate Business
        is_biz_ok, err_code, biz_msg = self.business_validator.validate(run_id, normalized_dict)
        
        if is_biz_ok:
            logging.info(" [VALIDATE BUSINESS SUCCESS] Dữ liệu an toàn logic tài chính. \n[cite: 7]")
            sys.exit(0)
        else:
            # Ở Pipeline Job tổng, bạn sẽ gọi hàm ghi error_log hoặc anomaly_log tại đây[cite: 7]
            logging.error(f" -> [THẤT BẠI LÚC VALIDATE BUSINESS] Lỗi {err_code}: {biz_msg}")
            sys.exit(1)

if __name__ == "__main__":
    # Tiếp nhận tham số run_id từ Terminal[cite: 7]
    parser = argparse.ArgumentParser(description="Debug độc lập bước Validate Business[cite: 7]")
    parser.add_argument('--run_id', type=str, required=True)
    args = parser.parse_args()

    job = JobTestValidateBusiness()
    job.run_dry_test(args.run_id)