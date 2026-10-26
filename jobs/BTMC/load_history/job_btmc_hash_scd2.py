import sys
import logging
from datetime import datetime
from database.oop_connection import DatabaseManagerOOP

# Import cỗ máy ở Tầng 4 (Hash) và Tầng 5 (Load History)
from hash.sites.BTMC.oop_btmc_hasher import BtmcHasherOOP
from load_history.sites.BTMC.oop_btmc_scd2 import BtmcScd2LoaderOOP

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class JobBtmcHashAndLoad:
    def __init__(self):
        self.db = DatabaseManagerOOP()
        self.hasher = BtmcHasherOOP()
        self.scd2_loader = BtmcScd2LoaderOOP()
        self.source_url = "https://btmc.vn"

    def run_pipeline(self, run_id):
        job_start_time = datetime.now()
        logging.info(f"========== BẮT ĐẦU HASH & LOAD HISTORY | RUN_ID: {run_id} ==========")
        
        # 1. Lấy dữ liệu Staging (đã xử lý xong ở phase Clean)[cite: 1]
        query_staging = """
            SELECT gold_type_id, data_date, buy_price, sell_price 
            FROM staging_gold_price WHERE run_id = %s
        """
        records = self.db.fetch_all(query_staging, (run_id,))
        
        if not records:
            logging.info("Không có dữ liệu Staging.")
            return

        for row in records:
            gold_type_id, data_date, buy_price, sell_price = row[0], row[1], row[2], row[3]

            # Bước 1: Check Hash Exist[cite: 1]
            is_changed, new_hash, record_hash_id = self.hasher.process_hash(
                run_id, gold_type_id, data_date, buy_price, sell_price, self.source_url
            )

            # Bước 2: Rẽ nhánh
            if is_changed == 0:
                logging.info(f"[{gold_type_id}] Hash existed -> Skip Load History")
                self._insert_log(run_id, gold_type_id, 'success', 'Skipped SCD2', job_start_time)
                continue

            logging.info(f"[{gold_type_id}] New Hash -> Running SCD Type 2 Logic...")
            success = self.scd2_loader.load_history(
                run_id, record_hash_id, gold_type_id, self.source_url, 
                buy_price, sell_price, new_hash, data_date, "PRICE_UPDATE"
            )
            
            # Ghi Log tổng kết[cite: 1]
            status = 'success' if success else 'fail'
            msg = 'SCD2 Load Success' if success else 'SCD2 DB Error'
            self._insert_log(run_id, gold_type_id, status, msg, job_start_time)

        logging.info("========== HOÀN TẤT ==========")

    def _insert_log(self, run_id, gold_type_id, status, message, start_time):
        query = """
            INSERT INTO pipeline_log (run_id, store_id, gold_type_id, job_name, step, status, message, start_time, end_time, source_url)
            VALUES (%s, 1, %s, 'JOB_HASH_SCD2', 'hash_scd2', %s, %s, %s, %s, %s)
        """
        self.db.execute_query(query, (run_id, gold_type_id, status, message, start_time, datetime.now(), self.source_url))

if __name__ == "__main__":
    job = JobBtmcHashAndLoad()
    job.run_pipeline(run_id="20261026_BTMC_01")