from clean.base.oop_base_normalizer import BaseNormalizerOOP

class BtmcNormalizerOOP(BaseNormalizerOOP):
    def __init__(self):
        # BTMC sử dụng hệ số nhân 10.000[cite: 6]
        super().__init__(unit_multiplier=10000)

    def normalize_payload(self, text_dict):
        normalized_data = {}
        # Các field cần xử lý của BTMC[cite: 6]
        target_keys = ['sjcmua', 'sjcban', 'btmcvangnhanmua', 'btmcvangnhanban']
        
        for key in target_keys:
            raw_val = text_dict.get(key)
            
            is_ok, num_val, msg = self.clean_and_convert_price(raw_val, field_name=key)
            
            # Bẫy lỗi: Nếu 1 field hỏng, đánh rớt toàn bộ payload này[cite: 6]
            if not is_ok:
                return False, None, msg
                
            normalized_data[key] = num_val
            
        return True, normalized_data, "Success"