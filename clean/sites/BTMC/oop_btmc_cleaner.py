# CHÚ Ý ĐƯỜNG DẪN IMPORT MỚI
from clean.base.oop_base_cleaner import BaseCleanerOOP

class BtmcCleanerOOP(BaseCleanerOOP):
    def extract_and_map(self, raw_json):
        cleaned_data = {
            'btmcvangnhanmua':  self.clean_html_tags(raw_json.get('btmcvangnhanmua')),
            'btmcvangnhanban':  self.clean_html_tags(raw_json.get('btmcvangnhanban')),
            'sjcmua':           self.clean_html_tags(raw_json.get('sjcmua')),
            'sjcban':           self.clean_html_tags(raw_json.get('sjcban'))
        }
        return cleaned_data