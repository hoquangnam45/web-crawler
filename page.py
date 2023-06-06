from __future__ import annotations
from datetime import datetime
from typing import Tuple
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import driver
import constants

class Post:
    def __init__(self, postId: str, pageId: str | None, groupId: str | None, content: str, images: list[str], commentIds: list[str], timestamp: datetime, userId: str):
        self.postId = postId
        self.pageId = pageId
        self.groupId = groupId
        self.content = content
        self.images = images
        self.commentIds = commentIds
        self.timestamp = timestamp
        self.userId = userId
    
    # def haveMoreText(element: WebElement) -> bool:
    # def haveImage(element: WebElement) -> bool:
    # def expandMoreText(element: WebElement):
    # def expandMoreImage(element: WebElement):
    # def linkToOtherPage(element: WebElement) -> list[str]:
        
    @staticmethod
    def getPage(pageId: str, limit: int=50) -> list[Post] | None:
        try:
            webDriver = driver.getWebDriver()
            webDriver.get(constants.FB_URL + "/" + pageId)
            # webDriver.find_element_by_xpath('//div[@role="dialog"]//div[contains(@class,"x92rtbv x10l6tqk x1tk7jg1 x1vjfegm")]').click()

            # Scroll through the page to load posts
            lastHeight = webDriver.execute_script("return document.body.scrollHeight")
            while True:
                webDriver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                WebDriverWait(webDriver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "div")))
                newHeight = webDriver.execute_script("return document.body.scrollHeight")
                if newHeight == lastHeight:
                    break
                lastHeight = newHeight

            posts: list[Post] = []
            # Extract the post data
            postElements = Post.find_elements_by_xpath(webDriver, "//div[@aria-posinset]")
            for postElement in postElements:
                ariaDescribedBy = Post.get_attribute(postElement, "aria-describedby")
                ariaDescribedByTokens = ariaDescribedBy.split(" ")
                postStatusId = ariaDescribedBy[0]
                postContentId = ariaDescribedByTokens[1]
                postVisualId = ariaDescribedByTokens[2]
                postUrl = Post.get_attribute(Post.find_element_by_tag_name(Post.find_element_by_id(postElement, postStatusId), "a"), "href")
                postContent = Post.find_element_by_xpath(postElement, "//div[contains(@id, '" + postContentId + "')]")
                postTimestamp: timestamp
                post = Post(postUrl, pageId, None, [], [], )
                posts.append(post)
                # try:
                    # Expand read morePage
                
                # try:
                #     postImage = Page.get_attribute(Page.find_element_by_id(postElement, ariaDescribedByTokens[2]))
                # except:
                #     # noop
                #     # Don't have image
                
            
            postData = [postElement.text for postElement in postElements]
            id: str = ""
            linkedPageIds: list[str] = []
            linkedGroupIds: list[str] = []
            page = Page(id, linkedPageIds, linkedGroupIds)
            return page
        except Exception as e:
            print(e)
            return None
    
    @staticmethod
    def find_element_by_id(element: WebElement, id: str) -> WebElement:
        return element.find_element_by_id(id)

    @staticmethod
    def find_elements_by_xpath(driver: WebDriver, xpath: str) ->list[WebElement]:
        return driver.find_elements_by_xpath(xpath)

    @staticmethod
    def find_element_by_xpath(element: WebElement, xpath: str) -> WebElement:
        return element.find_element_by_xpath(xpath)
    
    @staticmethod
    def get_attribute(element: WebElement, attribute: str) -> str:
        return element.get_attribute(attribute)
    
    @staticmethod
    def find_element_by_tag_name(element: WebElement, tagName: str) -> WebElement:
        return element.find_element_by_tag_name(tagName)
        
# NOTE: For testing-purposes only
def main():
    page = Page.getPage("fifaworldcup")

if __name__ == "__main__":
    main()
        