import hashlib

def generate_smart_hash(store_name, gold_type_name, buy_price, sell_price):
    """
    Tạo chữ ký nhận diện trạng thái giá vàng.
    Chuỗi băm bao gồm: Tên cửa hàng + Tên loại vàng + Giá mua + Giá bán.
    """
    if None in [store_name, gold_type_name, buy_price, sell_price]:
        return None
        
    # Chuẩn hóa dữ liệu đầu vào để tránh sai lệch do khoảng trắng hoặc kiểu dữ liệu
    store_str = str(store_name).strip().upper()
    gold_str = str(gold_type_name).strip().upper()
    buy_str = str(buy_price).strip()
    sell_str = str(sell_price).strip()
    
    # Nối chuỗi tạo cấu trúc duy nhất. Ví dụ: "BTMC_VANG_SJC_85000000_87000000"
    string_to_hash = f"{store_str}_{gold_str}_{buy_str}_{sell_str}"
    
    # Mã hóa bằng MD5
    return hashlib.md5(string_to_hash.encode('utf-8')).hexdigest()

if __name__ == '__main__':
    # Debug trực tiếp để thấy sự khác biệt
    print("1. BTMC, SJC, Giá không đổi:    ", generate_smart_hash("BTMC", "SJC", 123000000, 124000000))
    print("2. BTMC, SJC, Đổi giá bán:      ", generate_smart_hash("BTMC", "SJC", 123000000, 125000000))
    print("3. PNJ,  SJC, Cùng giá BTMC (1):", generate_smart_hash("PNJ", "SJC", 123000000, 124000000)) 
    # Kết quả (1) và (3) sẽ ra 2 mã Hash khác nhau hoàn toàn, đáp ứng đúng nhu cầu mở rộng chuỗi cửa hàng của bạn!