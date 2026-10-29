import argparse
import sys
from datetime import datetime
from database.connection import connection, cursor
from database.queries import (
    get_active_hash_query, 
    deactivate_hash_query, 
    insert_hash_query, 
    insert_gold_history_query
)
from hash.create_hash import generate_smart_hash

def process_tracking(run_id):
    print(f"\n[HASH TRACKING] Khởi động luồng rà soát biến động cho RUN_ID: {run_id}")
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        date_part = run_id.split('_')[0]
        current_data_date = datetime.strptime(date_part, '%Y%m%d').strftime('%Y-%m-%d')
    except:
        current_data_date = datetime.now().strftime('%Y-%m-%d')

    # 1. Lấy dữ liệu sạch nhất hiện tại từ kho dim_gold_price
    cursor.execute("SELECT store, gold_type_name, buy_price, sell_price FROM dim_gold_price")
    dim_records = cursor.fetchall()

    if not dim_records:
        print(" -> [BỎ QUA] Không có dữ liệu trong dim_gold_price để xử lý Hash.")
        return False

    success_count = 0

    for record in dim_records:
        store_name, gold_name, buy_price, sell_price = record
        
        # Ánh xạ tên sang ID để khớp với bảng hash_tracking (SCD2)
        store_id = 1 if store_name == "Bảo Tín Minh Châu" else 0
        gold_type_id = 1 if gold_name == "Vàng SJC" else (2 if gold_name == "Vàng nhẫn trơn" else 0)

        if store_id == 0 or gold_type_id == 0:
            continue

        print(f"\n -> Đang kiểm tra Hash cho: {gold_name}...")
        
        # 2. Tạo mã Hash mới từ dữ liệu hiện tại
        new_hash = generate_smart_hash(buy_price, sell_price)
        
        # 3. Lấy mã Hash đang Active từ Database
        cursor.execute(get_active_hash_query, (store_id, gold_type_id))
        active_hash_record = cursor.fetchone()

        is_changed = 1 # Mặc định giả sử là có thay đổi / dữ liệu mới

        if active_hash_record:
            old_hash_id, old_hash_value = active_hash_record
            
            if new_hash == old_hash_value:
                # TRƯỜNG HỢP 1: GIÁ KHÔNG ĐỔI
                print(f"    [NO CHANGE] Mã hash khớp. Giá {gold_name} không thay đổi.")
                is_changed = 0
            else:
                # TRƯỜNG HỢP 2: CÓ BIẾN ĐỘNG GIÁ
                print(f"    [CHANGED] Phát hiện biến động giá! Bắt đầu đóng version cũ...")
                # Vô hiệu hóa hash cũ
                cursor.execute(deactivate_hash_query, (now_str, old_hash_id))
                # Thêm hash mới
                cursor.execute(insert_hash_query, (store_id, gold_type_id, new_hash, buy_price, sell_price, now_str))
                print(f"    [SCD2 UPDATED] Đã cập nhật Hash phiên bản mới.")
        else:
            # TRƯỜNG HỢP 3: DỮ LIỆU LẦN ĐẦU TIÊN XUẤT HIỆN
            print(f"    [NEW] Dữ liệu lần đầu xuất hiện. Khởi tạo Hash mới...")
            cursor.execute(insert_hash_query, (store_id, gold_type_id, new_hash, buy_price, sell_price, now_str))

        # 4. Lưu vào bảng lịch sử cuối cùng (Chỉ lưu nếu có thay đổi hoặc là bản ghi mới)
        if is_changed == 1:
            try:
                cursor.execute(insert_gold_history_query, (store_id, gold_type_id, current_data_date, buy_price, sell_price, is_changed))
                print(f"    [HISTORY SAVED] Đã ghi nhận bản ghi giá mới vào kho lưu trữ lịch sử.")
            except Exception as e:
                print(f"    [LỖI HISTORY] Không thể ghi lịch sử: {e}")
                connection.rollback()
                return False
                
        success_count += 1

    if success_count > 0:
        connection.commit()
        print("\n [HOÀN THÀNH] Toàn bộ tiến trình xử lý Hash & Lịch sử kết thúc tốt đẹp.")
        return True
    return False

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Luồng rà soát Hash và lưu vết lịch sử")
    parser.add_argument('--run_id', type=str, required=True, help="Ví dụ: 20260518_BTMC")
    args = parser.parse_args()

    result = process_tracking(args.run_id)
    
    cursor.close()
    connection.close()
    
    if result:
        sys.exit(0)
    else:
        sys.exit(1)