import os
import pandas as pd
from datetime import datetime
from database.oop_connection import DatabaseManagerOOP
import warnings

# Tắt cảnh báo SQLAlchemy của Pandas
warnings.filterwarnings('ignore', category=UserWarning)

class BaseExporterOOP:
    def __init__(self, data_lake_path="./data_lake"):
        self.data_lake_path = data_lake_path
        self.db = DatabaseManagerOOP()

    def _create_dir_if_not_exists(self, path):
        os.makedirs(path, exist_ok=True)

    def get_partition_path(self, folder_name, date_obj):
        """Tự động sinh cấu trúc thư mục: folder_name/year=YYYY/month=MM"""
        year_str = date_obj.strftime("%Y")
        month_str = date_obj.strftime("%m")
        path = os.path.join(self.data_lake_path, folder_name, f"year={year_str}", f"month={month_str}")
        self._create_dir_if_not_exists(path)
        return path

    def export_to_parquet(self, query, params, output_path):
        """Xuất dữ liệu SQL ra file siêu nén Parquet"""
        conn = self.db.get_connection()
        try:
            df = pd.read_sql(query, conn, params=params)
            if not df.empty:
                df.to_parquet(output_path, engine='pyarrow', index=False)
                return True, len(df)
            return False, 0
        except Exception as e:
            print(f"Lỗi xuất Parquet: {e}")
            return False, -1
        finally:
            conn.close()

    def export_to_jsonl(self, query, params, output_path):
        """Xuất dữ liệu thô ra file JSON Lines"""
        conn = self.db.get_connection()
        try:
            df = pd.read_sql(query, conn, params=params)
            if not df.empty:
                df.to_json(output_path, orient='records', lines=True, force_ascii=False)
                return True, len(df)
            return False, 0
        except Exception as e:
            print(f"Lỗi xuất JSONL: {e}")
            return False, -1
        finally:
            conn.close()