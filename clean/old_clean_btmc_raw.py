import json
import argparse
import sys
from database.connection import connection, cursor

def clean_html_tags(raw_val):
    if not raw_val: 
        return None
    return raw_val.replace("<b>", "").replace("</b>", "").strip()

def process_clean_raw_json(raw_payload_str):

    try:
        raw_json = json.loads(raw_payload_str)
        cleaned_data = {
            'btmcvangnhanmua':  clean_html_tags(raw_json.get('btmcvangnhanmua')),
            'btmcvangnhanban':  clean_html_tags(raw_json.get('btmcvangnhanban')),
            'sjcmua':           clean_html_tags(raw_json.get('sjcmua')),
            'sjcban':           clean_html_tags(raw_json.get('sjcban'))
        }
        return json.dumps(cleaned_data, ensure_ascii=False)
    except:
        return None

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Debug độc lập bước dọn dẹp JSON thô")
    parser.add_argument('--run_id', type=str, required=True)
    args = parser.parse_args()

    print(f"\n[DEBUG CLEAN RAW] RUN_ID: {args.run_id}")
    query = "SELECT raw_payload FROM raw_gold_price WHERE run_id = %s AND status = 'success' ORDER BY raw_id DESC LIMIT 1"
    cursor.execute(query, (args.run_id,))
    row = cursor.fetchone()

    if row:
        print(f" -> Dữ liệu thô gốc trong DB:\n    {row[0]}")
        ok_json = process_clean_raw_json(row[0])
        print(f" -> Dữ liệu sau khi tinh gọn:\n    {ok_json}")
        cursor.close()
        connection.close()
        if ok_json:
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        print(f"[THẤT BẠI] Không tìm thấy dữ liệu thô của ngày '{args.run_id}'.")
        cursor.close()
        connection.close()
        sys.exit(1)