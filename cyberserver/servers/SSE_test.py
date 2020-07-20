import signal
import pathlib
from typing import Optional, Awaitable

from tornado import web
from tornado.log import app_log
from tornado.options import options, define, parse_command_line
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop, PeriodicCallback
from tornado.iostream import StreamClosedError

from . import SSEHandler
from .utilities.colors import colorize
import logging

import click
import pathlib
from click_help_colors import HelpColorsGroup


logger = logging.getLogger()

_script_path = pathlib.Path(__file__)
_script_stem = pathlib.Path(__file__).stem
_script_name = pathlib.Path(__file__).name

# _map_path = _script_path.parent.parent.joinpath("map")
_map_path = pathlib.Path("/var/www/cybermap")
_map_index_page = _map_path.joinpath("index.html")


class Cybermap(web.Application):
    def __init__(self):
        handlers = [
                       (r'/', MainHandler),
                       (r'/events', SSEHandler),
                       # UNCOMMENT IF YOU DONT USE NGINX
                       # (r'/js/(.*)', web.StaticFileHandler, {'path': str(_map_path.joinpath('js'))}),
                       # UNCOMMENT IF YOU DONT USE NGINX
                       # (r'/css/(.*)', web.StaticFileHandler, {'path': str(_map_path.joinpath('css'))}),
                       # UNCOMMENT IF YOU DONT USE NGINX
                       # (r'/assets/(.*)', web.StaticFileHandler, {'path': str(_map_path.joinpath('assets'))}),
                   ],
        settings = dict(
            # cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
            # xsrf_cookies=True,
            debug = False,
        )
        web.Application.__init__(self, *handlers, **settings)


class MainHandler(web.RequestHandler):
    
    def head(self):
        pass
    
    def get(self):
        logger.info(f"New request received: {repr(self.request)}")
        self.render(str(_map_index_page))


@click.group(
    cls = HelpColorsGroup,
    help_headers_color = 'green',
    help_options_color = 'bright_red',
    name = "Cybermap Tornado Server",
    context_settings = {
        "help_option_names": ['-h', '--help'],
        "ignore_unknown_options": True
    },
    no_args_is_help = False,
    invoke_without_command = True,
    options_metavar = "<options>"
)
@click.option(
    "-p",
    "--port",
    default = 8080,
    type = click.INT,
    metavar = "<integer>",
    help = "Port that tornado server will listen to"
)
@click.option(
    "--no-nginx",
    is_flag = True,
    metavar = "<switch>",
    help = "Disable NGINX integration for load balancing"
)
@click.option(
    "-v",
    "--verbose",
    is_flag = True,
    metavar = "<switch>",
    help = "Enable verbose logging messages"
)
@click.pass_context
def main(ctx, port, no_nginx, verbose):
    # arguments are handled by click, with args=[] we only enable tornado's logging without parsing command line options
    parse_command_line(args = ["", f"--logging={'debug' if verbose else 'info'}"])
    
    logger.info(f"port: {port}")
    logger.info(f"no-nginx: {colorize(no_nginx and 'on' or 'off', 'gold_1')}")
    logger.info(f"verbose: {colorize(verbose and 'on' or 'off', 'gold_1')}")
    
    if no_nginx:
        logger.info("Static content will be served from tornado instead of NGINX")
    
    server = HTTPServer(Cybermap(), xheaders = True)
    server.listen(port)
    logger.info(f"Cybermap's HTTPServer started on port {port}")
    try:
        IOLoop.instance().start()
    except KeyboardInterrupt:
        IOLoop.instance().stop()


if __name__ == "__main__":
    main()
