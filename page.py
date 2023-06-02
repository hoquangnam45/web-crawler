from __future__ import annotations
from typing import Tuple
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import driver
import constants

class Page:
    def __init__(self, id: str, linkedPageIds: list[str], linkGroupIds: list[str]):
        self.id = id
        self.linkedPageIds = linkedPageIds
        self.linkedGroupIds = linkGroupIds
    
    # def haveMoreText(element: WebElement) -> bool:
    # def haveImage(element: WebElement) -> bool:
    # def expandMoreText(element: WebElement):
    # def expandMoreImage(element: WebElement):
    # def linkToOtherPage(element: WebElement) -> list[str]:
    
    @staticmethod
    def getLoginDialog() -> WebElement | None:
        try:
            webDriver = driver.getWebDriver()
            elements: list[WebElement] = webDriver.find_element_by_xpath('//div[@role="dialog"]//div[contains(@class,"x92rtbv x10l6tqk x1tk7jg1 x1vjfegm")]').click()
            if len(elements) > 0:
                return elements[0]
            return None
        except:
            return None
        
    @staticmethod
    def getPage(pageId: str) -> Page | None:
        try:
            webDriver = driver.getWebDriver()
            webDriver.get(constants.FB_URL + "/" + pageId)
            # webDriver.find_element_by_xpath('//div[@role="dialog"]//div[contains(@class,"x92rtbv x10l6tqk x1tk7jg1 x1vjfegm")]').click()

            # Scroll through the page to load posts
            lastHeight = webDriver.execute_script("return document.body.scrollHeight")
            while True:
                loginDialog = Page.getLoginDialog()
                if loginDialog is not None:
                    loginDialog.click()
                webDriver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                WebDriverWait(webDriver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "div")))
                newHeight = webDriver.execute_script("return document.body.scrollHeight")
                if newHeight == lastHeight:
                    break
                lastHeight = newHeight

            # Extract the post data
            postElements: list[WebElement] =  webDriver.find_element_by_xpath("//div[contains(@class, 'x1yztbdb x1n2onr6 xh8yej3 x1ja2u2z')]")
            postData = [postElement.text for postElement in postElements]
            id: str = ""
            linkedPageIds: list[str] = []
            linkedGroupIds: list[str] = []
            page = Page(id, linkedPageIds, linkedGroupIds)
            return page
        except Exception as e:
            print(e)
            return None
        
# NOTE: For testing-purposes only
def main():
    page = Page.getPage("fifaworldcup")

if __name__ == "__main__":
    main()
        