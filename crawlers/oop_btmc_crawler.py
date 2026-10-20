from crawlers.oop_base_crawler import BaseCrawlerOOP

class BtmcCrawlerOOP(BaseCrawlerOOP):
    def __init__(self):
        # Truyền 3 tham số gốc lên cho Class Cha quản lý
        super().__init__(
            job_name='BTMC_CRAWLER_OOP', 
            store_id=1, 
            api_url='https://btmc.vn/ProductHome/getGoldDate'
        )

    def build_request_params(self):
        # Đóng gói tham số riêng của BTMC
        params = {'date': self.formatted_date}
        
        # Tạo chuỗi URL lưu vết để insert vào cột source_url trong Database
        actual_url = f"{self.api_url}?date={self.formatted_date.replace('/', '%2F')}"
        
        return params, actual_url

if __name__ == "__main__":
    bot = BtmcCrawlerOOP()
    bot.run()