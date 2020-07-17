import colored
from time import strftime, localtime


def colorize(text, color = 'green'):
    return colored.stylize(text, colored.fg(color))


def time_colored(color = "gold_1", reverse = True):
    return colored.stylize(
        text = strftime('[%Y-%m-%d %H:%M:%S]', localtime()),
        styles = [colored.fg(color), colored.attr('reverse')] if reverse else colored.fg(color)
    )
