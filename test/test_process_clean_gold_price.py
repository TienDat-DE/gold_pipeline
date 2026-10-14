from database.connection import (
    connection,
    cursor
)

from clean.process_clean_gold_price import process_clean_gold_price

# ======================
# GET LATEST RAW DATA
# ======================

query = """
SELECT
    raw_id,
    run_id,
    store_id,
    source_url,
    raw_payload
FROM raw_gold_price
ORDER BY raw_id DESC
LIMIT 1
"""

cursor.execute(query)

result = cursor.fetchone()

raw_id = result[0]

run_id = result[1]

store_id = result[2]

source_url = result[3]

raw_payload = result[4]

print('\n===== RAW DATA =====\n')

print(f'raw_id: {raw_id}')

print(f'run_id: {run_id}')

# ======================
# PROCESS CLEAN GOLD PRICE
# ======================

process_clean_gold_price(
    run_id=run_id,
    raw_id=raw_id,
    store_id=store_id,
    source_url=source_url,
    raw_payload=raw_payload
)

# ======================
# CLOSE CONNECTION
# ======================

cursor.close()

connection.close()