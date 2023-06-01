from __future__ import annotations
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlparse

from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
import constants

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

def get_path_by_index(url: str, index: int) -> str | None:
    parsed_url = urlparse(url)
    path_segments = parsed_url.path.split('/')
    if len(path_segments) > index:
        return path_segments[index]
    else:
        return None

def get_path_by_name(url: str, paramName: str) -> str | None:
    parsed_url = urlparse(url)
    path_segments = parsed_url.path.split('/')
    for index, segment in enumerate(path_segments):
        if segment == paramName: 
            return path_segments[index + 1]
    return None


def get_parameters(url: str, parameter: str) -> list[str] | None:
    parsed_url = urlparse(url)

    # Get the query parameters as a dictionary
    query_params = parse_qs(parsed_url.query)

    # Access specific query parameter values
    return query_params.get(parameter)

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

def lenN(xs: list | None) -> int:
    if xs is None:
        return 0
    return len(xs)

def mapIdToUrl(id: str, type: constants.CrawlType) -> str:
    if type == constants.CrawlType.FB_GROUP:
        return getFbGroupUrl(id)
    if type == constants.CrawlType.FB_PAGE:
        return getFbPageUrl(id)

def getFbPageUrl(pageId: str) -> str: 
    return constants.BASIC_FB_URL + "/" + pageId + "?v=timeline"

def getFbGroupUrl(groupId: str) -> str: 
    return constants.BASIC_FB_URL + "/groups/" + groupId