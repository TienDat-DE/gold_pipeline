import json
import logging
from raw.base.oop_base_raw import BaseRawOOP

class BtmcRawOOP(BaseRawOOP):
    def __init__(self):
        super().__init__(job_name='BTMC_RAW_OOP', store_id=1)

    def extract_payload(self, response_body):
        """
        Ghi đè hàm của BaseRawOOP. 
        Biến đổi chuỗi JSON từ web_responses thành raw_payload tinh gọn.
        """
        try: 
            data_dict = json.loads(response_body)
            # Lấy toàn bộ dữ liệu nằm trong key 'Data'
            raw_payload_dict = data_dict.get('Data', {})
            
            if not raw_payload_dict:
                logging.warning("Không tìm thấy key 'Data' trong JSON trả về.")
                return None
                
            # Đóng gói lại thành chuỗi string để ném vào Database
            raw_payload_string = json.dumps(raw_payload_dict, ensure_ascii=False)
            return raw_payload_string
        
        except json.JSONDecodeError:
            logging.error('Lỗi: Dữ liệu HTML/JSON trả về không hợp lệ để bóc tách.')
            return None
        except Exception as e:
            logging.error(f"Lỗi khi trích xuất raw_payload: {e}")
            return None