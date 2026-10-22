# CHÚ Ý ĐƯỜNG DẪN IMPORT MỚI
from clean.base.oop_base_validate_business import BaseValidateBusinessOOP

class BtmcValidateBusinessOOP(BaseValidateBusinessOOP):
    def get_pairs_to_check(self):
        return [
            ('sjcmua', 'sjcban'),
            ('btmcvangnhanmua', 'btmcvangnhanban')
        ]