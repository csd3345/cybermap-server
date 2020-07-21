"""
Utilities package

An opinionated, minimal template for utilities needed for cyberserver
"""

from .redis_watcher import RedisWatcher

from .logging import (
    get_console_logger,
    get_rotating_file_logger,
    init_logger_from_file,
)
from .colors import (
    colorize,
    time_colored,
)

from .platform import (
    get_platform,
    get_time,
    confirmation
)


def frange(start, stop = None, step = None):
    if stop is None:
        stop = start + 0.0
        start = 0.0
    
    if step is None:
        step = 1.0
    
    while True:
        if step > 0 and start >= stop:
            break
        elif step < 0 and start <= stop:
            break
        yield float(start)  # return float number
        start = start + step


__all__ = [
    "get_console_logger",
    "get_rotating_file_logger",
    "init_logger_from_file",
    "colorize",
    "time_colored",
    "get_platform",
    "confirmation",
    "get_time",
    "RedisWatcher"
]
