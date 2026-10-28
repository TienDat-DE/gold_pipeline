from crawlers.base.oop_base_crawler import BaseCrawlerOOP

class BtmcCrawlerOOP(BaseCrawlerOOP):
    def __init__(self):
        super().__init__(
            job_name='BTMC_CRAWLER', 
            store_id=1, 
            store_name='BTMC',
            api_url='https://btmc.vn/ProductHome/getGoldDate'
        )
        # Khôi phục bộ Headers chống WAF gốc của bạn
        self.headers = {
            'Accept': '*/*', 'Accept-Language': 'vi', 'Connection': 'keep-alive',
            'Referer': 'https://btmc.vn/gia-vang-theo-ngay.html', 
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36'
        }

    def build_request_params(self):
        params = {'date': self.formatted_date}
        actual_url = f"{self.api_url}?date={self.formatted_date.replace('/', '%2F')}"
        return params, actual_url