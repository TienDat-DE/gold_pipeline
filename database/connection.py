from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

# ============================
# LOAD ENV
# ============================
load_dotenv()


# ============================
# MYSQL CONNECTION
# ============================

DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')

engine = create_engine(
    f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}'
    f'@{DB_HOST}:{DB_PORT}/{DB_NAME}'
)

connection = engine.raw_connection()

cursor = connection.cursor()
