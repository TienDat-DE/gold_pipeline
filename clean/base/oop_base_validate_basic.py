class BaseValidateBasicOOP:
    def get_required_keys(self):
        raise NotImplementedError("Class Con phải khai báo key bắt buộc!")

    def validate(self, cleaned_dict):
        required_keys = self.get_required_keys()
        
        for key in required_keys:
            val = cleaned_dict.get(key)
            
            # Lỗi 1: Key không tồn tại hoặc bị rỗng chữ
            if val is None or str(val).strip() == "":
                return False, f"NULL_FIELD: Thiếu hoặc rỗng dữ liệu tại '{key}'"
            
            # Lỗi 2: Chứa chữ cái hoặc ký tự lạ (VD: "16380VND" hoặc "null")
            if not str(val).strip().isdigit():
                return False, f"NON_NUMERIC_STRING: Dữ liệu '{val}' tại '{key}' chứa ký tự lạ, không thể ép kiểu."

        return True, "Success"