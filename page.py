from __future__ import annotations
import csv
from datetime import datetime, timedelta
import os
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
from urllib.parse import parse_qs, urlparse
from typing import TypeVar, Generic

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
    
    def peek(self, fn: typing.Callable[[T], None]) -> Optional[T]:
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
    
    def ifPresent(self, fn: typing.Callable[[T], None]):
        self.map(fn)
    
    def filter(self, fn: typing.Callable[[T], bool]) -> Optional[T]:
        if self.val is None or fn(self.val) is False:
            return Optional(None)
        return Optional(self.val)
        
class Post: 
    def __init__(self, postId: str, pageId: str | None, groupId: str | None, content: str, images: list[Image] | None, comments: list[Comment] | None, timestamp: datetime, userId: str, url: str):
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
    def __init__(self, commentId: str, content: str, images: list[str], replies: list[Comment] | None, replyTo: str | None, timestamp: datetime, userId: str, url: str, postId: str | None):
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

def getComment(commentElement: WebElement) -> Comment | None:
    commentUrl = Optional.ofNullable(find_element_by_xpath(commentElement, ".//div[contains(@data-sigil, 'feed_story_ring')]//a"))\
        .map(lambda x: get_attribute(x, "href"))\
        .orError()
    commentUser = Optional.ofNullable(get_path_by_index(commentUrl, 1)).orError()
    commentBodyElement = Optional.ofNullable(find_element_by_xpath(commentElement, ".//div[contains(@data-sigil, 'comment-body')]")).orError()
    commentId = Optional.ofNullable(get_attribute(commentBodyElement, "data-commentid")).orError()
    
    def setReplyTo(comments: list[Comment], commentId: str):
        for comment in comments:
            comment.replyTo = commentId
    
    commentContent = commentBodyElement.text
    
    commentTimestamp = Optional.ofNullable(find_element_by_xpath(commentElement, ".//div[contains(@data-sigil, 'ufi-inline-comment-actions')]//abbr"))\
        .map(lambda x: x.text)\
        .map(parseTimestamp)\
        .orError()

    # Expand more replies
    Optional.ofNullable(find_element_by_xpath(commentElement, ".//div[contains(@data-sigil, 'replies-see-more')]//a"))\
        .peek(lambda x: x.click())
            
    replies = Optional.ofNullable(find_elements_by_xpath(commentElement, ".//div[contains(@data-sigil, 'comment inline-reply')]"))\
        .map(lambda els: getComments(els))\
        .peek(lambda comments: setReplyTo(comments, commentId))\
        .get()
    
    return Comment(commentId, commentContent, [], replies, None, commentTimestamp, commentUser, commentUrl, None)

def getComments(commentElements: list[WebElement]) -> list[Comment] | None:
    comments: list[Comment] = []
    for commentElement in commentElements:
        comment = getComment(commentElement) 
        if comment is not None:
            comments.append(comment)
        else:
            return None
    return comments
    
def getCommentsOfUrl(url: str) -> list[Comment] | None:
    webDriver = driver.getWebDriver()
    webDriver.get(url)
    
    commentCount = 0
    while True:
        commentElements = Optional.ofNullable(find_elements_by_xpath(webDriver, "//div[@data-sigil='comment']")).orElse([])
        currentCommentCount = len(commentElements)
        if currentCommentCount > commentCount:
            commentCount = currentCommentCount
        else:
            # No more change after clicking load more comment
            break

        # Try clicking load more comment
        Optional.ofNullable(find_element_by_xpath(webDriver, "//div[contains(@class, 'async_elem')]//a")).ifPresent(lambda x: x.click())
        # Wait a little for ajax to finish loading the comments
        WebDriverWait(webDriver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "div")))

    if commentCount > 0:
        return getComments(commentElements)
    return []

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
    
def createPostsWithPageId(pageId: str, els: list[WebElement], cutOffFn: typing.Callable[[int, Post], bool], count: int) -> list[Post]:
    posts: list[Post] = []
    for el in els:
        count += 1
        post = createPost(el)
        if post is None:
            continue
        if cutOffFn(count, post):
            break
        post.pageId = pageId
        post.groupId = None
        posts.append(post)
    
    for post in posts:
        images = Optional.ofNullable(getImagesOfUrl(post.url)).orElse([])
        post.images = images
        comments = Optional.ofNullable(getCommentsOfUrl(post.url)).orError()
        for comment in comments:
            comment.postId = post.postId
        post.comments = comments

    return posts

def getPostsOfPage(pageId: str, cutOffCheck: typing.Callable[[int, Post], bool]) -> list[Post] | None:
    webDriver = driver.getWebDriver()
    webDriver.get(constants.FB_URL + "/" + pageId)

    allPosts: list[Post] = []
    # Scroll through the page to load posts
    lastHeight = webDriver.execute_script("return document.body.scrollHeight")
    while True:
        count = len(allPosts)
        posts = Optional.ofNullable(find_elements_by_xpath(webDriver, "//article[contains(@data-sigil, 'story-div story-popup-metadata  story-popup-metadata feed-ufi-metadata')]"))\
            .map(lambda x: createPostsWithPageId(pageId, x, cutOffCheck, count))\
            .orElse([])
        webDriver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        WebDriverWait(webDriver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "div")))
        newHeight = webDriver.execute_script("return document.body.scrollHeight")
        if newHeight == lastHeight:
            break
        lastHeight = newHeight        allPosts.extend(posts)
        if (len(allPosts) == count):
            continue
        break

    return allPosts

def parseTimestamp(timestamp: str) -> datetime:
    # Check if it has
    formats = ["%d tháng %m lúc %H:%M", "%d tháng %m, %Y lúc %H:%M"]
    for format in formats:
        try:
            return datetime.strptime(timestamp, format)
        except:
            continue
    
    # When post creation is less than 24 hour it will be in the format hour ago or minutes ago
    if timestamp.endswith("giờ"):
        return datetime.now() - timedelta(hours=int(timestamp.split(" ")[0]))
    if timestamp.endswith("phút"):
        return datetime.now() - timedelta(minutes=int(timestamp.split(" ")[0]))
    if timestamp == "Vừa xong":
        return datetime.now()
    raise ValueError("Recheck if facebook change their timestamp display formatting, this should not happened, here is the value it trying to parse: " + timestamp)    

def find_element_by_id(element: WebElement | WebDriver, id: str) -> WebElement | None:
    try:
        return element.find_element_by_id(id)
    except:
        pass
    
def find_elements_by_xpath(driver: WebElement | WebDriver, xpath: str) -> list[WebElement] | None:
    try:
        return driver.find_elements_by_xpath(xpath)
    except:
        pass

def find_element_by_xpath(element: WebElement | WebDriver, xpath: str) -> WebElement | None:
    try:
        return element.find_element_by_xpath(xpath)
    except: 
        pass
    
def get_attribute(element: WebElement, attribute: str) -> str | None:
    return element.get_attribute(attribute)

def find_element_by_tag_name(element: WebElement | WebDriver, tagName: str) -> WebElement | None:
    try:
        return element.find_element_by_tag_name(tagName)
    except:
        pass

def value_of_css_property(element: WebElement, property: str) -> str | None:
    try:
        return element.value_of_css_property(property)
    except:
        pass
    
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
    getPostsOfPage("etribune", limitNumberOfPostsCrawl(1_000_000))
    # outputPosts(getPostsOfPage("etribune", limitNumberOfPostsCrawl(1_000_000)), "crawled_data", "pages/etribune", "posts")

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