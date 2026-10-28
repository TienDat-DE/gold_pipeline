from load_history.base.oop_base_scd2 import BaseScd2LoaderOOP

class BtmcSCD2LoaderOOP(BaseScd2LoaderOOP): # CHÚ Ý: Viết hoa chữ SCD2 để khớp với file Hash
    def __init__(self):
        super().__init__(store_id=1)