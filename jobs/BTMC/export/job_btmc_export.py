import sys
import argparse
import logging
from export.sites.BTMC.oop_btmc_exporter import BtmcExporterOOP

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class JobBtmcExportBackup:
    def __init__(self):
        self.exporter = BtmcExporterOOP()

    def run_daily_export(self, run_id):
        logging.info(f"========== BẮT ĐẦU TIẾN TRÌNH SAO LƯU DATA LẠNH (RUN_ID: {run_id}) ==========")

        # 1. Sao lưu Raw Data (JSONL) theo run_id
        raw_status, raw_rows = self.exporter.backup_raw_data(run_id)
        if raw_status:
            logging.info(f" -> [THÀNH CÔNG] Đã backup {raw_rows} bản ghi RAW.")
        else:
            logging.warning(" -> [TRỐNG] Không có dữ liệu RAW mới.")

        # 2. Xuất bảng BI Current (Parquet)
        bi_status, bi_rows = self.exporter.export_bi_current(run_id)
        if bi_status:
            logging.info(f" -> [THÀNH CÔNG] Đã xuất {bi_rows} bản ghi Snapshot phục vụ BI.")
        else:
            logging.warning(" -> [LỖI] Không thể xuất bảng BI.")

        # 3. Sao lưu Incremental History (Parquet) - Khắc phục lỗi xuất quá nhiều dòng
        hist_status, hist_rows = self.exporter.backup_history_data(run_id)
        if hist_status:
            logging.info(f" -> [THÀNH CÔNG] Đã backup {hist_rows} bản ghi LỊCH SỬ mới sinh ra.")
        else:
            logging.info(" -> [BỎ QUA] Không có biến động giá nên không phát sinh file lịch sử mới.")
        
        logging.info("========== TIẾN TRÌNH SAO LƯU HOÀN TẤT ==========")

if __name__ == "__main__":
    # Đón nhận tham số --run_id từ Master Pipeline
    parser = argparse.ArgumentParser(description="Chạy Export Backup theo Run ID")
    parser.add_argument('--run_id', type=str, required=True)
    args = parser.parse_known_args()[0]
    
    job = JobBtmcExportBackup()
    job.run_daily_export(args.run_id)