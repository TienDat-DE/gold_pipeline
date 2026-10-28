from clean.base.oop_base_normalizer import BaseNormalizerOOP

class BtmcNormalizerOOP(BaseNormalizerOOP):
    def __init__(self):
        # Khai báo hệ số nhân riêng của BTMC
        super().__init__(unit_multiplier=10000)

    def normalize_payload(self, text_dict):
        normalized_data = {}
        target_keys = ['sjcmua', 'sjcban', 'btmcvangnhanmua', 'btmcvangnhanban']
        
        for key in target_keys:
            raw_val = text_dict.get(key)
            # Ép kiểu trực tiếp không cần phòng thủ
            num_val = self.clean_and_convert_price(raw_val)
            normalized_data[key] = num_val
            
        return normalized_data