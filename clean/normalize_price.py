class BaseNormalizerOOP:
    def __init__(self, unit_multiplier=1):
        self.unit_multiplier = unit_multiplier

    def clean_and_convert_price(self, raw_val, field_name):
        """Xử lý dấu phân cách và ép kiểu số nguyên"""
        if raw_val is None or str(raw_val).strip() == "":
            return False, None, f"Dữ liệu '{field_name}' bị rỗng."
        
        try:
            # Loại bỏ dấu chấm, dấu phẩy chuẩn bị ép kiểu
            cleaned_str = str(raw_val).replace('.', '').replace(',', '').strip()
            num_val = int(cleaned_str)
            return True, num_val * self.unit_multiplier, "Success"
        except Exception as e:
            return False, None, f"CAST_TO_INT_FAILED: Không thể ép kiểu số nguyên cho '{field_name}': {raw_val}"

    def normalize_payload(self, text_dict):
        raise NotImplementedError("Class Con phải tự định nghĩa các key cần chuẩn hóa!")