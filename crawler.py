from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
import argparse

import os
from time import sleep

from cio import read
from init import initDriver


def checkLiveClone(driver: WebDriver) -> bool:
    try:
        driver.get("https://mbasic.facebook.com/")
        sleep(2)
        driver.get("https://mbasic.facebook.com/")
        sleep(1)
        elementLive = driver.find_elements_by_xpath('//a[contains(@href, "/messages/")]')
        if (len(elementLive) > 0):
            print("Live")
            return True

        return False
    except:
        print("Check Live Fail")
        return False


def convertToCookie(cookie: str) -> str | None:
    try:
        new_cookie = ["c_user=", "xs="]
        cookie_arr = cookie.split(";")
        for i in cookie_arr:
            if i.__contains__('c_user='):
                new_cookie[0] = new_cookie[0] + (i.strip() + ";").split("c_user=")[1]
            if i.__contains__('xs='):
                new_cookie[1] = new_cookie[1] + (i.strip() + ";").split("xs=")[1]
                if (len(new_cookie[1].split("|"))):
                    new_cookie[1] = new_cookie[1].split("|")[0]
                if (";" not in new_cookie[1]):
                    new_cookie[1] = new_cookie[1] + ";"

        conv = new_cookie[0] + " " + new_cookie[1]
        if (conv.split(" ")[0] == "c_user="):
            return None
        else:
            return conv
    except:
        print("Error Convert Cookie")


def checkCookieLiveness(driver: WebDriver, cookie: str) -> bool:
    try:
        driver.get('https://mbasic.facebook.com/')
        sleep(1)
        driver.get('https://mbasic.facebook.com/')
        sleep(2)
        loginFacebookByCookie(driver ,cookie)

        return checkLiveClone(driver)
    except:
        print("check live fail")
        return False


def loginFacebookByCookie(driver: WebDriver, cookie: str):
    try:
        newCookie = convertToCookie(cookie)
        print(newCookie)
        if (newCookie != None):
            script = 'javascript:void(function(){ function setCookie(t) { var list = t.split("; "); console.log(list); for (var i = list.length - 1; i >= 0; i--) { var cname = list[i].split("=")[0]; var cvalue = list[i].split("=")[1]; var d = new Date(); d.setTime(d.getTime() + (7*24*60*60*1000)); var expires = ";domain=.facebook.com;expires="+ d.toUTCString(); document.cookie = cname + "=" + cvalue + "; " + expires; } } function hex2a(hex) { var str = ""; for (var i = 0; i < hex.length; i += 2) { var v = parseInt(hex.substr(i, 2), 16); if (v) str += String.fromCharCode(v); } return str; } setCookie("' + cookie + '"); location.href = "https://mbasic.facebook.com"; })();'
            driver.execute_script(script)
            sleep(5)
    except:
        print("loi login")

def outCookie(driver: WebDriver):
    try:
        sleep(1)
        script = "javascript:void(function(){ function deleteAllCookiesFromCurrentDomain() { var cookies = document.cookie.split(\"; \"); for (var c = 0; c < cookies.length; c++) { var d = window.location.hostname.split(\".\"); while (d.length > 0) { var cookieBase = encodeURIComponent(cookies[c].split(\";\")[0].split(\"=\")[0]) + '=; expires=Thu, 01-Jan-1970 00:00:01 GMT; domain=' + d.join('.') + ' ;path='; var p = location.pathname.split('/'); document.cookie = cookieBase + '/'; while (p.length > 0) { document.cookie = cookieBase + p.join('/'); p.pop(); }; d.shift(); } } } deleteAllCookiesFromCurrentDomain(); location.href = 'https://mbasic.facebook.com'; })();"
        driver.execute_script(script)
    except:
        print("loi login")


def getContentComment(driver: WebDriver) -> list[str]:
    try:
        links: list[WebElement] = driver.find_elements_by_xpath('//a[contains(@href, "comment/replies")]')
        ids: list[str] = []
        if (len(links)):
            for link in links:
                takeLink = link.get_attribute('href').split('ctoken=')[1].split('&')[0]
                textCommentElement = driver.find_element_by_xpath(('//*[@id="' + takeLink.split('_')[1] + '"]/div/div[1]'))
                if (takeLink not in ids):
                    print(textCommentElement.text)
                    writeFileTxt('comments.csv', textCommentElement.text)
                    ids.append(takeLink)
        return ids
    except:
        print("error get link")
        return []

def getAmountOfComments(driver: WebDriver, postId: str, numberCommentTake: int, filePath: str):
    try:
        driver.get("https://mbasic.facebook.com/" + str(postId))
        sumLinks = getContentComment(driver)
        while(sumLinks is not None and len(sumLinks) < numberCommentTake):
            try:
                nextBtn = driver.find_elements_by_xpath('//*[contains(@id,"see_next")]/a')
                if (len(nextBtn)):
                    nextBtn[0].click()
                    comments = getContentComment(driver)
                    if comments is not None:
                        sumLinks.extend(comments)
                else:
                    break
            except:
                print('Error when cralw content comment')
        
    except:
        print("Error get cmt")

def getPostIds(allPosts: list[str], driver: WebDriver) -> list[str]:
    sleep(2)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
    shareBtn: list[WebElement] = driver.find_elements_by_xpath('//a[contains(@href, "/sharer.php")]')
    newFoundPostIds: list[str] = []
    if (len(shareBtn)):
        for link in shareBtn:
            postId = link.get_attribute('href').split('sid=')[1].split('&')[0]
            if postId not in allPosts:
                print(postId)
                newFoundPostIds.append(postId)
    return newFoundPostIds

def getnumOfPostFanpage(allPosts: list[str], driver: WebDriver, pageId: str, amount: int, filePath: str):
    driver.get("https://touch.facebook.com/" + pageId)
    while len(allPosts) < amount:
        newFoundPostIds = getPostIds(allPosts, driver)
        writeFileTxt(filePath, newFoundPostIds)
        allPosts.extend(newFoundPostIds)

# NOTE: How do I plant to do this: read the seed to get some starting points -> follow the links + filter until enough data has been crawled
def main(cookie: str, driver: WebDriver): 
    if (checkCookieLiveness(driver, cookie) is not True):
        raise Exception("recheck cookie it's not work")
    
    crawlPostFile = 'postIds.csv'
    crawlCommentFile = 'commentIds.csv'
    
    # input:
    keywords = read("inputs/keywords.txt") 
    seedGroups = read("inputs/seeds.txt")

    # Crawl posts based on keywords

    # Crawl posts based on seeds
    # for group in seedGroups:



    # Filter for higher confidence

    # Normalize

    # Output

    allPosts = read(crawlPostFile)
    allComments = read(crawlCommentFile)
    getnumOfPostFanpage(allPosts, driver, 'thinhseu.official', 100, crawlPostFile)
    for postId in allPosts:
        getAmountOfComments(driver, postId, 1000, crawlCommentFile)

if __name__ == "__main__":
    parser = argparse.ArgumentParser("crawler")
    parser.add_argument("--cookie", dest="cookie", help="specify the cookie to be used to crawl facebook", type=str, required=True)
    args = parser.parse_args()  
    driver = initDriver()
    main(args.cookie, driver)