from clean.validate_basic.base.oop_base_validate_basic import BaseValidateBasicOOP

class BtmcValidateBasicOOP(BaseValidateBasicOOP):
    def __init__(self):
        super().__init__(store_id=1, job_name='VALIDATE_BASIC')

    def get_required_keys(self):
        # Trả về chính xác các key dùng để kiểm tra như code gốc
        return ['sjcmua', 'sjcban', 'btmcvangnhanmua', 'btmcvangnhanban']