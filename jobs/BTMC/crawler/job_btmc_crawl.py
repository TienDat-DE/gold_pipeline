import logging
from crawlers.sites.BTMC.oop_btmc_crawler import BtmcCrawlerOOP

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class JobBtmcCrawler:
    def __init__(self):
        # Nạp cỗ máy cào dữ liệu của BTMC từ tầng Công cụ
        self.crawler = BtmcCrawlerOOP()

    def run_job(self):
        logging.info("========== BẮT ĐẦU TIẾN TRÌNH CRAWL DATA BTMC ==========")
        
        # Hàm run() của BaseCrawlerOOP đã bao gồm sẵn các bước:
        # Lấy param -> Gửi Request -> Insert pipeline_log -> Insert web_responses
        self.crawler.run()
        
        logging.info("========== HOÀN TẤT TIẾN TRÌNH CRAWL DATA BTMC ==========")

if __name__ == "__main__":
    job = JobBtmcCrawler()
    job.run_job()