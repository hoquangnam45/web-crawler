from pathlib import Path
import traceback
import constants
import csv
from datetime import datetime
import json
import os
from typing import Union
import typing
from typing_extensions import deprecated
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import driver
import constants
from urllib.parse import parse_qs, urlparse
from selenium.webdriver.common.action_chains import ActionChains
import logging
from selenium.common.exceptions import InvalidSessionIdException
from selenium.common.exceptions import TimeoutException
import utils
from optional import Optional
from exception import exceptionHandler  
from comment import Comment
from image import Image
import comment
from video import Video
import image
import video
import jsonpickle

class Post: 
    def __init__(self, postId: str, parentId: str | None, crawlType: constants.CrawlType, content: str | None, images: list[Image] | None, videos: list[Video] | None, comments: list[Comment] | None, timestamp: datetime, userId: str, url: str):
        self.postId = postId
        self.parentId = parentId
        self.content = content
        self.images = images
        self.comments = comments
        self.timestamp = timestamp
        self.userId = userId
        self.url = url
        self.crawlType = crawlType
        self.videos = videos

def createPostsWithUrls(postEntriesPath: str, batchSize: int = 5, outputFile: str = "crawledPost.json") -> list[Post] | None:
    with open(postEntriesPath, "r") as f:
        csvReader = csv.reader(f)
        webDriver = driver.getWebDriver()
        postsBatch: list[Post] = []
        batchIndex: int = 0
        for row in csvReader:
            postId = row[0]
            parentId = row[1]
            crawlType = constants.CrawlType[row[2]]
            postTimestamp = datetime.strptime(row[3], '%Y-%m-%d %H:%M:%S')
            userId = row[4]
            postUrl = row[5]

            parsedUrl = urlparse(postUrl)
            if parsedUrl.hostname == urlparse(constants.BASIC_FB_URL).hostname or parsedUrl.hostname == urlparse(constants.MOBILE_FB_URL).hostname:
                if crawlType == constants.CrawlType.FB_PAGE:
                    # NOTE: Transform mbasic url into desktop url to circumvent rate limit issues set in place by FB 
                    webDriver.get(parsedUrl._replace(netloc = urlparse(constants.FB_URL).hostname, path = userId + "/posts/" + parse_qs(parsedUrl.query)["story_fbid"][0], query = "", fragment = "").geturl())
                elif crawlType == constants.CrawlType.FB_GROUP:
                    webDriver.get(constants.FB_URL + "/groups/" + parentId + "/posts/" + postId)
            else:
                webDriver.get(postUrl)
        
            post = Post(postId, parentId, crawlType, None, None, None, None, postTimestamp, userId, postUrl)
            
            postElement = Optional.ofNullable(exceptionHandler(lambda: utils.find_element_by_xpath(webDriver, "//*[@aria-describedby]"), 10, False)).orError()
            ariaDescribedBy = utils.get_attribute(postElement, "aria-describedby")
            tokens = ariaDescribedBy.split(" ")
            
            post.content = exceptionHandler(lambda: utils.find_element_by_xpath(postElement, ".//*[@id = '" + tokens[1] + "']").text, 1, False)
            
            postImageXpath = ".//*[@id = '" + tokens[2] + "']//a[@role = 'link' and (contains(@href, '/photo/') or contains(@href, '/photo.php'))]"
            postImageElements = utils.find_elements_by_xpath(postElement, postImageXpath)
            post.images = [image.getImage(postId, el) for el in postImageElements]
            
            # NOTE: Expand all comment
            currentHeight = webDriver.execute_script("return document.body.scrollHeight")
            idx = -1
            while True:
                idx += 1
                loadMoreCommentXpaths: dict[constants.CrawlType, list[str]] = {
                    constants.CrawlType.FB_PAGE: ["./following-sibling::*[1]//*[@role = 'button' and @tabindex = '0']"],
                    constants.CrawlType.FB_GROUP: ["./preceding-sibling::div[1]/div[@class]", "./following-sibling::div[1]//div[@role = 'button']"],
                }
                commentSectionElement = utils.find_element_by_xpath(postElement, ".//ul[1]")
                if crawlType == constants.CrawlType.FB_GROUP:
                    loadMoreCommentEl = Optional.ofNullable(exceptionHandler(lambda: utils.find_element_by_xpath(commentSectionElement, loadMoreCommentXpaths[crawlType][0]), 1, False))
                    if loadMoreCommentEl.isEmpty():
                        loadMoreCommentEl = Optional.ofNullable(exceptionHandler(lambda: utils.find_element_by_xpath(commentSectionElement, loadMoreCommentXpaths[crawlType][1]), 1, False))
                else:
                    loadMoreCommentEl = Optional.ofNullable(exceptionHandler(lambda: utils.find_element_by_xpath(commentSectionElement, loadMoreCommentXpaths[crawlType][0]), 1, False))

                if loadMoreCommentEl.isEmpty():
                    break
                if exceptionHandler(lambda: loadMoreCommentEl.peek(lambda x: x.click()).map(lambda _: True).orElse(False), 1, False) is False:
                    break

                # NOTE: Waiting until it finish ajax loading comment before starting next iteration
                WebDriverWait(webDriver, 10).until(lambda innerWebDriver: innerWebDriver.execute_script("return document.body.scrollHeight") > currentHeight)
                currentHeight = webDriver.execute_script("return document.body.scrollHeight")
            
            commentElementXpaths: dict[constants.CrawlType, str] = {
                constants.CrawlType.FB_GROUP: ".//ul/li//div[@role = 'article']/ancestor::li[1]",
                constants.CrawlType.FB_PAGE: ".//form[@role = 'presentation']/../../../../following-sibling::ul/li"
            }
            
            commentElements = utils.find_elements_by_xpath(postElement, commentElementXpaths[crawlType])
            post.comments = [comment.getComment(postId, crawlType, None, el, webDriver) for el in commentElements]
            
            # videoElements = utils.find_elements_by_xpath(postElement, commentElementXpaths[crawlType])
            # post.videos = [video.getVideo(postId, crawlType, el, webDriver) for el in videoElements]
            
            postsBatch.append(post)
            
            if len(postsBatch) >= batchSize:
                outputPosts(postsBatch, generateBatchFileName(outputFile, batchIndex))
                postsBatch.clear()
                batchIndex += 1
        return postsBatch

def generateBatchFileName(filePath: str, batchIndex: int) -> str:
    baseName = os.path.basename(filePath)
    dirName = os.path.dirname(filePath)
    
    fileName, ext = os.path.splitext(baseName)
    return os.path.join(dirName, fileName + "_" + str(batchIndex) + ext)
    
@deprecated("Use createPostsWithUrls instead") 
def createPost(postElement: WebElement, crawlType: constants.CrawlType) ->  Post | None:
    postStoryContainer = Optional.ofNullable(utils.find_element_by_xpath(postElement, ".//div[contains(@class, 'story_body_container')]")).orError()
    postHeaderElement = Optional.ofNullable(utils.find_element_by_xpath(postStoryContainer, ".//header")).orError()
    postBodyElement = Optional.ofNullable(utils.find_element_by_xpath(postStoryContainer, ".//div[contains(@data-gt, '{\"tn\":\"*s\"}')]")).orError()
    
    postUser = Optional.ofNullable(utils.find_element_by_xpath(postHeaderElement, ".//h3//a"))\
        .map(lambda it: utils.get_attribute(it, "href"))\
        .map(lambda it: utils.get_path_by_index(it, 1))\
        .orError()
    postUrl = Optional.ofNullable(utils.find_element_by_xpath(postHeaderElement, ".//div[contains(@data-sigil, 'm-feed-voice-subtitle')]//a"))\
        .map(lambda it: utils.get_attribute(it, "href"))\
        .orError()
    postTimestamp = Optional.ofNullable(utils.find_element_by_xpath(postHeaderElement, ".//div[contains(@data-sigil, 'm-feed-voice-subtitle')]//a"))\
        .map(lambda it: it.text)\
        .map(utils.parseTimestamp)\
        .orError()
    postId = Optional.of(postUrl)\
        .map(lambda it: utils.get_parameters(it, "id"))\
        .map(lambda it: it[0])\
        .orError()
    # NOTE: Post content element could be empty
    postContentElement = Optional.ofNullable(utils.find_element_by_xpath(postBodyElement, ".//div//span")).get()
    Optional.ofNullable(postContentElement).map(lambda x: utils.find_element_by_xpath(x, ".//span[@data-sigil='more']//a")).ifPresent(lambda x: x.click())
    postContent = Optional.ofNullable(postContentElement).map(lambda x: x.text).orElse("")
    
    return Post(postId, None, crawlType, postContent, None, None, None, postTimestamp, postUser, postUrl)

# NOTE: Side-effectful method, running this will save the cursor url from the seed url and output a text file contains basic post data collect from the seed url using cutOffCheck as the limiter whether to continue crawling the post or stop
def getPosts(id: str, crawlType: constants.CrawlType, cutOffCheck: typing.Callable[[int, Union[datetime, None]], tuple[bool, bool]], batchSize: int = 1, cursorUrlPath: str = "output/postCursor.txt", postEntriesPath: str = "output/postEntries.txt", outputFile: str = "output/crawledPost.json") -> list[Post] | None:
    webDriver = driver.getWebDriver()
    url = utils.mapIdToUrl(id, crawlType)
    try:
        with open(cursorUrlPath, 'r') as f:
            cursorUrl = f.readline()
            if len(cursorUrl.strip()) > 0:
                webDriver.get(cursorUrl)
            else:
                webDriver.get(url)
    except:        
        webDriver.get(url)

    batch: list[Post] = []
    batchIndex = -1
    crawlCount = 0
    currentBatch = -1
    
    while True:
        cutOff: bool = False
        
        previousCrawlCount: int = crawlCount
        if crawlType in [constants.CrawlType.FB_GROUP, constants.CrawlType.FB_PAGE]:
            postElementXpaths: dict[constants.CrawlType, str] = {
                constants.CrawlType.FB_PAGE: "//*[@id = 'structured_composer_async_container']//article[@data-ft]",
                constants.CrawlType.FB_GROUP: "//*[@id = 'm_group_stories_container']//article[@data-ft]",
            }
            postElements = utils.find_elements_by_xpath(webDriver, postElementXpaths[crawlType])
            
            for postElement in postElements:
                try: 
                    dataFt = utils.get_attribute(postElement, "data-ft")
                    metadata = json.loads(dataFt)
                    pageInsight = metadata["page_insights"]
                    userId = metadata["content_owner_id_new"]
                    parentId = list(pageInsight.keys())[-1] # Posts could be shared from page to page, the last object in page insights is the current page id
                    postId = metadata["top_level_post_id"]
                    postMetadata = pageInsight[list(pageInsight.keys())[0]]
                    postTimestamp = datetime.fromtimestamp(postMetadata["post_context"]["publish_time"])
                    postUrl = getPostUrl(postElement)
                    cursorUrl = str(webDriver.current_url)
               
                    cutOff, skip = cutOffCheck(crawlCount, postTimestamp)
                    
                    if skip:
                        continue
                    # Perform some cut off check to see whether we should scroll down more
                    if cutOff:
                        break
                    else:
                        post = Post(postId, parentId, crawlType, None, None, None, None, postTimestamp, userId, postUrl)
                        batch.append(post)
                        crawlCount += 1
                        logging.info("collect " + str(crawlCount) + " post entries")
                except Exception as e:
                    traceback.print_exc()
                    logging.error(e)
                    
        afterCrawlCount: int = crawlCount
        
        if afterCrawlCount - previousCrawlCount == 0:
            cutOff = True # No elements in batch get added to entries set, this could indicate that all entries either has timestamp outside the range we care, or the batch itself is empty, either ways stop further processing to avoid wasting time
        
        Path(os.path.dirname(cursorUrlPath)).mkdir(parents=True, exist_ok=True)
        with open(cursorUrlPath, 'w') as cursorF:
            # NOTE: Go to next page, and save the cursor in case the need to resume later
            cursorF.write(webDriver.current_url)
        
        currentBatch = int(crawlCount / batchSize)
        if currentBatch > batchIndex:
            if batchIndex >= 0:
                with open(postEntriesPath, 'a') as f:
                    csvWriter = csv.writer(f)
                    csvWriter.writerows([(el.postId, el.parentId, crawlType.name, el.timestamp, el.userId, el.url, webDriver.current_url) for el in batch[:batchSize]])
                    batch = batch[batchSize:]
            batchIndex = currentBatch
    
        if cutOff is True:
            Path(os.path.dirname(postEntriesPath)).mkdir(parents=True, exist_ok=True)
            with open(postEntriesPath, 'a') as f:
                csvWriter = csv.writer(f)
                csvWriter.writerows([(el.postId, el.parentId, crawlType.name, el.timestamp, el.userId, el.url, webDriver.current_url) for el in batch[:batchSize]])
                batch.clear()
            break
        else:
            loadMorePostElementXpaths: dict[constants.CrawlType, str] = {
                constants.CrawlType.FB_PAGE: "//*[@id = 'structured_composer_async_container']/*[2]//a",
                constants.CrawlType.FB_GROUP: "//*[@id = 'm_group_stories_container']/*[2]//a",
            }
            nextPageUrl = utils.get_attribute(utils.find_element_by_xpath(webDriver, loadMorePostElementXpaths[crawlType]), "href")
            webDriver.get(nextPageUrl)
            with open(cursorUrlPath, 'w') as cursorF:
                cursorF.write(nextPageUrl)
 
    return createPostsWithUrls(postEntriesPath, batchSize=batchSize, outputFile=outputFile)

@deprecated("Not needed anymore with mbasic version of FB URL since html attribute already include this info")
def getPostTimestamp(postElement: WebElement, timeout: int = 10) -> datetime | None:
    webDriver = driver.getWebDriver()
    try:
        return Optional.ofNullable(utils.get_attribute(postElement, "aria-describedby"))\
            .map(lambda x: x.split(" "))\
            .peek(lambda x: logging.info("post id: " + x[0]))\
            .map(lambda x: utils.find_element_by_xpath(postElement, ".//*[@id = '" + x[0] + "']"))\
            .peek(lambda _: webDriver.execute_script("arguments[0].scrollIntoView({behavior: 'auto',block: 'center',inline: 'center'});", postElement))\
            .peek(lambda _: WebDriverWait(webDriver, timeout).until(EC.visibility_of(postElement)))\
            .peek(lambda x: webDriver.execute_script("arguments[0].scrollIntoView({behavior: 'auto',block: 'center',inline: 'center'});", x))\
            .peek(lambda x: WebDriverWait(webDriver, timeout).until(EC.visibility_of_element_located((By.ID, utils.get_attribute(x, "id")))))\
            .peek(lambda x: ActionChains(webDriver).move_to_element(x).perform())\
            .peek(lambda x: WebDriverWait(webDriver, timeout).until(lambda _: Optional.ofNullable(utils.find_element_by_xpath(x, ".//*[@aria-describedby]")).isPresent()))\
            .map(lambda x: utils.find_element_by_xpath(x, ".//*[@aria-describedby]"))\
            .map(lambda x: utils.get_attribute(x, "aria-describedby"))\
            .peek(lambda x: logging.info("aria-describedby: " + x))\
            .peek(lambda x: WebDriverWait(webDriver, timeout).until(lambda innerWebDriver: Optional.ofNullable(utils.find_element_by_xpath(innerWebDriver, "//*[@id = '" + x + "']")).isPresent()))\
            .map(lambda x: utils.find_element_by_xpath(webDriver, "//*[@id = '" + x + "']").text)\
            .peek(lambda x: logging.info("text: " + x))\
            .map(utils.parseTimestamp)\
            .get()
    finally:
        ActionChains(webDriver).move_by_offset(50, 50).perform()

def getPostUrl(postElement: WebElement) -> str:
    return Optional.ofNullable(utils.find_element_by_xpath(postElement, ".//*[@data-ft = '{\"tn\":\"*W\"}']/*[2]/a[3]"))\
        .map(lambda x: utils.get_attribute(x, "href"))\
        .orError()

def outputPosts(posts: list[Post] | None, path: str = "./crawledPost.json", append: bool = False):
    if posts is None:
        return
    Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)
    # Clear the file if it exists
    if append is False:
        open(path, 'w').close()
    
    jsonpickle.set_preferred_backend('json')
    jsonpickle.set_encoder_options('json', ensure_ascii=False)
    with open(path, 'a') as f:
        jsonStr: str = jsonpickle.encode(posts, unpicklable=False, indent=4) # type: ignore
        f.write(jsonStr)