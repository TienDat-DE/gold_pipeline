import json
import argparse
import traceback
import sys
from database.connection import connection, cursor
from database.queries import error_log_query
from clean.clean_btmc_raw import process_clean_raw_json

def insert_normalize_error(run_id, raw_id, error_type, error_message):
    error_values = (run_id, raw_id, 1, None, 'NORMALIZE_PRICE', error_type, error_message, traceback.format_exc(), None)
    cursor.execute(error_log_query, error_values)
    connection.commit()
    print(f" -> [ LOG ERROR_LOG] {error_type}: {error_message}")

def clean_and_convert_price(run_id, raw_id, raw_val, field_name):
    if not raw_val: return None
    try:
        cleaned_str = str(raw_val).replace('.', '').replace(',', '').strip()
        return int(cleaned_str)
    except Exception as e:
        insert_normalize_error(run_id, raw_id, 'CAST_TO_INT_FAILED', f"Không thể ép kiểu số nguyên cho '{field_name}': {raw_val}")
        return None

def normalize_price(run_id, raw_id, cleaned_payload_str, is_debug=False):
    if is_debug:
        print(f" -> Đang tiến hành normalize_price cho raw_id: {raw_id}")
        
    if not cleaned_payload_str: return None
    try:
        data_dict = json.loads(cleaned_payload_str)
    except:
        return None

    sjc_mua = clean_and_convert_price(run_id, raw_id, data_dict.get('sjcmua'), 'sjcmua')
    sjc_ban = clean_and_convert_price(run_id, raw_id, data_dict.get('sjcban'), 'sjcban')
    nhan_mua = clean_and_convert_price(run_id, raw_id, data_dict.get('btmcvangnhanmua'), 'btmcvangnhanmua')
    nhan_ban = clean_and_convert_price(run_id, raw_id, data_dict.get('btmcvangnhanban'), 'btmcvangnhanban')

    if None in [sjc_mua, sjc_ban, nhan_mua, nhan_ban]:
        return None

    normalized_list = [
        {'gold_type_name': 'Vàng SJC', 'buy_price': sjc_mua * 10000, 'sell_price': sjc_ban * 10000},
        {'gold_type_name': 'Vàng nhẫn trơn', 'buy_price': nhan_mua * 10000, 'sell_price': nhan_ban * 10000}
    ]
    
    if is_debug:
        print(" [NORMALIZE PRICE SUCCESS] Quy đổi mảng cấu hình hệ số nhân 10.000 thành công.\n")
    return normalized_list

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Debug độc lập bước Normalize Price")
    parser.add_argument('--run_id', type=str, required=True)
    args = parser.parse_args()

    print(f"\n[DEBUG NORMALIZE PRICE] RUN_ID: {args.run_id}")
    query = "SELECT raw_id, run_id, raw_payload FROM raw_gold_price WHERE run_id = %s AND status = 'success' ORDER BY raw_id DESC LIMIT 1"
    cursor.execute(query, (args.run_id,))
    row = cursor.fetchone()

    if row:
        cleaned_str = process_clean_raw_json(row[2])
        result = normalize_price(run_id=row[1], raw_id=row[0], cleaned_payload_str=cleaned_str, is_debug=True)
        cursor.close()
        connection.close()
        if result:
            print(" -> Mảng đầu ra phục vụ bước sau:\n", json.dumps(result, ensure_ascii=False, indent=4))
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        cursor.close()
        connection.close()
        sys.exit(1)