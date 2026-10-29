from clean.base.oop_base_normalizer import BaseNormalizerOOP

class BtmcNormalizerOOP(BaseNormalizerOOP):
    def normalize_payload(self, data_dict):
        normalized = {}
        # Lặp qua bất kỳ key nào được Pipeline truyền vào (chỉ các key hợp lệ)
        for key, val in data_dict.items():
            normalized[key] = self.clean_and_convert_price(val)
        return normalized