from clean.base.oop_base_normalizer import BaseNormalizerOOP

class BtmcNormalizerOOP(BaseNormalizerOOP):
    def normalize_payload(self, data_dict):
        normalized = {}
        # Lặp qua bất kỳ key nào được Pipeline truyền vào (chỉ các key hợp lệ)
        for key, val in data_dict.items():
            num_val = self.clean_and_convert_price(val)
            # Tự động nhân 1000 bung tỷ giá (chỉ áp dụng riêng cho class BTMC)
            normalized[key] = num_val * 10000 if num_val is not None else None
        return normalized