class BaseNormalizerOOP:
    def __init__(self, unit_multiplier=1):
        self.unit_multiplier = unit_multiplier

    def clean_and_convert_price(self, raw_val):
        cleaned_str = str(raw_val).replace('.', '').replace(',', '').strip()
        num_val = int(cleaned_str)
        return num_val * self.unit_multiplier

    def normalize_payload(self, text_dict):
        raise NotImplementedError("Class Con phải tự định nghĩa các key cần chuẩn hóa!")