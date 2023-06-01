from __future__ import annotations
import csv
from datetime import datetime
import json
import os
import traceback
from typing import TypeVar
from typing_extensions import deprecated
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import driver
from urllib.parse import parse_qs, urlparse
from selenium.webdriver.common.action_chains import ActionChains
import logging
import base64
import utils
from optional import Optional
from exception import exceptionHandler
import constants
from image import Image
import image

T = TypeVar('T')

class Comment:
    def __init__(self, commentId: str, content: str, images: list[Image], replies: list[Comment] | None, replyTo: str | None, timestamp: datetime | None, userId: str, url: str, postId: str | None):
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
        self.hasReply = Optional.ofNullable(replies).map(lambda x: len(x) > 0).orElse(False)

# TODO: Recheck comment timestamp getting approach, when OP comment, it happen twice
def getComment(postId: str, crawlType: constants.CrawlType, replyTo: str | None, commentElement: WebElement, webDriver: WebDriver) -> Comment:
    commentTimestamp = Optional.ofNullable(exceptionHandler(lambda: getCommentTimestamp(commentElement, timeoutInSec=1), 10, False)).orError()
    commentUrl = utils.get_attribute(utils.find_element_by_xpath(commentElement, ".//a[contains(@href, 'comment_id')]"), "href")
    queries = Optional.of(commentUrl)\
            .map(urlparse)\
            .map(lambda x: x.query)\
            .map(parse_qs)
    if crawlType == constants.CrawlType.FB_PAGE:
        commentUser = queries.map(lambda xs: xs.get("id", None)).map(lambda xs: xs[0]).orElse(Optional.ofNullable(utils.get_path_by_index(commentUrl, 1)).orError())
    elif crawlType == constants.CrawlType.FB_GROUP:
        userUrl = utils.get_attribute(utils.find_element_by_xpath(commentElement, ".//a[contains(@href, '/user/')]"), "href")
        commentUser = Optional.of(userUrl)\
            .map(lambda url: utils.get_path_by_name(url, "user"))\
            .orError()
            
    # NOTE: it's in the format comment:id1_id2 or just plain comment_id
    commentId = exceptionHandler(lambda: queries\
        .map(lambda xs: xs["comment_id"][0])\
        .map(base64.b64decode)\
        .map(lambda decoded_bytes: decoded_bytes.decode('utf-8'))\
        .map(lambda decoded_str: decoded_str.split(":")[1])\
        .map(lambda ids: ids.split("_")[0])\
        .orError(), 1, False)
    if commentId is None:
        commentId = queries\
            .map(lambda xs: xs["comment_id"][0]).orError()
    try:
        commentContentSectionXpaths: dict[constants.CrawlType, str] = {
            constants.CrawlType.FB_PAGE: ".//a[contains(@href, 'comment_id')]/../following-sibling::*[1]",
            constants.CrawlType.FB_GROUP: ".//a[contains(@href, 'user')]/../ancestor::span[@class = '']/following-sibling::div[1]",
        }
        # NOTE: Some comment do not have content such as when they post only image
        commentContentSection = exceptionHandler(lambda: utils.find_element_by_xpath(commentElement, commentContentSectionXpaths[crawlType]), 1, False)

        # NOTE: Click read more
        # NOTE: This is so weird some time click into read more using selenium get all the text but the comment is not 
        # expand in the browser but anyways currently it get all the text after clicking read more even though the browser 
        # UI do not match, just weird behaviour from facebook
        Optional.ofNullable(commentContentSection)\
            .map(lambda x: exceptionHandler(lambda: utils.find_element_by_xpath(x, ".//*[@role = 'button']"), 1, False))\
            .peek(lambda x: webDriver.execute_script("arguments[0].scrollIntoView({behavior: 'auto',block: 'center',inline: 'center'});", x))\
            .ifPresent(lambda x: x.click())
        commentContent = Optional.ofNullable(commentContentSection).map(lambda x: x.text).orElse(None)
        
        # NOTE: Replies and images will be set later
        comment = Comment(commentId, commentContent, [], [], replyTo, commentTimestamp, commentUser, commentUrl, postId)
                
        comment.images = [image.getImage(commentId, el) for el in utils.find_elements_by_xpath(commentElement, ".//a[@role = 'link' and (contains(@href, '/photo/') or contains(@href, '/photo.php'))]")]
        
        # NOTE: Top level comment reply section sometimes have different structure from reply section of reply
        relpliesXpathTopLevel = "./*/*/ul"
        relpliesXpathReply = "./*/ul"
        try:
            webDriver = driver.getWebDriver()
            while True:
                readMoreBtn = exceptionHandler(lambda: utils.find_element_by_xpath(commentElement, "./*/*/*/*[@role = 'button']"), 1, False)
                if readMoreBtn is None: # NOTE: Just weird FB structure
                    readMoreBtn = exceptionHandler(lambda: utils.find_element_by_xpath(commentElement, "./*/*/*[@role = 'button']"), 1, False)
                if readMoreBtn is None:
                    break
                # Expand replies and wait until reply section is visible
                Optional.ofNullable(readMoreBtn)\
                    .peek(lambda x: webDriver.execute_script("arguments[0].scrollIntoView({behavior: 'auto',block: 'center',inline: 'center'});", x))\
                    .peek(lambda x: x.click())\
                
                if readMoreBtn is not None:
                    # NOTE: Optimization changing the order of wait for reply and top level comment
                    if replyTo is not None: # Is reply
                        WebDriverWait(webDriver, 10).until(lambda _: exceptionHandler(lambda: utils.find_element_by_xpath(commentElement, relpliesXpathReply), 1, False) is not None)
                    else: # Top level comment
                        WebDriverWait(webDriver, 10).until(lambda _: exceptionHandler(lambda: utils.find_element_by_xpath(commentElement, relpliesXpathTopLevel), 1, False) is not None)
        except Exception as e:
            print(e)
        
        if replyTo is None:
            repliesSection = exceptionHandler(lambda: utils.find_element_by_xpath(commentElement, relpliesXpathTopLevel), 1, False)
        else:
            repliesSection = exceptionHandler(lambda: utils.find_element_by_xpath(commentElement, relpliesXpathReply), 1, False)
            
        comment.hasReply = repliesSection is not None
        if comment.hasReply:
            comment.replies = [getComment(postId, crawlType, commentId, el, webDriver) for el in Optional.ofNullable(repliesSection).map(lambda x: utils.find_elements_by_xpath(x, "./li")).orElse([])]
        
        return comment
    except Exception as e:
        print(traceback.format_exc())
        raise(e)

def getCommentTimestamp(commentElement: WebElement, timeoutInSec: int = 10) -> datetime:
    webDriver = driver.getWebDriver()
    return Optional.of(utils.find_element_by_xpath(commentElement, ".//ul[@aria-hidden = 'false']//a[contains(@href, 'comment_id')]"))\
            .peek(lambda _: webDriver.execute_script("arguments[0].scrollIntoView({behavior: 'auto',block: 'center',inline: 'center'});", commentElement))\
            .peek(lambda _: WebDriverWait(webDriver, timeoutInSec).until(EC.visibility_of(commentElement)))\
            .peek(lambda x: webDriver.execute_script("arguments[0].scrollIntoView({behavior: 'auto',block: 'center',inline: 'center'});", x))\
            .peek(lambda x: WebDriverWait(webDriver, timeoutInSec).until(EC.visibility_of(x)))\
            .peek(lambda x: ActionChains(webDriver).move_to_element(x).perform())\
            .peek(lambda x: WebDriverWait(webDriver, timeoutInSec).until(lambda _: Optional.ofNullable(utils.find_element_by_xpath(x, ".//*[@aria-describedby]")).isPresent()))\
            .map(lambda x: utils.find_element_by_xpath(x, ".//*[@aria-describedby]"))\
            .map(lambda x: utils.get_attribute(x, "aria-describedby"))\
            .peek(lambda x: logging.info("aria-describedby: " + x))\
            .peek(lambda x: WebDriverWait(webDriver, timeoutInSec).until(lambda innerWebDriver: Optional.ofNullable(utils.find_element_by_xpath(innerWebDriver, "//*[@id = '" + x + "']")).isPresent()))\
            .map(lambda x: utils.find_element_by_xpath(webDriver, "//*[@id = '" + x + "']").text)\
            .peek(lambda x: logging.info("text: " + x))\
            .map(utils.parseTimestamp)\
            .orError()

            
def outputComments(comments: list[Comment] | None, path: str, group: str, id: str):
    pass
    # if comments is None:
    #     return
    # with open(path + os.path.sep + id + ".csv", 'r') as f:
    #     writer = csv.writer(f)
    #     writer.writerow(["id", "userId", "pageId", "groupId", "content", "images", "timestamp"])
            
        # # Flatten comments
        # flattenedComments: list[Comment] = 
        
        # for comment in comments:
        #     writer.writerow([post.postId, post.userId, post.pageId, post.groupId, post.content, post.images, post.timestamp])
        #     outputComments(post.comments, path, id, "comments")