import sys
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

    def run_pipeline(self, run_id):
        logging.info(f"========== BẮT ĐẦU HASH & LOAD HISTORY | RUN_ID: {run_id} ==========")
        
        # Bước 1: Lấy dữ liệu đã được làm sạch và chuẩn hóa từ bảng Staging
        # Chỉ lấy những bản ghi thuộc về run_id hiện tại
        query_staging = """
            SELECT gold_type_id, data_date, buy_price, sell_price, source_url 
            FROM staging_gold_price 
            WHERE run_id = %s
        """
        records = self.db.fetch_all(query_staging, (run_id,))
        
        if not records:
            logging.info("Không có dữ liệu trong bảng Staging để xử lý Hash.")
            return

        # Bước 2: Cho từng loại vàng chạy qua trạm kiểm tra Hash
        for row in records:
            gold_type_id = row[0]
            data_date = row[1]
            buy_price = row[2]
            sell_price = row[3]
            source_url = row[4]

            # 2A. Băm dữ liệu và đối chiếu với Hash cũ trong cơ sở dữ liệu
            is_changed, new_hash, record_hash_id = self.hasher.process_hash(
                run_id=run_id,
                gold_type_id=gold_type_id,
                data_date=data_date,
                buy_price=buy_price,
                sell_price=sell_price,
                source_url=source_url
            )

            # 2B. Xử lý logic rẽ nhánh (Skip hoặc Load History)
            if is_changed == 0:
                # TRƯỜNG HỢP TRÙNG LẶP: Dừng xử lý loại vàng này, nhảy sang loại tiếp theo
                logging.info(f"[{gold_type_id}] Giá không thay đổi so với lần trước -> SKIP.")
                continue  # Bỏ qua đoạn code phía dưới, quay lại đầu vòng lặp for
            
            # TRƯỜNG HỢP CÓ THAY ĐỔI: Chạy tiếp để ghi vết lịch sử
            logging.info(f"[{gold_type_id}] Phát hiện giá biến động! -> Bắt đầu ghi SCD Type 2...")
            
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
                logging.error(f"[{gold_type_id}] -> Lỗi khi ghi SCD Type 2.")

        logging.info("========== HOÀN TẤT HASH & LOAD HISTORY ==========")

if __name__ == "__main__":
    # Test chạy luồng Hash độc lập
    job = JobBtmcHashPipeline()
    job.run_pipeline(run_id="20261026_BTMC_01")