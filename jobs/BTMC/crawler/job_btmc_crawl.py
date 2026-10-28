import logging
from crawlers.sites.BTMC.oop_btmc_crawler import BtmcCrawlerOOP

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class JobBtmcCrawler:
    def __init__(self):
        self.crawler = BtmcCrawlerOOP()

    def run_job(self):
        logging.info("========== BẮT ĐẦU TIẾN TRÌNH CRAWL DATA BTMC ==========")
        # crawler.run() tự động xử lý toàn bộ logic và trả về sys.exit()
        self.crawler.run()

if __name__ == "__main__":
    job = JobBtmcCrawler()
    job.run_job()