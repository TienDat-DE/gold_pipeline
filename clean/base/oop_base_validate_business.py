from datetime import datetime

class BaseValidateBusinessOOP:
    def __init__(self, min_price=10000000, max_price=500000000):
        self.min_price = min_price
        self.max_price = max_price

    def get_pairs_to_check(self):
        raise NotImplementedError("Class Con phải khai báo các cặp [Mua, Bán]!")

    def validate(self, run_id, normalized_dict):
        # 1. DATETIME_FORMAT_MISMATCH: Kiểm tra định dạng ngày từ run_id
        try:
            date_part = run_id.split('_')[0]
            data_date = datetime.strptime(date_part, '%Y%m%d')
        except Exception as e:
            return False, 'DATETIME_FORMAT_MISMATCH', f'Mã run_id sai cấu trúc định dạng ngày: {e}'

        # 2. WRONG_DATE_ERROR: Chặn dữ liệu đến từ tương lai[cite: 7]
        if data_date.date() > datetime.now().date():
            return False, 'WRONG_DATE_ERROR', f'Dữ liệu ngày {data_date.strftime("%Y-%m-%d")} thuộc về tương lai.'

        # 3. PRICE_OUT_OF_BOUNDS: Kiểm tra giá trần/sàn và logic Mua < Bán[cite: 7]
        pairs = self.get_pairs_to_check()
        for buy_key, sell_key in pairs:
            buy = normalized_dict.get(buy_key, 0)
            sell = normalized_dict.get(sell_key, 0)

            # Cảnh báo giá nhảy vọt vô lý[cite: 7]
            if not (self.min_price <= buy <= self.max_price) or not (self.min_price <= sell <= self.max_price):
                return False, 'PRICE_OUT_OF_BOUNDS', f"Giá cặp '{buy_key}/{sell_key}' nhảy vọt vô lý: Mua {buy} | Bán {sell}"
                
            # Cảnh báo lỗi logic: Cửa hàng mua vào đắt hơn bán ra[cite: 7]
            if buy > sell:
                return False, 'PRICE_OUT_OF_BOUNDS', f"Lỗi logic cửa hàng: Giá mua ({buy}) cao hơn giá bán ({sell}) tại '{buy_key}/{sell_key}'"

        return True, 'SUCCESS', 'Dữ liệu an toàn logic tài chính.'