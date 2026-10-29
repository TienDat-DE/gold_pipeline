import json
import argparse
import traceback
import sys
from datetime import datetime
from database.connection import connection, cursor
from database.queries import error_log_query
from clean.clean_btmc_raw import process_clean_raw_json
from clean.normalize_price import normalize_price

def insert_business_error(run_id, raw_id, error_type, error_message):
    error_values = (run_id, raw_id, 1, None, 'VALIDATE_BUSINESS', error_type, error_message, traceback.format_exc(), None)
    cursor.execute(error_log_query, error_values)
    connection.commit()
    print(f" -> [ LOG ERROR_LOG] {error_type}: {error_message}")

def validate_business(run_id, raw_id, normalized_data_list, is_debug=False):
    if is_debug:
        print(f" -> Đang tiến hành validate_business cho raw_id: {raw_id}")
        
    # DATETIME_FORMAT_MISMATCH
    try:
        date_part = run_id.split('_')[0]
        data_date = datetime.strptime(date_part, '%Y%m%d')
        data_date_str = data_date.strftime('%Y-%m-%d')
    except Exception as e:
        insert_business_error(run_id, raw_id, 'DATETIME_FORMAT_MISMATCH', f'Mã run_id sai cấu trúc định dạng ngày: {e}')
        return False

    # WRONG_DATE_ERROR
    if data_date.date() > datetime.now().date():
        insert_business_error(run_id, raw_id, 'WRONG_DATE_ERROR', f'Dữ liệu ngày {data_date_str} thuộc về tương lai.')
        return False

    # PRICE_OUT_OF_BOUNDS
    MIN_PRICE, MAX_PRICE = 10000000, 500000000

    for item in normalized_data_list:
        gold_type = item['gold_type_name']
        buy = item['buy_price']
        sell = item['sell_price']

        if not (MIN_PRICE <= buy <= MAX_PRICE) or not (MIN_PRICE <= sell <= MAX_PRICE):
            insert_business_error(run_id, raw_id, 'PRICE_OUT_OF_BOUNDS', f"Giá loại '{gold_type}' nhảy vọt vô lý: Mua {buy} | Bán {sell}")
            return False
            
        if buy > sell:
            insert_business_error(run_id, raw_id, 'PRICE_OUT_OF_BOUNDS', f"Lỗi logic cửa hàng: Giá mua {buy} cao hơn giá bán {sell}")
            return False

    if is_debug:
        print(" [VALIDATE BUSINESS SUCCESS] Dữ liệu an toàn logic tài chính. \n")
    return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Debug độc lập bước Validate Business")
    parser.add_argument('--run_id', type=str, required=True)
    args = parser.parse_args()

    print(f"\n[DEBUG VALIDATE BUSINESS] RUN_ID: {args.run_id}")
    query = "SELECT raw_id, run_id, raw_payload FROM raw_gold_price WHERE run_id = %s AND status = 'success' ORDER BY raw_id DESC LIMIT 1"
    cursor.execute(query, (args.run_id,))
    row = cursor.fetchone()

    if row:
        r_id, run_id_val, raw_payload_str = row[0], row[1], row[2]
        cleaned_str = process_clean_raw_json(raw_payload_str)
        normalized_list = normalize_price(run_id=run_id_val, raw_id=r_id, cleaned_payload_str=cleaned_str, is_debug=False)
        
        if normalized_list:
            business_ok = validate_business(run_id=run_id_val, raw_id=r_id, normalized_data_list=normalized_list, is_debug=True)
            cursor.close()
            connection.close()
            if business_ok:
                sys.exit(0)
            else:
                sys.exit(1)
        else:
            cursor.close()
            connection.close()
            sys.exit(1)
    else:
        cursor.close()
        connection.close()
        sys.exit(1)