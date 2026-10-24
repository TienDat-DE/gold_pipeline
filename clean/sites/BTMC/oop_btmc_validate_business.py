from clean.base.oop_base_validate_business import BaseValidateBusinessOOP

class BtmcValidateBusinessOOP(BaseValidateBusinessOOP):
    def __init__(self):
        # Thiết lập biên độ giá hợp lệ theo logic cũ[cite: 7]
        super().__init__(min_price=10000000, max_price=500000000)

    def get_pairs_to_check(self):
        # Định nghĩa các cặp [Mua, Bán] cần đưa vào luồng kiểm duyệt
        return [
            ('sjcmua', 'sjcban'),
            ('btmcvangnhanmua', 'btmcvangnhanban')
        ]