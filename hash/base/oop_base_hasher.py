import hashlib
from datetime import datetime
from database.oop_connection import DatabaseManagerOOP

class BaseHasherOOP:
    def __init__(self, store_id):
        self.store_id = store_id
        self.db = DatabaseManagerOOP()

    def generate_hash(self, gold_type_id, data_date, buy_price, sell_price):
        """Băm chuỗi dữ liệu thành mã SHA-256 duy nhất"""
        raw_str = f"{self.store_id}_{gold_type_id}_{data_date}_{buy_price}_{sell_price}"
        return hashlib.sha256(raw_str.encode('utf-8')).hexdigest()

    def process_hash(self, run_id, gold_type_id, data_date, buy_price, sell_price, source_url):
        """Kiểm tra Hash tồn tại và lưu lịch sử check"""
        new_hash = self.generate_hash(gold_type_id, data_date, buy_price, sell_price)
        
        # 1. Lấy hash hiện tại (is_current = 1) từ gold_price_history
        conn = self.db.get_connection()
        previous_hash = None
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT hash_value FROM gold_price_history WHERE store_id = %s AND gold_type_id = %s AND is_current = 1",
                (self.store_id, gold_type_id)
            )
            result = cursor.fetchone()
            if result:
                previous_hash = result[0]
        finally:
            cursor.close()
            conn.close()

        # 2. Quyết định trạng thái thay đổi
        is_changed = 1 if new_hash != previous_hash else 0
        
        # 3. Ghi log vào hash_tracking theo đúng sơ đồ draw.io
        insert_query = """
            INSERT INTO hash_tracking 
            (run_id, store_id, gold_type_id, source_url, data_date, hash_value, previous_hash, is_changed, detected_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        record_hash_id = self.db.execute_query(insert_query, (
            run_id, self.store_id, gold_type_id, source_url, data_date, new_hash, previous_hash, is_changed, datetime.now()
        ))
        
        return is_changed, new_hash, record_hash_id