from __future__ import annotations

import logging
import time
import traceback
import typing
from typing import TypeVar
from selenium.common.exceptions import InvalidSessionIdException

T = TypeVar('T')  # Declare a type variable
K = TypeVar('K')

def exceptionHandler(f: typing.Callable[[], T], maxRetries: int = 10, shouldLog: bool = True, delayInSec: int = 0, reraise: bool = False) -> T | None:
    e: Exception | None = None
    for i in range(maxRetries):
        try:
            if i > 0:
                logging.info("Retrying: " + str(i))
            return f()
        except InvalidSessionIdException as innerE:
            # TODO: Refresh session id
            # TODO: Find a way to handle exception gracefully and allow resume from exception
            if shouldLog:
                logging.error(innerE) 
                logging.error(traceback.format_exc())
            e = innerE
            pass
        except Exception as innerE:
            if shouldLog:
                logging.error(innerE)
                logging.error(traceback.format_exc())
            e = innerE
            pass
        finally:
            if delayInSec > 0:
                time.sleep(delayInSec)
    if reraise:
        if e is not None:
            raise(e)
        