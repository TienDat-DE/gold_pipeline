# CHÚ Ý ĐƯỜNG DẪN IMPORT MỚI
from clean.base.oop_base_validate_basic import BaseValidateBasicOOP

class BtmcValidateBasicOOP(BaseValidateBasicOOP):
    def get_required_keys(self):
        return ['sjcmua', 'sjcban', 'btmcvangnhanmua', 'btmcvangnhanban']