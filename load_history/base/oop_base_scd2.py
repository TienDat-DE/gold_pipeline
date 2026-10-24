from datetime import datetime
import logging
from database.oop_connection import DatabaseManagerOOP

class BaseSCD2LoaderOOP:
    def __init__(self, store_id):
        self.store_id = store_id
        self.db = DatabaseManagerOOP()

    def get_current_version(self, gold_type_id):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT version FROM gold_price_history WHERE store_id = %s AND gold_type_id = %s AND is_current = 1", (self.store_id, gold_type_id))
            result = cursor.fetchone()
            return result[0] if result else 0
        finally:
            cursor.close()
            conn.close()

    def load_history(self, run_id, record_hash_id, gold_type_id, source_url, buy_price, sell_price, new_hash, data_date, change_reason):
        conn = self.db.get_connection()
        if not conn: return False

        try:
            cursor = conn.cursor()
            current_time = datetime.now()
            new_version = self.get_current_version(gold_type_id) + 1

            # Bước 1: Update old record (Đóng hiệu lực)
            if new_version > 1:
                update_query = """
                    UPDATE gold_price_history 
                    SET is_current = 0, valid_to = %s 
                    WHERE store_id = %s AND gold_type_id = %s AND is_current = 1
                """
                cursor.execute(update_query, (current_time, self.store_id, gold_type_id))

            # Bước 2: Insert new record (Mở hiệu lực mới)
            insert_query = """
                INSERT INTO gold_price_history 
                (run_id, record_hash_id, store_id, gold_type_id, source_url, buy_price, sell_price, 
                 valid_from, valid_to, is_current, hash_value, data_date, change_reason, version, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NULL, 1, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (
                run_id, record_hash_id, self.store_id, gold_type_id, source_url, buy_price, sell_price,
                current_time, new_hash, data_date, change_reason, new_version, current_time
            ))

            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logging.error(f"[SCD2] Lỗi cập nhật lịch sử: {e}")
            return False
        finally:
            cursor.close()
            conn.close()