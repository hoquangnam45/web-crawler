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
from comment import Comment
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

T = TypeVar('T')  # Declare a type variable
K = TypeVar('K')

