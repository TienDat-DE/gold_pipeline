import json
import traceback
import logging
from database.oop_connection import DatabaseManagerOOP
from database.queries import error_log_query

class BaseValidateBasicOOP:
    def __init__(self, store_id, job_name):
        self.store_id = store_id
        self.job_name = job_name
        self.db = DatabaseManagerOOP()

    def get_required_keys(self):
        """Class con bắt buộc phải ghi đè hàm này để khai báo các trường cần kiểm tra"""
        raise NotImplementedError("Class con phải khai báo key bắt buộc!")

    def log_error(self, run_id, raw_id, error_type, error_msg, source_url):
        """
        Ghi lỗi vào bảng error_log chuẩn. 
        gold_type_id = None vì ở bước Basic, ta đang kiểm tra toàn bộ chuỗi chứ chưa tách loại vàng.
        """
        error_values = (
            run_id, 
            raw_id, 
            self.store_id, 
            None, # gold_type_id
            self.job_name, 
            error_type, 
            error_msg, 
            traceback.format_exc(), 
            source_url
        )
        self.db.execute_query(error_log_query, error_values)
        logging.error(f" -> [LOG ERROR_LOG] {error_type}: {error_msg} | Source: {source_url}")

    def validate(self, run_id, raw_id, cleaned_payload_str, source_url, is_debug=False):
        """Logic kiểm duyệt kế thừa nguyên bản từ file validate_basic.py cũ"""
        if is_debug:
            logging.info(f" -> Đang tiến hành validate_basic cho raw_id: {raw_id}")
            
        # 1. Kiểm tra chuỗi rỗng
        if not cleaned_payload_str:
            self.log_error(run_id, raw_id, 'JSON_EMPTY_ERROR', 'Chuỗi dữ liệu truyền vào bị rỗng.', source_url)
            return False
            
        # 2. Kiểm tra format JSON
        try:
            data_dict = json.loads(cleaned_payload_str)
        except Exception as e:
            self.log_error(run_id, raw_id, 'JSON_PARSE_ERROR', f'Lỗi giải nén JSON: {e}', source_url)
            return False

        # 3. Kiểm tra các trường bắt buộc và định dạng số
        required_keys = self.get_required_keys()
        for key in required_keys:
            val = data_dict.get(key)
            
            if val is None or str(val).strip() == "":
                self.log_error(run_id, raw_id, 'MISSING_REQUIRED_FIELD', f"Thiếu trường cốt lõi hoặc rỗng: '{key}'", source_url)
                return False
                
            if not str(val).strip().isdigit():
                self.log_error(run_id, raw_id, 'INVALID_NUMBER_FORMAT', f"Trường '{key}' chứa ký tự không phải số: '{val}'", source_url)
                return False
                
        if is_debug:
            logging.info(" [VALIDATE BASIC SUCCESS] Dữ liệu số hợp lệ, không chứa ký tự lạ.\n")
        return True