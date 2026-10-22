# CHÚ Ý ĐƯỜNG DẪN IMPORT MỚI
from clean.base.oop_base_normalize import BaseNormalizerOOP

class BtmcNormalizerOOP(BaseNormalizerOOP):
    def __init__(self):
        super().__init__(unit_multiplier=1000)

    def normalize_payload(self, raw_dict):
        normalized_data = {}
        target_keys = ['sjcmua', 'sjcban', 'btmcvangnhanmua', 'btmcvangnhanban']
        
        for key in target_keys:
            raw_val = raw_dict.get(key)
            normalized_data[key] = self.clean_to_number(raw_val)
            
        return normalized_data