from datetime import datetime

from typing import Type, TypeVar
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

T = TypeVar('T')

COMMENT_FACEBOOK_URL = 'https://www.facebook.com/comments'

class Comment:
    def __init__(self, postId: str, commentId: str, content: str, commentIds: list[str], timestamp: datetime):
        self.postId = postId;
        self.commentId = commentId;
        self.content = content;
        self.commentIds = commentIds;
        self.timestamp = timestamp;
    
    @staticmethod
    def getComment(webdriver: WebDriver, commentId: str):
        webdriver.get(COMMENT_FACEBOOK_URL + "/" + commentId)