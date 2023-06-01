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

T = TypeVar('T')  # Declare a type variable
K = TypeVar('K')

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
            return Optional[K].empty()
        return fn(self.val)
        
    def map(self, fn: typing.Callable[[T], Union[Union[K, None], K]]) -> Optional[K]:
        if self.val is None:
            return Optional[K].empty()
        return Optional(fn(self.val))
    
    def peek(self, fn: typing.Callable[[T], Any]) -> Optional[T]:
        self.ifPresent(fn)
        return self
    
    def get(self) -> T | None:
        return self.val
    
    def orElse(self, defaultValue: T) -> T:
        if self.val is not None:
            return self.val
        return defaultValue
    
    def orElseGet(self, factory: typing.Callable[[], T]) -> T:
        if self.val is not None:
            return self.val
        return factory()
    
    def orError(self) -> T:
        if self.val is None:
            raise ValueError("value is None")
        return self.val
    
    def isPresent(self) -> bool:
        return self.val is not None
    
    def isEmpty(self) -> bool:
        return self.val is None
    
    def ifPresent(self, fn: typing.Callable[[T], Any]):
        self.map(fn)
    
    def filter(self, fn: typing.Callable[[T], bool]) -> Optional[T]:
        if self.val is None or fn(self.val) is False:
            return Optional.empty()
        return Optional(self.val)
