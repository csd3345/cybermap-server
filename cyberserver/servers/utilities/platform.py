import sys
import time
import click

from .colors import time_colored


def get_platform():
    """Check the OS in which the script is running"""
    platforms = {
        'linux': 'Linux',
        'linux1': 'Linux',
        'linux2': 'Linux',
        'darwin': 'OS X',
        'win32': 'Windows'
    }
    if sys.platform not in platforms:
        return sys.platform
    
    return platforms[sys.platform]


def get_time(mode: str = "local"):
    modes = ["local", "GMT"]
    if mode not in modes:
        raise ValueError(f"Mode: {mode} is not defined. Use one of the following [{','.join(modes)}]")
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime() if mode == "local" else time.gmtime())


def confirmation(msg: str = "confirm"):
    try:
        click.confirm(f"{time_colored()} {msg}?", abort = True)
    except click.Abort:
        return False
    return True
