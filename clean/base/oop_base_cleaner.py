import json
import logging

class BaseCleanerOOP:
    def clean_html_tags(self, raw_val):
        if not raw_val:
            return None
        return str(raw_val).replace("<b>", "").replace("</b>", "").strip()

    def extract_and_map(self, raw_json):
        raise NotImplementedError("Class Con phải tự định nghĩa cách lấy biến (key)!")

    def process_clean_raw_json(self, raw_payload_str):
        try:
            raw_json = json.loads(raw_payload_str)
            cleaned_dict = self.extract_and_map(raw_json)
            if cleaned_dict:
                return json.dumps(cleaned_dict, ensure_ascii=False)
            return None
        except json.JSONDecodeError:
            logging.error("[CLEAN] Dữ liệu truyền vào không phải JSON hợp lệ.")
            return None
        except Exception as e:
            logging.error(f"[CLEAN] Lỗi trong quá trình dọn dẹp: {e}")
            return None