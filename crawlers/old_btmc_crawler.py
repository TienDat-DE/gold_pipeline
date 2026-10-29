import argparse
import traceback
import time
import sys  
from datetime import datetime
import tls_client
from database.connection import connection, cursor
from database.queries import web_response_query, error_log_query

# ======================
# THAM SỐ DÒNG LỆNH & CẤU HÌNH HỆ THỐNG
# ======================

parser = argparse.ArgumentParser(description="BTMC Gold History API Crawler Robust Version")
parser.add_argument('--date', type=str, default=datetime.now().strftime('%Y%m%d'), help="Định dạng YYYYMMDD")
args = parser.parse_known_args()[0]

# Kiểm tra nếu ngày gõ vào không đủ hoặc thừa số (Phải chuẩn 8 ký tự)
if len(args.date) != 8 or not args.date.isdigit():
    print(f"\n[LỖI NGHIÊM TRỌNG] Ngày truyền vào '{args.date}' không hợp lệ!")
    print("-> Vui lòng truyền chính xác 8 chữ số dạng YYYYMMDD (Ví dụ: 20260505).")
    sys.exit(1) # Sửa thành sys.exit(1) để báo lỗi thẳng cho Airflow ngắt Task ngay lập tức

formatted_date = f"{args.date[6:8]}/{args.date[4:6]}/{args.date[0:4]}"
run_id = f"{args.date}_BTMC"
api_url = 'https://btmc.vn/ProductHome/getGoldDate'
job_name = 'BTMC_CRAWLER'
store_id = 1
max_retry = 5
timeout_sec = 60

print(f"\n[START] Khởi động phiên chạy: {run_id} | Ngày tra cứu: {formatted_date}")

# ======================
# GHI LOG KHỞI ĐỘNG LUỒNG CHẠY (PIPELINE LOG)
# ======================

try:
    upsert_pipeline_query = """
        INSERT INTO pipeline_log (run_id, job_name, status) VALUES (%s, %s, 'running')
        ON DUPLICATE KEY UPDATE status = VALUES(status)
    """
    cursor.execute(upsert_pipeline_query, (run_id, job_name))
    connection.commit()
except Exception as db_init_err:
    print(f"[LỖI DATABASE] Không thể khởi tạo log pipeline: {db_init_err}")
    sys.exit(1)

# ======================
# LUỒNG CÀO MẠNG XỬ LÝ LỖI & THỬ LẠI (WHILE & TRY-EXCEPT)
# ======================

retry_count = 0
status = 'fail'
response_code = None
response_body = None
last_error = None

# Khởi tạo giải pháp bẻ gãy tường lửa BTMC 
session = tls_client.Session(client_identifier="chrome_120", random_tls_extension_order=True)
headers = {
    'Accept': '*/*', 'Accept-Language': 'vi', 'Connection': 'keep-alive',
    'Referer': 'https://btmc.vn/gia-vang-theo-ngay.html', 'X-Requested-With': 'XMLHttpRequest',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36'
}

while retry_count < max_retry:
    try:
        print(f"Attempt: {retry_count + 1}/{max_retry} | Gửi request tới API...")
        response = session.get(api_url, params={'date': formatted_date}, headers=headers, timeout_seconds=timeout_sec)
        
        response_code = response.status_code
        response_body = response.text
        
        # Bẫy lỗi bảo mật ngầm: Nếu dính HTML báo lỗi thay vì chuỗi JSON sạch
        if "CẢNH BÁO HỆ THỐNG" in response_body or "Object moved" in response_body or response_code != 200:
            print(" -> [CẢNH BÁO] Phản hồi lỗi hệ thống (WAF Chặn hoặc Sai cấu trúc). Thử lại sau 5 giây...")
            retry_count += 1
            time.sleep(5)
            continue
            
        status = 'success'
        print(" [THÀNH CÔNG] Đã lấy trọn vẹn chuỗi JSON lịch sử!")
        break
        
    except Exception as error:
        retry_count += 1
        last_error = traceback.format_exc()
        print(f" -> [LỖI MẠNG CHẬP CHỜN]: {error}. Đang thử lại...")
        time.sleep(5)

# ======================
# NẠP DỮ LIỆU VÀO TẦNG PHẢN HỒI MẠNG (WEB RESPONSES)
# ======================
actual_url = f"{api_url}?date={formatted_date.replace('/', '%2F')}"
web_response_values = (run_id, store_id, response_code, response_body, status, actual_url, retry_count)

try:
    cursor.execute(web_response_query, web_response_values)
    connection.commit()
    print(f"Inserted web_responses thành công. ID bản ghi: {cursor.lastrowid}")
except Exception as db_web_err:
    print(f"[LỖI DATABASE] Không thể lưu web_responses: {db_web_err}")
    sys.exit(1)

# ======================
# GHI LOG LỖI NẾU Crawl THẤT BẠI TOÀN BỘ (ERROR LOG)
# ======================
if status == 'fail':
    error_values = (
        run_id, None, store_id, None, job_name, 
        'CRAWL_FAILED', f'Thất bại hoàn toàn sau {max_retry} lần cào ngày {formatted_date}', 
        last_error, actual_url
    )
    cursor.execute(error_log_query, error_values)
    connection.commit()
    print(" -> [NGUY HIỂM] Đã ghi nhận log lỗi chi tiết vào bảng error_log.")
    
    # Giải phóng tài nguyên và kết thúc luồng với mã lỗi 1 để Airflow biết
    cursor.close()
    connection.close()
    sys.exit(1)

# ======================
# GIẢI PHÓNG KẾT NỐI DATABASE
# ======================
cursor.close()
connection.close()
print(f"===== HOÀN TẤT PHIÊN CHẠY LUỒNG CHO: {run_id} =====\n")
sys.exit(0) # Trả về mã thành công tuyệt đối cho Airflow