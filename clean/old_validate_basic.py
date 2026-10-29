import json
import argparse
import traceback
import sys
from database.connection import connection, cursor
from database.queries import error_log_query
from clean.clean_btmc_raw import process_clean_raw_json

def insert_validation_error(run_id, raw_id, error_type, error_message, source_url):
    error_values = (run_id, raw_id, 1, None, 'VALIDATE_BASIC', error_type, error_message, traceback.format_exc(), source_url)
    cursor.execute(error_log_query, error_values)
    connection.commit()
    print(f" -> [ LOG ERROR_LOG] {error_type}: {error_message} | Source: {source_url}")

def validate_basic(run_id, raw_id, cleaned_payload_str, source_url, is_debug=False):
    if is_debug:
        print(f" -> Đang tiến hành validate_basic cho raw_id: {raw_id}")
        
    if not cleaned_payload_str:
        insert_validation_error(run_id, raw_id, 'JSON_EMPTY_ERROR', 'Chuỗi dữ liệu truyền vào bị rỗng.', source_url)
        return False
        
    try:
        data_dict = json.loads(cleaned_payload_str)
    except Exception as e:
        insert_validation_error(run_id, raw_id, 'JSON_PARSE_ERROR', f'Lỗi giải nén JSON: {e}', source_url)
        return False

    required_keys = ['sjcmua', 'sjcban', 'btmcvangnhanmua', 'btmcvangnhanban']
    for key in required_keys:
        val = data_dict.get(key)
        if val is None or str(val).strip() == "":
            insert_validation_error(run_id, raw_id, 'MISSING_REQUIRED_FIELD', f"Thiếu trường cốt lõi hoặc rỗng: '{key}'", source_url)
            return False
            
        if not str(val).strip().isdigit():
            insert_validation_error(run_id, raw_id, 'INVALID_NUMBER_FORMAT', f"Trường '{key}' chứa ký tự không phải số: '{val}'", source_url)
            return False
            
    if is_debug:
        print(" [VALIDATE BASIC SUCCESS] Dữ liệu số hợp lệ, không chứa ký tự lạ.\n")
    return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Debug độc lập bước Validate Basic")
    parser.add_argument('--run_id', type=str, required=True)
    args = parser.parse_args()

    print(f"\n[DEBUG VALIDATE BASIC] RUN_ID: {args.run_id}")
    query = "SELECT raw_id, run_id, store_id, source_url, raw_payload FROM raw_gold_price WHERE run_id = %s AND status = 'success' ORDER BY raw_id DESC LIMIT 1"
    cursor.execute(query, (args.run_id,))
    row = cursor.fetchone()

    if row:
        cleaned_str = process_clean_raw_json(row[4])
        # Khi chạy độc lập, truyền thêm row[3] (chính là source_url gốc từ DB) vào hàm
        success = validate_basic(run_id=row[1], raw_id=row[0], cleaned_payload_str=cleaned_str, source_url=row[3], is_debug=True)
        cursor.close()
        connection.close()
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        print(f"[LỖI] Không tìm thấy dữ liệu.")
        cursor.close()
        connection.close()
        sys.exit(1)