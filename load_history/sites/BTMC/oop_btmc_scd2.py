from load_history.base.oop_base_scd2 import BaseSCD2LoaderOOP

class BtmcSCD2LoaderOOP(BaseSCD2LoaderOOP):
    def __init__(self):
        super().__init__(store_id=1)