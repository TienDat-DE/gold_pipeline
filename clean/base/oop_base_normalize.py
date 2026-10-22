import re

class BaseNormalizerOOP:
    def __init__(self, unit_multiplier=1):
        self.unit_multiplier = unit_multiplier

    def clean_to_number(self, raw_str):
        if not raw_str:
            return None
        no_html = re.sub(r'<[^>]+>', '', str(raw_str))
        clean_str = no_html.replace(',', '').replace('.', '').strip()
        
        if clean_str.isdigit():
            return int(clean_str) * self.unit_multiplier
        return None

    def normalize_payload(self, raw_dict):
        raise NotImplementedError("Class Con phải tự map các key cần chuẩn hóa!")