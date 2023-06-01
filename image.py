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
from typing_extensions import deprecated
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
import base64
import utils
from optional import Optional

class Image:
    # NOTE: url is the link to the downloadable image file, whereare sourceUrl is the link to the image page, which could be used
    # to crawl for more data like comment inside the image page
    def __init__(self, parentId: str, id: str, url: str, sourceUrl: str | None):
        self.id = id
        self.url = url
        self.sourceUrl = sourceUrl
        self.parentId = parentId
        

def getImage(parentId: str, imageElement: WebElement) -> Image:
    imageUrl = Optional.ofNullable(utils.find_element_by_xpath(imageElement, ".//img[@src]"))\
        .map(lambda x: utils.get_attribute(x, "src"))\
        .orError()
    imageSrc = Optional.ofNullable(utils.get_attribute(imageElement, "href"))\
        .orError()
    imageId = Optional.ofNullable(imageSrc)\
        .map(lambda x: utils.get_parameters(x, "fbid"))\
        .map(lambda x: x[0])\
        .orError()

    return Image(parentId, imageId, imageUrl, imageSrc)

@deprecated("use getImageXX method instead")
def getImagesOfUrl(url: str) -> list[Image] | None:
    return None
    # webDriver = driver.getWebDriver()
    # webDriver.get(url)
    
    # imageElements = Optional.ofNullable(utils.find_element_by_xpath(webDriver, ".//div[@data-ft = '{\"tn\":\"H\"}']"))\
    #     .map(lambda el: utils.find_elements_by_xpath(el, ".//div[@data-gt = '{\"tn\":\"E\"}']"))\
    #     .filter(lambda x: len(x) > 0)\
    #     .get()
    # if imageElements is None:
    #     return None
    # ret: list[Image] = []
    # for el in imageElements:
    #     img = getImage(el, constants.CrawlType.FB_PAGE, )
    #     if img is None:
    #         return None
    #     ret.append(img)
    # return ret