from __future__ import annotations
import csv
from datetime import datetime, timedelta
import os
from typing import Tuple
import typing
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import driver
import constants
from typing import Any
from typing import Type

class Post:
    def __init__(self, postId: str, pageId: str | None, groupId: str | None, content: str, images: list[str] | None, comments: list[Comment] | None, timestamp: datetime, userId: str):
        self.postId = postId
        self.pageId = pageId
        self.groupId = groupId
        self.content = content
        self.images = images
        self.comments = comments
        self.timestamp = timestamp
        self.userId = userId
    
    # def haveMoreText(element: WebElement) -> bool:
    # def haveImage(element: WebElement) -> bool:
    # def expandMoreText(element: WebElement):
    # def expandMoreImage(element: WebElement):
    # def linkToOtherPage(element: WebElement) -> list[str]:

class Comment:
    def __init__(self, commentId: str, content: str, images: list[str], replies: list[Comment], timestamp: datetime, userId: str):
        self.commentId = commentId
        self.content = content
        self.images = images
        self.replies = replies
        self.timestamp = timestamp
        self.userId = userId

# TODO: Get images,  get comments
def getComments(postIds: str) -> list[Comment] | None:
    try:
        return []
    except:
        return None

def getImagesOfPost(postIds: str) -> list[str] | None:
    try: 
        return []
    except:
        return None
    
def getPostsOfPage(pageId: str, cutOffCheck: typing.Callable[[int, Post], bool]) -> list[Post] | None:
    try:
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

        posts: list[Post] = []
        # Extract the post data
        postElements = find_elements_by_xpath(webDriver, "//div[@aria-posinset]")
        count = 0
        for postElement in postElements:
            ariaDescribedBy = get_attribute(postElement, "aria-describedby")
            ariaDescribedByTokens = ariaDescribedBy.split(" ")
            ariaLabeledBy = get_attribute(postElement, "aria-labelledby")
            
            postUserId = get_attribute(find_element_by_xpath(postElement, ".//*[contains(@id, '" + ariaLabeledBy + "')]//a"), "href")
            postStatusId = ariaDescribedBy[0]
            postContentId = ariaDescribedByTokens[1]
            postVisualId = ariaDescribedByTokens[2]
            postUrl = get_attribute(find_element_by_xpath(postElement, ".//*[contains(@id, '" + postStatusId + "')]//a"), "href")
            postBody = find_element_by_xpath(postElement, ".//ancestor::*[contains(@id, '" +  postContentId + "') or contains(@id, '" + postVisualId + "')][1]")
            try:
                postContent = find_element_by_xpath(postBody, ".//*[contains(@id, '" + postContentId + "')]")
            except:
                # This is probaly a translated piece of content
                postContent = find_element_by_xpath(postBody, ".//blockquote")
                
            try:
                # Expand read more
                find_element_by_xpath(postContent, ".//*[contains(@role, 'button')]").click()
            except:
                # Don't have read more
                pass
            
            comments = getComments(postUrl)
            images = getImagesOfPost(postVisualId)

            postTimestamp = datetime(1,1,1)
            post = Post(postUrl, pageId, None, postContent.text, images, comments, postTimestamp, postUserId)
            
            if cutOffCheck(count, post):
                break
            
            posts.append(post)
        return posts
    except Exception as e:
        print(e)
        return None

def parseTimestamp(timestamp: str) -> None:
    # Check if it has
    
    yesterday = "hôm qua"
    
    
def find_element_by_id(element: WebElement | WebDriver, id: str) -> WebElement:
    return element.find_element_by_id(id)

def find_elements_by_xpath(driver: WebElement | WebDriver, xpath: str) ->list[WebElement]:
    return driver.find_elements_by_xpath(xpath)

def find_element_by_xpath(element: WebElement | WebDriver, xpath: str) -> WebElement:
    return element.find_element_by_xpath(xpath)

def get_attribute(element: WebElement, attribute: str) -> str:
    return element.get_attribute(attribute)

def find_element_by_tag_name(element: WebElement | WebDriver, tagName: str) -> WebElement:
    return element.find_element_by_tag_name(tagName)

def outputPosts(posts: list[Post] | None, path: str, group: str, id: str):
    if posts is None:
        return
    with open(path + os.path.sep + id + ".csv", 'r') as f:
        writer = csv.writer(f)
        writer.writerow(["id", "userId", "pageId", "groupId", "content", "images", "timestamp"])
        
        for post in posts:
            writer.writerow([post.postId, post.userId, post.pageId, post.groupId, post.content, post.images, post.timestamp])
            outputComments(post.comments, path, id, "comments")
            
def outputComments(comments: list[Comment] | None, path: str, group: str, id: str):
    if comments is None:
        return
    with open(path + os.path.sep + id + ".csv", 'r') as f:
        writer = csv.writer(f)
        writer.writerow(["id", "userId", "pageId", "groupId", "content", "images", "timestamp"])
        
        # # Flatten comments
        # flattenedComments: list[Comment] = 
        
        # for comment in comments:
        #     writer.writerow([post.postId, post.userId, post.pageId, post.groupId, post.content, post.images, post.timestamp])
        #     outputComments(post.comments, path, id, "comments")
    
# NOTE: For testing-purposes only
def main():
    outputPosts(getPostsOfPage("OPFCVN", limitNumberOfPostsCrawl(1_000_000)), "crawled_data", "pages/OPFCVN", "posts")

def limitNumberOfPostsCrawl(upperLimit: int, upperTimeDelta: timedelta=timedelta(days=30)) -> typing.Callable[[int, Post], bool]:
    def fn(count: int, post: Post) -> bool:
        now = datetime.now()
        if count > upperLimit:
            return True
        duration = now - post.timestamp
        if duration > upperTimeDelta:
            return True
        return False
    return fn 
 
    
if __name__ == "__main__":
    main()
        