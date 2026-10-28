import json
from raw.base.oop_base_raw import BaseRawOOP

class BtmcRawOOP(BaseRawOOP):
    def __init__(self):
        super().__init__(job_name='BTMC_RAW', store_id=1)

    def extract_payload(self, response_body):
        """
        Biến đổi chuỗi JSON. Nếu lỗi xảy ra, BaseRawOOP sẽ tự động bắt exception.
        """
        data_dict = json.loads(response_body)
        raw_payload_dict = data_dict.get('Data', {})
        
        if not raw_payload_dict:
            return None
            
        return json.dumps(raw_payload_dict, ensure_ascii=False)