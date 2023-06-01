from datetime import datetime


class Post:
    def __init__(self, postId: str, pageId: str, groupId: str, content: str, images: list[str], commentIds: list[str], timestamp: datetime, userId: str):
        self.postId = postId
        self.pageId = pageId
        self.groupId = groupId
        self.content = content
        self.images = images
        self.commentIds = commentIds
        self.timestamp = timestamp
        self.userId = userId