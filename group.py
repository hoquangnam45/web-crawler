from datetime import datetime
import json
from comment import Comment
from image import Image
import constants

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