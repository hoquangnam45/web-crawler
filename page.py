from __future__ import annotations
import argparse
import csv
from datetime import datetime, timedelta
import json
import os
import time
import traceback
from typing import Tuple, Union
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
from typing import Tuple
from urllib.parse import parse_qs, urlparse
from typing import TypeVar, Generic
from selenium.webdriver.common.action_chains import ActionChains
import logging
from selenium.common.exceptions import InvalidSessionIdException
from selenium.common.exceptions import TimeoutException


T = TypeVar('T')  # Declare a type variable
K = TypeVar('K')

def get_path_by_index(url: str, index: int) -> str | None:
    parsed_url = urlparse(url)
    path_segments = parsed_url.path.split('/')
    if len(path_segments) > index:
        return path_segments[index]
    else:
        return None

def get_parameters(url: str, parameter: str) -> list[str] | None:
    parsed_url = urlparse(url)

    # Get the query parameters as a dictionary
    query_params = parse_qs(parsed_url.query)

    # Access specific query parameter values
    return query_params.get(parameter)

class Optional(Generic[T]):
    def __init__(self, val: T | None):
        self.val = val
        
    @staticmethod
    def of(val: T) -> Optional[T]:
        if val is None:
            raise ValueError("value is None")
        return Optional(val)

    @staticmethod
    def ofNullable(val: T | None) -> Optional[T]:
        return Optional(val)
    
    @staticmethod
    def empty() -> Optional[T]:
        return Optional(None)
    
    def flatMap(self, fn: typing.Callable[[T], Optional[K]]) -> Optional[K]:
        if self.val is None:
            return Optional(None)
        return fn(self.val)
        
    def map(self, fn: typing.Callable[[T], Union[Union[K, None], K]]) -> Optional[K]:
        if self.val is None:
            return Optional(None)
        return Optional(fn(self.val))
    
    def peek(self, fn: typing.Callable[[T], Any]) -> Optional[T]:
        self.ifPresent(fn)
        return self
    
    def get(self) -> T | None:
        return self.val
    
    def orElse(self, defaultValue: T) -> T:
        if self.val is not None:
            return self.val
        return defaultValue
    
    def orError(self) -> T:
        if self.val is None:
            raise ValueError("value is None")
        return self.val
    
    def isPresent(self) -> bool:
        return self.val is not None
    
    def isEmpty(self) -> bool:
        return self.val is None
    
    def ifPresent(self, fn: typing.Callable[[T], Any]):
        self.map(fn)
    
    def filter(self, fn: typing.Callable[[T], bool]) -> Optional[T]:
        if self.val is None or fn(self.val) is False:
            return Optional(None)
        return Optional(self.val)
        
class Post: 
    def __init__(self, postId: str, pageId: str | None, groupId: str | None, content: str | None, images: list[Image] | None, comments: list[Comment] | None, timestamp: datetime, userId: str, url: str):
        self.postId = postId
        self.pageId = pageId
        self.groupId = groupId
        self.content = content
        self.images = images
        self.comments = comments
        self.timestamp = timestamp
        self.userId = userId
        self.url = url

class Comment:
    def __init__(self, commentId: str, content: str, images: list[str], replies: list[Comment] | None, replyTo: str | None, timestamp: datetime | None, userId: str, url: str, postId: str | None):
        self.commentId = commentId
        self.content = content
        self.images = images
        self.timestamp = timestamp
        self.userId = userId
        self.timestamp = timestamp
        self.replyTo = replyTo
        self.url = url
        self.postId = postId
        self.replies = replies
    
class Image:
    def __init__(self, imageId: str, url: str, sourceUrl: str):
        self.imageId = imageId
        self.url = url
        self.sourceUrl = sourceUrl

def getComment(postId: str, replyTo: str | None, commentElement: WebElement) -> Comment:
    commentUrl = get_attribute(find_element_by_xpath(commentElement, ".//a[contains(@href, '/comment/replies')]"), 'href')
    commentUser = get_path_by_index(get_attribute(find_element_by_xpath(commentElement, ".//h3//a"), "href"), 1)
    assert(commentUser is not None)
    assert(commentUrl is not None)
    commentId = get_attribute(commentElement, "id")
    commentContent = find_element_by_xpath(commentElement, ".//h3/../*[2]").text
    
    return Comment(commentId, commentContent, [], [], replyTo, None, commentUser, commentUrl, postId)

# def getComments(commentElements: list[WebElement]) -> list[Comment] | None:
#     comments: list[Comment] = []
#     for commentElement in commentElements:
#         comment = getComment(commentElement) 
#         if comment is not None:
#             comments.append(comment)
#         else:
#             return None
#     return comments
    
# def getCommentsOfUrl(url: str) -> list[Comment] | None:
#     webDriver = driver.getWebDriver()
#     webDriver.get(url)
    
#     commentCount = 0
#     while True:
#         commentElements = Optional.ofNullable(find_elements_by_xpath(webDriver, "//div[@data-sigil='comment']")).orElse([])
#         currentCommentCount = len(commentElements)
#         if currentCommentCount > commentCount:
#             commentCount = currentCommentCount
#         else:
#             # No more change after clicking load more comment
#             break

#         # Try clicking load more comment
#         Optional.ofNullable(find_element_by_xpath(webDriver, "//div[contains(@class, 'async_elem')]//a")).ifPresent(lambda x: x.click())
#         # Wait a little for ajax to finish loading the comments
#         WebDriverWait(webDriver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "div")))

#     if commentCount > 0:
#         return getComments(commentElements)
#     return []

def getImage(imageElement: WebElement) -> Image | None:
    imageUrl = Optional.ofNullable(find_element_by_xpath(imageElement, ".//a"))\
        .map(lambda x: get_attribute(x, "href"))\
        .orError()
    imageId = Optional.ofNullable(imageUrl)\
        .map(lambda x: get_parameters(x, "id"))\
        .map(lambda x: x[0])\
        .orError()
    imageSrc = Optional.ofNullable(find_element_by_xpath(imageElement, ".//i[@role = 'img']"))\
        .map(lambda x: value_of_css_property(x, "background-image"))\
        .map(lambda x: x.replace('url("', '').replace('")', ''))\
        .orError()
    return Image(imageId, imageUrl, imageSrc)
        
def getImagesOfUrl(url: str) -> list[Image] | None:
    webDriver = driver.getWebDriver()
    webDriver.get(url)
    
    imageElements = Optional.ofNullable(find_element_by_xpath(webDriver, ".//div[@data-ft = '{\"tn\":\"H\"}']"))\
        .map(lambda el: find_elements_by_xpath(el, ".//div[@data-gt = '{\"tn\":\"E\"}']"))\
        .filter(lambda x: len(x) > 0)\
        .get()
    if imageElements is None:
        return None
    ret: list[Image] = []
    for el in imageElements:
        img = getImage(el)
        if img is None:
            return None
        ret.append(img)
    return ret
    
def createPost(postElement: WebElement) ->  Post | None:
    postStoryContainer = Optional.ofNullable(find_element_by_xpath(postElement, ".//div[contains(@class, 'story_body_container')]")).orError()
    postHeaderElement = Optional.ofNullable(find_element_by_xpath(postStoryContainer, ".//header")).orError()
    postBodyElement = Optional.ofNullable(find_element_by_xpath(postStoryContainer, ".//div[contains(@data-gt, '{\"tn\":\"*s\"}')]")).orError()
    
    postUser = Optional.ofNullable(find_element_by_xpath(postHeaderElement, ".//h3//a"))\
        .map(lambda it: get_attribute(it, "href"))\
        .map(lambda it: get_path_by_index(it, 1))\
        .orError()
    postUrl = Optional.ofNullable(find_element_by_xpath(postHeaderElement, ".//div[contains(@data-sigil, 'm-feed-voice-subtitle')]//a"))\
        .map(lambda it: get_attribute(it, "href"))\
        .orError()
    postTimestamp = Optional.ofNullable(find_element_by_xpath(postHeaderElement, ".//div[contains(@data-sigil, 'm-feed-voice-subtitle')]//a"))\
        .map(lambda it: it.text)\
        .map(parseTimestamp)\
        .orError()
    postId = Optional.of(postUrl)\
        .map(lambda it: get_parameters(it, "id"))\
        .map(lambda it: it[0])\
        .orError()
    # NOTE: Post content element could be empty
    postContentElement = Optional.ofNullable(find_element_by_xpath(postBodyElement, ".//div//span")).get()
    Optional.ofNullable(postContentElement).map(lambda x: find_element_by_xpath(x, ".//span[@data-sigil='more']//a")).ifPresent(lambda x: x.click())
    postContent = Optional.ofNullable(postContentElement).map(lambda x: x.text).orElse("")
    
    return Post(postId, None, None, postContent, None, None, postTimestamp, postUser, postUrl)
    
def createPostsWithUrls(postEntriesPath: str) -> list[Post] | None:
    with open(postEntriesPath, "r") as f:
        csvReader = csv.reader(f)
        webDriver = driver.getWebDriver()
        for row in csvReader:
            postId = row[0]
            pageId = row[1]
            postTimestamp = datetime.strptime(row[2], '%Y-%m-%d %H:%M:%S')
            userId = row[3]
            postUrl = row[4]
            post = Post(postId, pageId, None, None, None, None, postTimestamp, userId, postUrl)
            webDriver.get(postUrl)
            
            postElement = find_element_by_xpath(webDriver, "//*[@role = 'main']")
            post.content = find_element_by_xpath(postElement, ".//*[@data-ft = '{\"tn\":\"*s\"}']/*[1]").text
            # post.images = [get_attribute(el, "src") for el in find_elements_by_xpath(postElement, ".//*[@data-ft = '{\"tn\":\"H\"}']//img")]
            post.comments = []
            
            comments = [getComment(postId, None, el) for el in find_elements_by_xpath(postElement, ".//*[@id = 'm_story_permalink_view']/*[2]/*[1]/*[5 and not(@id)]/*[not(contains(@id, 'see_next'))]")]
            while len(comments) > 0:
                # merge comments list
                post.comments = post.comments + comments
                
                # Load more comments
                nextCommentUrl = get_attribute(find_element_by_xpath(postElement, ".//*[@id = 'm_story_permalink_view']/*[2]/*[1]/*[5 and not(@id)]/*[contains(@id, 'see_next')]//a"), "href")
                webDriver.get(nextCommentUrl)
            
            # post = Post(postId, pageId, None, postContent)
            # images = Optional.ofNullable(getImagesOfUrl(postUrl)).orElse([])
            # postUrl.images = images
            # comments = Optional.ofNullable(getCommentsOfUrl(postUrl)).orError()
            # for comment in comments:
            #     comment.postId = postId
            # postUrl.comments = comments

    # return posts
    pass

def getPostsOfPage(pageId: str, cutOffCheck: typing.Callable[[int, Union[datetime, None]], bool], batchSize: int = 500, cursorUrlPath: str = "postCursor.txt", postEntriesPath: str = "postEntries.txt") -> list[Post] | None:
    webDriver = driver.getWebDriver()
    defaultUrl = constants.BASIC_FB_URL + "/" + pageId + "?v=timeline"
    try:
        with open(cursorUrlPath, 'r') as f:
            cursorUrl = f.readline()
            if len(cursorUrl.strip()) > 0:
                webDriver.get(cursorUrl)
            else:
                webDriver.get(defaultUrl)
    except:        
        webDriver.get(defaultUrl)

    batch: list[Post] = []
    batchIndex = -1
    crawlCount = 0
    currentBatch = -1
    
    while True:
        cutOff: bool = False
        postElements = find_elements_by_xpath(webDriver, "//*[@id = 'structured_composer_async_container']//*[@role = 'article' and @data-ft]")
        
        for postElement in postElements:
            try: 
                dataFt = get_attribute(postElement, "data-ft")
                metadata = json.loads(dataFt)
                pageInsight = metadata["page_insights"]
                userId = metadata["content_owner_id_new"]
                postMetadata = pageInsight[userId]
                postTimestamp = datetime.fromtimestamp(postMetadata["post_context"]["publish_time"])
                postUrl = getPostUrl(postElement)
                cursorUrl = str(webDriver.current_url)
                postId = postMetadata["targets"][0]["post_id"]
                pageId = postMetadata["targets"][0]["page_id"]
                cutOff = cutOffCheck(crawlCount, postTimestamp)
                # Perform some cut off check to see whether we should scroll down more
                if cutOff:
                    break
                else:
                    post = Post(postId, pageId, None, None, None, None, postTimestamp, userId, postUrl)
                    batch.append(post)
                    crawlCount += 1
                    logging.info("collect " + str(crawlCount) + " post entries")
            except Exception as e:
                logging.error(e)
        
        with open(cursorUrlPath, 'w') as cursorF:
            # NOTE: Go to next page, and save the cursor in case the need to resume later
            cursorF.write(webDriver.current_url)
        
        currentBatch = int(crawlCount / batchSize)
        if currentBatch > batchIndex:
            if batchIndex >= 0:
                with open(postEntriesPath, 'a') as f:
                    csvWriter = csv.writer(f)
                    csvWriter.writerows([(el.postId, el.pageId, el.timestamp, el.userId, el.url, webDriver.current_url) for el in batch[:batchSize]])
                    batch = batch[batchSize:]
            batchIndex = currentBatch
                    
        
        if cutOff is True:
            break
        else:
            nextPageUrl = get_attribute(find_element_by_xpath(webDriver, "//*[@id = 'structured_composer_async_container']/*[2]//a"), "href")
            webDriver.get(nextPageUrl)
            with open(cursorUrlPath, 'w') as cursorF:
                cursorF.write(nextPageUrl)
 
    with open(postEntriesPath, 'a') as f:
        csvWriter = csv.writer(f)
        csvWriter.writerows([(el.postId, el.pageId, el.timestamp, el.userId, el.url, webDriver.current_url) for el in batch[:batchSize]])
        batch.clear()
    return createPostsWithUrls(postEntriesPath)

def getPostTimestamp(postElement: WebElement, timeout: int = 10) -> datetime | None:
    webDriver = driver.getWebDriver()
    try:
        return Optional.ofNullable(get_attribute(postElement, "aria-describedby"))\
            .map(lambda x: x.split(" "))\
            .peek(lambda x: logging.info("post id: " + x[0]))\
            .map(lambda x: find_element_by_xpath(postElement, ".//*[@id = '" + x[0] + "']"))\
            .peek(lambda _: webDriver.execute_script("arguments[0].scrollIntoView({behavior: 'auto',block: 'center',inline: 'center'});", postElement))\
            .peek(lambda _: WebDriverWait(webDriver, timeout).until(EC.visibility_of(postElement)))\
            .peek(lambda x: webDriver.execute_script("arguments[0].scrollIntoView({behavior: 'auto',block: 'center',inline: 'center'});", x))\
            .peek(lambda x: WebDriverWait(webDriver, timeout).until(EC.visibility_of_element_located((By.ID, get_attribute(x, "id")))))\
            .peek(lambda x: ActionChains(webDriver).move_to_element(x).perform())\
            .peek(lambda x: WebDriverWait(webDriver, timeout).until(lambda _: Optional.ofNullable(find_element_by_xpath(x, ".//*[@aria-describedby]")).isPresent()))\
            .map(lambda x: find_element_by_xpath(x, ".//*[@aria-describedby]"))\
            .map(lambda x: get_attribute(x, "aria-describedby"))\
            .peek(lambda x: logging.info("aria-describedby: " + x))\
            .peek(lambda x: WebDriverWait(webDriver, timeout).until(lambda innerWebDriver: Optional.ofNullable(find_element_by_xpath(innerWebDriver, "//*[@id = '" + x + "']")).isPresent()))\
            .map(lambda x: find_element_by_xpath(webDriver, "//*[@id = '" + x + "']").text)\
            .peek(lambda x: logging.info("text: " + x))\
            .map(parseTimestamp)\
            .get()
    finally:
        ActionChains(webDriver).move_by_offset(50, 50).perform()

def lenN(xs: list | None) -> int:
    if xs is None:
        return 0
    return len(xs)

def getPostUrl(postElement: WebElement) -> str:
    return Optional.ofNullable(find_element_by_xpath(postElement, ".//*[@data-ft = '{\"tn\":\"*W\"}']/*[2]/a[3]"))\
        .map(lambda x: get_attribute(x, "href"))\
        .orError()
        
def parseTimestamp(timestamp: str) -> datetime:
    timestampTokens = timestamp.split(', ')
    if len(timestampTokens) == 3: # It will be in the form: Weekday, %d tháng %m, %Y lúc %H:%M 
        timestamp =  ", ".join(timestamp.split(', ')[1:len(timestamp) - 1]) # Remove weekday
    # Check if it has following formats
    formats = ["%d tháng %m lúc %H:%M", "%d tháng %m, %Y lúc %H:%M"]
    for format in formats:
        try:
            return datetime.strptime(timestamp, format)
        except:
            continue
    
    # When post creation is less than 24 hour it will be in the format hour ago or minutes ago
    if timestamp.endswith("trước"):
        timestamp = timestamp[:len(timestamp)-len("trước")]
    if timestamp.endswith("giờ"):
        return datetime.now() - timedelta(hours=int(timestamp.split(" ")[0]))
    if timestamp.endswith("phút"):
        return datetime.now() - timedelta(minutes=int(timestamp.split(" ")[0]))
    if timestamp == "Vừa xong":
        return datetime.now()
    raise ValueError("Recheck if facebook change their timestamp display formatting, this should not happened, here is the value it trying to parse: " + timestamp)    


def exceptionHandler(f: typing.Callable[[], T], maxRetries: int = 10, shouldLog: bool = True, delayInSec: int = 0, reraise: bool = False) -> T | None:
    e: Exception | None = None
    for i in range(maxRetries):
        try:
            if i > 0:
                logging.info("Retrying: " + str(i))
            return f()
        except InvalidSessionIdException as innerE:
            if shouldLog:
                logging.error(innerE) # TODO: Refresh session id
                logging.error(traceback.format_exc())
            e = innerE
            pass
        except Exception as innerE:
            if shouldLog:
                logging.error(innerE) # TODO: Refresh session id
                logging.error(traceback.format_exc())
            e = innerE
            pass
        finally:
            if delayInSec > 0:
                time.sleep(delayInSec)
    if reraise:
        if e is not None:
            raise(e)
    
def find_element_by_id(element: WebElement | WebDriver, id: str) -> WebElement:
    return element.find_element_by_id(id)
    
def find_elements_by_xpath(driver: WebElement | WebDriver, xpath: str) -> list[WebElement]:
    return driver.find_elements_by_xpath(xpath)

def find_element_by_xpath(element: WebElement | WebDriver, xpath: str) -> WebElement:
    return element.find_element_by_xpath(xpath)
    
def get_attribute(element: WebElement, attribute: str) -> str:
    return element.get_attribute(attribute)
    
def find_element_by_tag_name(element: WebElement | WebDriver, tagName: str) -> WebElement | None:
    return element.find_element_by_tag_name(tagName)

def value_of_css_property(element: WebElement, property: str) -> str | None:
    return element.value_of_css_property(property)
    
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
    # getPostsOfPage("etribune", limitNumberOfPostsCrawl(1_000_000))
    createPostsWithUrls("postEntries.txt")
    # outputPosts(getPostsOfPage("etribune", limitNumberOfPostsCrawl(1_000_000)), "crawled_data", "pages/etribune", "posts")

def limitNumberOfPostsCrawl(upperLimit: int, upperTimeDelta: timedelta=timedelta(days=30)) -> typing.Callable[[int, Union[datetime, None]], bool]:
    def fn(count: int, postTimestamp: datetime | None) -> bool:
        now = datetime.now()
        if count > upperLimit:
            return True
        if postTimestamp is not None:
            duration = now - postTimestamp
            if duration > upperTimeDelta:
                return True
        return False
    return fn 
 
    
if __name__ == "__main__":
    # Create the argument parser
    parser = argparse.ArgumentParser(description='Crawl fb page')

    # Add arguments
    parser.add_argument('--log', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        default='info', help='Set the log level')

    # Parse the arguments
    args = parser.parse_args()

    # Access the parsed arguments
    loglevel = args.log

    # Use the parsed arguments
    print('Log level:', loglevel)
    
    numericLevel = getattr(logging, loglevel.upper(), None)
    if not isinstance(numericLevel, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    logging.basicConfig(level=numericLevel)
    main()