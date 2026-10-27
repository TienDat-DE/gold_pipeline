import os
from export.base.oop_base_exporter import BaseExporterOOP

class BtmcExporterOOP(BaseExporterOOP):
    def __init__(self):
        super().__init__(data_lake_path="./data_lake")
        self.store_id = 1 # ID của BTMC

    def backup_raw_data(self, target_date):
        """Sao lưu dữ liệu thô HTML (Kho lạnh)"""
        date_str = target_date.strftime("%Y-%m-%d")
        query = "SELECT * FROM raw_gold_price WHERE DATE(created_at) = %s AND store_id = %s"
        
        # Lưu vào backups/raw_data/year=.../month=.../
        dir_path = self.get_partition_path("backups/raw_data", target_date)
        file_name = f"raw_gold_BTMC_{target_date.strftime('%Y%m%d')}.jsonl"
        file_path = os.path.join(dir_path, file_name)
        
        return self.export_to_jsonl(query, (date_str, self.store_id), file_path)

    def export_bi_current(self, target_date):
        """Xuất Snapshot giá hiện tại phục vụ Dashboard (Business)"""
        query = "SELECT * FROM gold_price_history WHERE store_id = %s AND is_current = 1"
        
        # Thư mục output_bi không chia year/month để BI tools đọc 1 file duy nhất dễ dàng
        dir_path = os.path.join(self.data_lake_path, "output_bi")
        self._create_dir_if_not_exists(dir_path)
        
        file_name = f"current_gold_prices_BTMC_{target_date.strftime('%Y%m%d')}.parquet"
        file_path = os.path.join(dir_path, file_name)
        
        return self.export_to_parquet(query, (self.store_id,), file_path)
        
    def backup_history_data(self, target_date):
        """Sao lưu toàn bộ bảng lịch sử (Kho lạnh)"""
        query = "SELECT * FROM gold_price_history WHERE store_id = %s"
        
        dir_path = self.get_partition_path("backups/history_data", target_date)
        file_name = f"history_gold_BTMC_{target_date.strftime('%Y%m%d')}.parquet"
        file_path = os.path.join(dir_path, file_name)
        
        return self.export_to_parquet(query, (self.store_id,), file_path)