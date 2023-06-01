from __future__ import annotations
import argparse
from datetime import datetime, timedelta
from typing import Union
import typing
import logging
import post
import constants


def main():
    post.getPosts("tanbinh.phongtro.club", constants.CrawlType.FB_GROUP, limitNumberOfPostsCrawl(1000))
    # post.createPostsWithUrls("output/postEntries.txt")
    # post.createPostsWithUrls("postEntries.txt", batchSize=1, outputFile="output/crawledPost.json")
    # post.outputPosts(post.getPosts("tanbinh.phongtro.club", constants.CrawlType.FB_GROUP, limitNumberOfPostsCrawl(30)), "crawled_data", "tanbinh.phongtro.club")

def limitNumberOfPostsCrawl(upperLimit: int, upperTimeDelta: timedelta=timedelta(days=30)) -> typing.Callable[[int, Union[datetime, None]], tuple[bool, bool]]:
    def fn(count: int, postTimestamp: datetime | None) -> tuple[bool, bool]:
        now = datetime.now()
        if count >= upperLimit:
            return True, False
        if postTimestamp is not None:
            duration = now - postTimestamp
            if duration >= upperTimeDelta:
                return False, True
        return False, False
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