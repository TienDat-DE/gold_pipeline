# File: database/queries.py

# =========================
# PIPELINE LOG
# =========================
pipeline_log_query = '''
INSERT INTO pipeline_log(
    run_id,
    job_name,
    status
)
VALUES(%s,%s,%s)
'''

# =========================
# WEB RESPONSES
# =========================
web_response_query = '''
INSERT INTO web_responses(
    run_id,
    store_id,
    response_code,
    response_body,
    status,
    source_url,
    retry_count
)
VALUES (%s,%s,%s,%s,%s,%s,%s)
'''

# =========================
# ERROR LOG
# =========================
error_log_query = '''
INSERT INTO error_log(
    run_id,
    raw_id,
    store_id,
    gold_type_id,
    job_name,
    error_type,
    error_message,
    stack_trace,
    source_url
)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
'''

# ==========================
# GET WEB RESPONSE 
# ==========================
get_web_response_query = '''
SELECT
    response_id,
    response_body,
    status
FROM web_responses
WHERE run_id = %s
'''

# =========================
# INSERT RAW GOLD PRICE
# =========================
raw_gold_price_query = '''
INSERT INTO raw_gold_price(
    run_id,
    response_id,
    store_id,
    source_url,
    crawl_time,
    data_date,
    raw_payload,
    status
)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
'''

# ==========================
# CẬP NHẬT: INSERT STAGING_GOLD_PRICE (Thay thế cho clean_gold_price cũ)
# ==========================
staging_gold_price_query = '''
INSERT INTO staging_gold_price(
    run_id,
    raw_id,
    store_id,
    gold_type_id,
    source_url,
    data_date,
    buy_price,
    sell_price,
    normalized_unit,
    quality_flag
)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
'''

# ==========================
# THÊM MỚI: UPSERT DIM_GOLD_PRICE (Tầng dữ liệu sạch tối giản)
# ==========================
dim_gold_price_upsert_query = '''
INSERT INTO dim_gold_price (
    data_date, 
    store, 
    gold_type_name, 
    buy_price, 
    sell_price, 
    normalized_unit, 
    updated_at
)
VALUES (%s, %s, %s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE 
    updated_at = IF(buy_price != VALUES(buy_price) OR sell_price != VALUES(sell_price), VALUES(updated_at), updated_at),
    buy_price = IF(buy_price != VALUES(buy_price) OR sell_price != VALUES(sell_price), VALUES(buy_price), buy_price),
    sell_price = IF(buy_price != VALUES(buy_price) OR sell_price != VALUES(sell_price), VALUES(sell_price), sell_price);
'''


# ==========================
# HASH TRACKING & HISTORY (CDC - SCD2)
# ==========================

# Lấy mã hash đang active hiện tại của một sản phẩm
get_active_hash_query = '''
SELECT hash_id, hash_value 
FROM hash_tracking 
WHERE store_id = %s AND gold_type_id = %s AND is_active = 1
'''

# Vô hiệu hóa (đóng) mã hash cũ khi có sự thay đổi giá
deactivate_hash_query = '''
UPDATE hash_tracking 
SET is_active = 0, end_date = %s 
WHERE hash_id = %s
'''

# Thêm mã hash mới (mở phiên bản mới)
insert_hash_query = '''
INSERT INTO hash_tracking (
    store_id, gold_type_id, hash_value, buy_price, sell_price, start_date, is_active
) VALUES (%s, %s, %s, %s, %s, %s, 1)
'''

# Ghi nhận dữ liệu vào bảng lịch sử giá vàng
insert_gold_history_query = '''
INSERT INTO gold_price_history (
    store_id, gold_type_id, data_date, buy_price, sell_price, is_changed
) VALUES (%s, %s, %s, %s, %s, %s)
'''