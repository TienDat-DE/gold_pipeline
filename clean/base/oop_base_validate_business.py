class BaseValidateBusinessOOP:
    def __init__(self, min_price=1000000, max_price=200000000):
        self.min_price = min_price
        self.max_price = max_price

    def get_pairs_to_check(self):
        raise NotImplementedError("Class Con phải khai báo các cặp [Mua, Bán]!")

    def validate(self, normalized_dict):
        pairs = self.get_pairs_to_check()
        
        for buy_key, sell_key in pairs:
            buy_price = normalized_dict.get(buy_key, 0)
            sell_price = normalized_dict.get(sell_key, 0)
            
            if not (self.min_price <= buy_price <= self.max_price):
                return False, f"PRICE_OUT_OF_BOUNDS: Giá {buy_price} tại '{buy_key}' nằm ngoài khoảng cho phép."
            
            if sell_price <= buy_price:
                return False, f"INVALID_SPREAD: Lỗi logic - Bán ({sell_price}) <= Mua ({buy_price})."

        return True, "Success"