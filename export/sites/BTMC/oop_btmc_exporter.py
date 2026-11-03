import os
from datetime import datetime
from export.base.oop_base_exporter import BaseExporterOOP

class BtmcExporterOOP(BaseExporterOOP):
    def __init__(self):
        super().__init__(data_lake_path="./data_lake")
        self.store_id = 1 # ID của BTMC

    def _get_date_from_run_id(self, run_id):
        """Tách chuỗi run_id thành datetime object để chia thư mục năm/tháng"""
        date_str = run_id.split('_')[0]
        return datetime.strptime(date_str, '%Y%m%d')

    def backup_raw_data(self, run_id):
        """Sao lưu dữ liệu thô HTML (Kho lạnh) THEO RUN_ID"""
        target_date = self._get_date_from_run_id(run_id)
        
        # Chỉ lấy RAW phát sinh trong lần chạy này
        query = "SELECT * FROM raw_gold_price WHERE run_id = %s AND store_id = %s"
        
        dir_path = self.get_partition_path("backups/raw_data", target_date)
        file_name = f"raw_gold_{run_id}.jsonl"
        file_path = os.path.join(dir_path, file_name)
        
        return self.export_to_jsonl(query, (run_id, self.store_id), file_path)

    def export_bi_current(self, run_id):
        """Xuất Snapshot giá hiện tại phục vụ Dashboard (Business)"""
        # Snapshot cho BI luôn cần toàn bộ giá MỚI NHẤT hiện tại của cửa hàng
        query = "SELECT * FROM gold_price_history WHERE store_id = %s AND is_current = 1"
        
        dir_path = os.path.join(self.data_lake_path, "output_bi")
        self._create_dir_if_not_exists(dir_path)
        
        file_name = f"current_gold_prices_{run_id}.parquet"
        file_path = os.path.join(dir_path, file_name)
        
        return self.export_to_parquet(query, (self.store_id,), file_path)
        
    def backup_history_data(self, run_id):
        """Sao lưu CHỈ NHỮNG LỊCH SỬ MỚI PHÁT SINH trong lần chạy này (Incremental)"""
        target_date = self._get_date_from_run_id(run_id)
        
        # Khóa chặt bằng run_id để tránh kéo toàn bộ dữ liệu lịch sử cũ
        query = "SELECT * FROM gold_price_history WHERE run_id = %s AND store_id = %s"
        
        dir_path = self.get_partition_path("backups/history_data", target_date)
        file_name = f"history_gold_{run_id}.parquet"
        file_path = os.path.join(dir_path, file_name)
        
        return self.export_to_parquet(query, (run_id, self.store_id), file_path)