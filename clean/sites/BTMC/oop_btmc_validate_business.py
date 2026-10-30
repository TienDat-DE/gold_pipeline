from clean.base.oop_base_validate_business import BaseValidateBusinessOOP

class BtmcValidateBusinessOOP(BaseValidateBusinessOOP):
    def __init__(self):
        super().__init__(store_id=1, job_name='VALIDATE_BUSINESS')

    def get_pairs_to_check(self):
        # Trả về các field để kiểm duyệt theo cặp Mua - Bán
        return [
            ('sjcmua', 'sjcban'),
            ('btmcvangnhanmua', 'btmcvangnhanban')
        ]