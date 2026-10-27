from datetime import datetime
from database.oop_connection import DatabaseManagerOOP

class BaseScd2LoaderOOP:
    def __init__(self, store_id):
        self.store_id = store_id
        self.db = DatabaseManagerOOP()

    def load_history(self, run_id, record_hash_id, gold_type_id, source_url, buy_price, sell_price, new_hash, data_date, change_reason):
        current_time = datetime.now()
        
        try:
            # 1. TÌM VERSION TIẾP THEO (Nếu bảng bạn thiết kế có cột version)
            version_query = "SELECT COALESCE(MAX(version), 0) + 1 FROM gold_price_history WHERE store_id = %s AND gold_type_id = %s"
            version_result = self.db.fetch_all(version_query, (self.store_id, gold_type_id))
            next_version = version_result[0][0] if version_result else 1

            # 2. ĐÓNG RECORD CŨ (Update old)
            update_query = """
                UPDATE gold_price_history 
                SET is_current = 0, valid_to = %s 
                WHERE store_id = %s AND gold_type_id = %s AND is_current = 1
            """
            self.db.execute_query(update_query, (current_time, self.store_id, gold_type_id))

            # 3. MỞ RECORD MỚI (Insert new)
            insert_query = """
                INSERT INTO gold_price_history 
                (run_id, record_hash_id, store_id, gold_type_id, source_url, buy_price, sell_price, 
                 valid_from, valid_to, is_current, hash_value, data_date, change_reason, version, created_at) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            # valid_to của record mới thường để NULL hoặc một mốc thời gian xa trong tương lai (vd: 2099-12-31)
            self.db.execute_query(insert_query, (
                run_id, record_hash_id, self.store_id, gold_type_id, source_url, buy_price, sell_price,
                current_time, None, 1, new_hash, data_date, change_reason, next_version, current_time
            ))
            return True
        except Exception as e:
            print(f"Lỗi khi thực thi SCD2: {e}")
            return False