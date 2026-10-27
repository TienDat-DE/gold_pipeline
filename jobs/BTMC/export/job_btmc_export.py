import logging
from datetime import datetime
from export.sites.BTMC.oop_btmc_exporter import BtmcExporterOOP

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class JobBtmcExportBackup:
    def __init__(self):
        self.exporter = BtmcExporterOOP()

    def run_daily_export(self):
        # Mặc định lấy ngày hôm nay để chạy backup
        target_date = datetime.now()
        logging.info(f"========== BẮT ĐẦU TIẾN TRÌNH SAO LƯU DATA LẠNH CHO BTMC ({target_date.strftime('%Y-%m-%d')}) ==========")

        # 1. Sao lưu Raw Data (JSONL)
        raw_status, raw_rows = self.exporter.backup_raw_data(target_date)
        if raw_status:
            logging.info(f" -> [THÀNH CÔNG] Đã backup {raw_rows} bản ghi RAW.")
        else:
            logging.warning(" -> [TRỐNG] Không có dữ liệu RAW mới hôm nay.")

        # 2. Xuất bảng BI Current (Parquet)
        bi_status, bi_rows = self.exporter.export_bi_current(target_date)
        if bi_status:
            logging.info(f" -> [THÀNH CÔNG] Đã xuất {bi_rows} bản ghi Snapshot phục vụ BI.")
        else:
            logging.warning(" -> [LỖI] Không thể xuất bảng BI.")

        # 3. Sao lưu Full History (Parquet)
        hist_status, hist_rows = self.exporter.backup_history_data(target_date)
        if hist_status:
            logging.info(f" -> [THÀNH CÔNG] Đã backup toàn bộ {hist_rows} bản ghi LỊCH SỬ.")
        
        logging.info("========== TIẾN TRÌNH SAO LƯU HOÀN TẤT ==========")

if __name__ == "__main__":
    job = JobBtmcExportBackup()
    job.run_daily_export()