from crawlers.oop_base_crawler import BaseCrawlerOOP

class BtmcCrawlerOOP(BaseCrawlerOOP):
    def __init__(self):
        super().__init__(
            job_name='BTMC_CRAWLER_OOP',
            store_id=1,
            api_url='https://btmc.vn/ProductHome/getGoldDate'
            )
    
    def build_request_params(self):
        params = {'date': self.formatted_date}
        actual_url = f"{self.api_url}?date={self.formatted_date.replace('/', '%2F')}"
        return params, actual_url
    
if __name__ == "__main__":
    bot = BtmcCrawlerOOP()
    bot.run()    