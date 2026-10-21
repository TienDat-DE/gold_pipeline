import json
import logging

class BtmcRawParserOOP:
    
    @staticmethod
    def extract_raw_payload(response_body):
        try: 
            data_dict = json.loads(response_body)
            raw_payload_dict = data_dict.get('Data',{})
            
            raw_payload_string = json.dumps(raw_payload_dict, ensure_ascii=False)
                        
            return raw_payload_string
        
        except json.JSONDecodeError:
            logging.error('Lỗi: Dữ liệu không phải JSON hợp lệ.')
            return None
        except Exception as e:
            logging.error(f"Lỗi khi trích xuất raw_payload: {e}")
            return None