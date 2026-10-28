import sys
import argparse
import logging
from database.oop_connection import DatabaseManagerOOP
from load_history.sites.BTMC.oop_btmc_scd2 import BtmcSCD2LoaderOOP

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class JobBtmcLoadHistory:
    def __init__(self):
        self.db = DatabaseManagerOOP()
        self.scd2_loader = BtmcSCD2LoaderOOP()

    def run_pipeline(self):
        parser = argparse.ArgumentParser(description="Điều phối luồng Load History SCD2")
        parser.add_argument('--run_id', type=str, required=True)
        args = parser.parse_known_args()[0]
        run_id = args.run_id
        
        logging.info(f"========== BẮT ĐẦU LOAD HISTORY (SCD2) | RUN_ID: {run_id} ==========")
        
        # JOIN hash_tracking (lấy record thay đổi) với staging (lấy giá mua/bán)
        query_changed_records = """
            SELECT h.record_hash_id, h.gold_type_id, h.source_url, h.hash_value, h.data_date, s.buy_price, s.sell_price
            FROM hash_tracking h
            JOIN staging_gold_price s ON h.run_id = s.run_id AND h.gold_type_id = s.gold_type_id
            WHERE h.run_id = %s AND h.is_changed = 1
        """
        records = self.db.fetch_all(query_changed_records, (run_id,))
        
        if not records:
            logging.info("Không có biến động giá nào cần ghi nhận (is_changed = 0). Bỏ qua SCD2.")
            sys.exit(0)

        success_flag = True
        for row in records:
            record_hash_id, gold_type_id, source_url, new_hash, data_date, buy_price, sell_price = row
            try:
                logging.info(f"[{gold_type_id}] Đang thực thi ghi lịch sử SCD Type 2...")
                success = self.scd2_loader.load_history(
                    run_id, record_hash_id, gold_type_id, source_url, 
                    buy_price, sell_price, new_hash, data_date, "PRICE_UPDATE"
                )
                if not success:
                    success_flag = False
            except Exception as e:
                logging.error(f"[{gold_type_id}] -> Lỗi hệ thống khi Load History: {e}")
                success_flag = False

        logging.info("========== HOÀN TẤT LOAD HISTORY ==========")
        sys.exit(0 if success_flag else 1)

if __name__ == "__main__":
    job = JobBtmcLoadHistory()
    job.run_pipeline()