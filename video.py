from optional import Optional
import utils
import constants
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import driver

class Video:
    # NOTE: url is the link to the downloadable video file, whereare sourceUrl is the link to the video page, which could be used
    # to crawl for more data like comment inside the video page
    def __init__(self, parentId: str, id: str, url: str, sourceUrl: str):
        self.id = id
        self.url = url
        self.sourceUrl = sourceUrl
        self.parentId = parentId

def getVideo(postId: str, crawlType: constants.CrawlType, imageElement: WebElement, driver: driver.WebDriver) -> Video:
    videoUrl = Optional.ofNullable(utils.find_element_by_xpath(imageElement, ".//a"))\
        .map(lambda x: utils.get_attribute(x, "href"))\
        .orError()
    videoId = Optional.ofNullable(videoUrl)\
        .map(lambda x: utils.get_parameters(x, "id"))\
        .map(lambda x: x[0])\
        .orError()
    videoSrc = Optional.ofNullable(utils.find_element_by_xpath(imageElement, ".//i[@role = 'img']"))\
        .map(lambda x: utils.value_of_css_property(x, "background-image"))\
        .map(lambda x: x.replace('url("', '').replace('")', ''))\
        .orError()
    return Video(videoId, postId, videoUrl, videoSrc)