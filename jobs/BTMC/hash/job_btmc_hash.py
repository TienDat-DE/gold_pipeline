import sys
import argparse
import logging
from database.oop_connection import DatabaseManagerOOP
from hash.sites.BTMC.oop_btmc_hasher import BtmcHasherOOP

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class JobBtmcHash:
    def __init__(self):
        self.db = DatabaseManagerOOP()
        self.hasher = BtmcHasherOOP()

    def run_pipeline(self):
        parser = argparse.ArgumentParser(description="Điều phối luồng kiểm tra Hash")
        parser.add_argument('--run_id', type=str, required=True)
        args = parser.parse_known_args()[0]
        run_id = args.run_id
        
        logging.info(f"========== BẮT ĐẦU HASH | RUN_ID: {run_id} ==========")
        
        # [SỬA LỖI]: Dùng INNER JOIN với MAX(stg_id) để chỉ lấy đúng 1 dòng mới nhất cho SJC và Nhẫn
        query_staging = """
            SELECT s1.gold_type_id, s1.data_date, s1.buy_price, s1.sell_price, s1.source_url 
            FROM staging_gold_price s1
            INNER JOIN (
                SELECT gold_type_id, MAX(stg_id) as max_stg_id
                FROM staging_gold_price 
                WHERE run_id = %s AND quality_flag = 'good'
                GROUP BY gold_type_id
            ) s2 ON s1.stg_id = s2.max_stg_id
        """
        records = self.db.fetch_all(query_staging, (run_id,))
        
        if not records:
            logging.warning("Không có dữ liệu sạch (good) trong Staging. Bỏ qua luồng Hash.")
            sys.exit(0)

        success_flag = True
        for row in records:
            gold_type_id, data_date, buy_price, sell_price, source_url = row
            try:
                is_changed, _, _ = self.hasher.process_hash(
                    run_id, gold_type_id, data_date, buy_price, sell_price, source_url
                )
                if is_changed == 1:
                    logging.info(f"[{gold_type_id}] Phát hiện biến động! Đã ghi log hash_tracking.")
                else:
                    logging.info(f"[{gold_type_id}] Không thay đổi so với lần trước.")
            except Exception as e:
                logging.error(f"[{gold_type_id}] -> Lỗi khi xử lý Hash: {e}")
                success_flag = False

        logging.info("========== HOÀN TẤT HASH ==========")
        sys.exit(0 if success_flag else 1)

if __name__ == "__main__":
    job = JobBtmcHash()
    job.run_pipeline()