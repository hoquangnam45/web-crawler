from enum import Enum

BASIC_FB_URL = "https://mbasic.facebook.com"
MOBILE_FB_URL = "https://m.facebook.com"
FB_URL = "https://www.facebook.com"
# USER_AGENT = "Mozilla/5.0 (Linux; U; Android 7.0; BQ-5522 Build/NRD90M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/61.0.3163.98 Mobile Safari/537.36 OPR/36.2.2254.130496" # Opera mobile
USER_DATA_DIR = "/home/ttl/Documents/SeleniumUserDataDir"
USER_PROFILE = "Default"

class CrawlType(Enum):
    FB_GROUP = 0
    FB_PAGE = 1
    
class VotingDecision(Enum):
    MAJORITY = 0
    YES_ONE = 1
    ALL = 2
    
class CrawlObjectType(Enum):
    COMMENT = 0,
    POST = 1,
    GROUP = 2,
    PAGE = 3 
