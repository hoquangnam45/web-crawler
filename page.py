from __future__ import annotations
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
    
    @staticmethod
    def getPage(pageId: str) -> None:
        webDriver = driver.getWebDriver()
        webDriver.get(constants.FB_URL + "/" + pageId)
        # Scroll through the page to load posts
        lastHeight = webDriver.execute_script("return document.body.scrollHeight")
        while True:
            webDriver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            WebDriverWait(webDriver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "div")))
            newHeight = webDriver.execute_script("return document.body.scrollHeight")
            if newHeight == lastHeight:
                break
            lastHeight = newHeight

         # Extract the post data
        postElements = webDriver.find_elements_by_xpath("//div[contains(@class, 'userContentWrapper')]")
        postData = [postElement.text for postElement in postElements]
        
# NOTE: For testing-purposes only
def main():
    page = Page.getPage("fifaworldcup")

if __name__ == "__main__":
    main()
        