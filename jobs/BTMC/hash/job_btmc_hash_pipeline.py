import sys
import argparse
import logging
from database.oop_connection import DatabaseManagerOOP

# Import các cỗ máy từ tầng Công cụ (đảm bảo đúng chuẩn chữ hoa BTMC)
from hash.sites.BTMC.oop_btmc_hasher import BtmcHasherOOP
from load_history.sites.BTMC.oop_btmc_scd2 import BtmcSCD2LoaderOOP

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class JobBtmcHashPipeline:
    def __init__(self):
        self.db = DatabaseManagerOOP()
        
        # Khởi tạo cỗ máy kiểm tra Hash và cỗ máy ghi lịch sử
        self.hasher = BtmcHasherOOP()
        self.scd2_loader = BtmcSCD2LoaderOOP()

    def run_pipeline(self):
        # 1. Nhận tham số run_id từ hệ thống điều phối (Airflow)
        parser = argparse.ArgumentParser(description="Điều phối luồng Hash và ghi lịch sử SCD2")
        parser.add_argument('--run_id', type=str, required=True, help="Ví dụ: 20261028_BTMC")
        args = parser.parse_known_args()[0]
        run_id = args.run_id
        
        logging.info(f"========== BẮT ĐẦU HASH & LOAD HISTORY | RUN_ID: {run_id} ==========")
        
        # 2. Lấy dữ liệu từ Staging - FIX BUSINESS LOGIC: Bắt buộc chỉ lấy dữ liệu đạt chuẩn 'good'
        query_staging = """
            SELECT gold_type_id, data_date, buy_price, sell_price, source_url 
            FROM staging_gold_price 
            WHERE run_id = %s AND quality_flag = 'good'
        """
        records = self.db.fetch_all(query_staging, (run_id,))
        
        if not records:
            logging.warning("Không có dữ liệu sạch (good) trong bảng Staging để xử lý Hash. Bỏ qua luồng.")
            sys.exit(0) # Trả về 0 để Airflow ghi nhận Task thành công (dù bỏ qua)

        success_flag = True

        # 3. Cho từng loại vàng chạy qua trạm kiểm tra Hash
        for row in records:
            gold_type_id = row[0]
            data_date = row[1]
            buy_price = row[2]
            sell_price = row[3]
            source_url = row[4]

            try:
                # 3A. Băm dữ liệu, lưu hash_tracking và đối chiếu với Hash cũ
                is_changed, new_hash, record_hash_id = self.hasher.process_hash(
                    run_id=run_id,
                    gold_type_id=gold_type_id,
                    data_date=data_date,
                    buy_price=buy_price,
                    sell_price=sell_price,
                    source_url=source_url
                )

                # 3B. Xử lý logic rẽ nhánh (Skip hoặc Load History)
                if is_changed == 0:
                    logging.info(f"[{gold_type_id}] Giá không thay đổi so với lần trước -> SKIP.")
                    continue
                
                logging.info(f"[{gold_type_id}] Phát hiện biến động! -> Ghi SCD Type 2...")
                
                success = self.scd2_loader.load_history(
                    run_id=run_id,
                    record_hash_id=record_hash_id,
                    gold_type_id=gold_type_id,
                    source_url=source_url,
                    buy_price=buy_price,
                    sell_price=sell_price,
                    new_hash=new_hash,
                    data_date=data_date,
                    change_reason="PRICE_UPDATE"
                )
                
                if success:
                    logging.info(f"[{gold_type_id}] -> Ghi lịch sử thành công.")
                else:
                    logging.error(f"[{gold_type_id}] -> Lỗi Database khi ghi SCD Type 2.")
                    success_flag = False

            except Exception as e:
                logging.error(f"[{gold_type_id}] -> Lỗi hệ thống trong quá trình Hash/Load: {e}")
                success_flag = False

        logging.info("========== HOÀN TẤT HASH & LOAD HISTORY ==========")
        
        # 4. Trả Code cho Airflow
        if success_flag:
            sys.exit(0)
        else:
            sys.exit(1)

if __name__ == "__main__":
    job = JobBtmcHashPipeline()
    job.run_pipeline()