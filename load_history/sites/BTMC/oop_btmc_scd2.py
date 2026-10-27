from load_history.base.oop_base_scd2 import BaseScd2LoaderOOP

class BtmcScd2LoaderOOP(BaseScd2LoaderOOP):
    def __init__(self):
        # Truyền ID cố định của BTMC (VD: store_id = 1) lên Lớp Cha
        super().__init__(store_id=1)