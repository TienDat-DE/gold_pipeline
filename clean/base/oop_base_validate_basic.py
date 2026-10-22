class BaseValidateBasicOOP:
    def get_required_keys(self):
        raise NotImplementedError("Class Con phải khai báo key bắt buộc!")

    def validate(self, normalized_dict):
        required_keys = self.get_required_keys()
        
        for key in required_keys:
            val = normalized_dict.get(key)
            
            if val is None:
                return False, f"NULL_REQUIRED_FIELD: Thiếu dữ liệu tại '{key}'"
            
            if not isinstance(val, int):
                return False, f"NON_NUMERIC_PRICE: Dữ liệu '{val}' tại '{key}' không phải số nguyên."

        return True, "Success"