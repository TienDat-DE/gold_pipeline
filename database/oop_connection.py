import os
import pymysql
import logging
from dotenv import load_dotenv

load_dotenv()

class DatabaseManagerOOP:
    def __init__(self):
        self.host = os.getenv('DB_HOST', 'localhost')
        self.user = os.getenv('DB_USER', 'root')
        self.password = os.getenv('DB_PASSWORD', '')
        self.database = os.getenv('DB_NAME', 'gold_pipeline')
        self.port = int(os.getenv('DB_PORT', 3306))

    def get_connection(self):
        try:
            conn = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                port=self.port
            )
            return conn
        except Exception as e:
            logging.error(f"[OOP_DB] Lỗi kết nối: {e}")
            return None

    def execute_query(self, query, params=None):
        conn = self.get_connection()
        if not conn:
            return None
            
        try:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            conn.commit()
            last_id = cursor.lastrowid
            return last_id
        except Exception as e:
            logging.error(f"[OOP_DB] Lỗi thực thi lệnh: {e}")
            conn.rollback()
            return None
        finally:
            cursor.close()
            conn.close()