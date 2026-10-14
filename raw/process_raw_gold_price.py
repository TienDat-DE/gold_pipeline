import json
import argparse
import sys  
from datetime import datetime
from database.connection import connection, cursor
from database.queries import raw_gold_price_query

def process_raw_gold_price(run_id, response_id, store_id, source_url, response_body, status):
    crawl_time = datetime.now()
    
    # Lấy ngày ghi nhận dữ liệu từ chính mã run_id (Cắt 8 ký tự đầu YYYYMMDD)
    try:
        date_part = run_id.split('_')[0]
        data_date = datetime.strptime(date_part, '%Y%m%d').strftime('%Y-%m-%d')
    except:
        data_date = crawl_time.strftime('%Y-%m-%d')

    # XỬ LÝ CHUỖI JSON ĐỂ TRÍCH XUẤT NỘI DUNG 
    raw_payload = None
    if status == 'success' and response_body:
        try:
            # Chuyển đổi chuỗi văn bản JSON từ DB thành Dictionary của Python
            json_data = json.loads(response_body)
            
            # Chỉ lấy đúng khối dữ liệu "Data" chứa giá trị các loại vàng
            if "Data" in json_data and json_data["Data"] is not None:
                # Đóng gói Dictionary này thành chuỗi string gọn gàng để nạp vào raw_gold_price
                raw_payload = json.dumps(json_data["Data"], ensure_ascii=False)
                print(" -> Trích xuất khối JSON Data thô thành công.")
                
        except Exception as e:
            print(f" -> Lỗi khi giải nén chuỗi JSON: {e}")
            status = 'fail'

    # ĐÓNG GÓI VÀ NẠP VÀO (RAW_GOLD_PRICE)
    raw_gold_price_values = (
        run_id, response_id, store_id, source_url,
        crawl_time, data_date, raw_payload, status
    )

    try:
        cursor.execute(raw_gold_price_query, raw_gold_price_values)
        connection.commit()
        raw_id = cursor.lastrowid
        print('Inserted raw_gold_price thành công')
        print(f' -> raw_id: {raw_id} | data_date: {data_date}\n')
        return raw_id
    except Exception as db_err:
        print(f" -> Lỗi database khi ghi raw_gold_price: {db_err}")
        connection.rollback()
        return None

# =====================================================================
# KHỐI TRUYỀN THAM SỐ ĐỂ KIỂM TRA HOẶC BACKFILL TẦNG RAW BẤT CỨ LÚC NÀO
# =====================================================================

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Xử lý dữ liệu từ web_responses sang raw_gold_price cho API JSON")
    parser.add_argument(
        '--run_id', 
        type=str, 
        default=datetime.now().strftime('%Y%m%d_BTMC'),
        help="Truyền vào run_id cần xử lý thô (Ví dụ: 20260518_BTMC)"
    )
    args = parser.parse_args()

    print(f"\n[HỆ THỐNG] Đang lấy dữ liệu JSON để xử lý thô cho RUN_ID: {args.run_id}")
    
    # Tìm kiếm bản ghi mới nhất của ngày chỉ định trong bảng web_responses
    query = """
        SELECT response_id, run_id, store_id, source_url, response_body, status
        FROM web_responses
        WHERE run_id = %s
        ORDER BY response_id DESC
        LIMIT 1
    """
    cursor.execute(query, (args.run_id,))
    row = cursor.fetchone()

    if row:
        r_id = process_raw_gold_price(
            run_id=row[1], response_id=row[0], store_id=row[2],
            source_url=row[3], response_body=row[4], status=row[5]
        )
        cursor.close()
        connection.close()
        if r_id:
            sys.exit(0) # Thành công
        else:
            sys.exit(1) # Thất bại do lỗi xử lý nội bộ
    else:
        print(f"[THẤT BẠI] Không tìm thấy dữ liệu mạng của ngày '{args.run_id}' trong bảng web_responses.")
        cursor.close()
        connection.close()
        sys.exit(1) # Báo lỗi cho Airflow nếu không có dữ liệu đầu vào