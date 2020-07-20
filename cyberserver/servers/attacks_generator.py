import sys
import json
import time
from random import choice, randint, randrange
import pathlib
import logging
import timeit
import click
from click_help_colors import HelpColorsCommand, HelpColorsGroup
from typing import Union, Optional
from math import inf as INFINITE

from cyberserver.servers import utilities


_script_path = pathlib.Path(__file__)
_script_stem = pathlib.Path(__file__).stem
_script_name = pathlib.Path(__file__).name
_logger: logging.Logger


class AttacksGenerator(object):
    _logger: logging.Logger
    
    def __init__(
            self,
            channel: str = "raw-cyberattacks",
            ips_to_generate: Union[int, type(INFINITE)] = INFINITE,
            method: str = "random",
            interval: float = 0.1,
            filepath: Optional[Union[pathlib.Path, str]] = None,
            
            silent: Optional[bool] = None,
            script_mode: Optional[bool] = None,
            verbose: Optional[bool] = None
    ):
        
        self.method: str = method
        if self.method != "random":
            if filepath is None:
                raise FileNotFoundError(f"You have to specify a file for method {self.method}")
        
        self.ports = {
            0: "DoS",  # Denial of Service
            1: "ICMP",  # ICMP
            20: "FTP",  # FTP Data
            21: "FTP",  # FTP Control
            22: "SSH",  # SSH
            23: "TELNET",  # Telnet
            25: "EMAIL",  # SMTP
            43: "WHOIS",  # Whois
            53: "DNS",  # DNS
            80: "HTTP",  # HTTP
            88: "AUTH",  # Kerberos
            109: "EMAIL",  # POP v2
            110: "EMAIL",  # POP v3
            115: "SFTP",  # SFTP
            118: "SQL",  # SQL
            143: "EMAIL",  # IMAP
            156: "SQL",  # SQL
            161: "SNMP",  # SNMP
            220: "EMAIL",  # IMAP v3
            389: "AUTH",  # LDAP
            443: "HTTPS",  # HTTPS
            445: "SMB",  # SMB
            636: "AUTH",  # LDAP of SSL/TLS
            1433: "SQL",  # MySQL Server
            1434: "SQL",  # MySQL Monitor
            3306: "SQL",  # MySQL
            3389: "RDP",  # RDP
            5900: "RDP",  # VNC:0
            5901: "RDP",  # VNC:1
            5902: "RDP",  # VNC:2
            5903: "RDP",  # VNC:3
            8080: "HTTP",  # HTTP Alternative
        }
        
        self.ips_to_generate: int = ips_to_generate
        
        # random method
        self.channel: str = channel
        self.interval: float = interval
        
        # file methods
        self.filepath: pathlib.Path = filepath
        
        self.silent: bool = silent
        self.verbose: bool = verbose
        self.script_mode: bool = script_mode
        self.redis_watcher: utilities.RedisWatcher = utilities.RedisWatcher(silent = self.silent)
        self.ips_forged: int = 0
        
        # initiation
        self._logger = utilities.logging.get_console_logger(
            name = _script_stem,
            level = logging.DEBUG if self.verbose else logging.INFO,
            disable_stream = True if self.silent else False
        )
        
        self._logger.info(f"Method used {utilities.colorize(self.method, 'gold_1')}")
        if self.method != "random":
            self._logger.info(f"File used {utilities.colorize(self.filepath, 'gold_1')}")
        
        self._logger.info(
            f"Number of IPs to generate "
            f"{utilities.colorize(self.ips_to_generate if self.ips_to_generate != INFINITE else '∞', 'gold_1')}"
        )
        self._logger.info(
            f"Publishing to channel "
            f"{utilities.colorize(self.channel, 'gold_1')}"
        )
        self._logger.info(f"Publishing interval {utilities.colorize(self.interval, 'gold_1')} seconds")
        self._logger.info(f"Silent mode {utilities.colorize(self.silent and 'on' or 'off', 'gold_1')}")
        self._logger.info(f"Script mode {utilities.colorize(self.script_mode and 'on' or 'off', 'gold_1')}")
    
    def __call__(self):
        self.start_time = timeit.default_timer()
        self._logger.info(
            f"Attacks Generator started at: "
            f"{utilities.colorize(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), 'gold_1')}"
        )
        
        if self.method == "random":
            self.random()
    
    def __del__(self):
        if not self.silent:
            sys.stdout.write("\033[1000D\033[K")
            self._logger.info(f"Stopped generator. Total IPs generated: {utilities.colorize(self.ips_forged)}")
    
    def random(self):
        while self.ips_to_generate == INFINITE or self.ips_forged < self.ips_to_generate:
            port = choice(list(self.ports.keys()))
            
            data = {
                'src': {
                    'ip': self.ipv4(),
                    'port': port
                },
                'dst': {
                    'ip': self.ipv4(),
                    'port': port
                },
                'type': self.ports[port],
                'cve': f"CVE:{randrange(1997, 2019)}:{randrange(1, 400)}"
            }
            json_data = json.dumps(data)
            self.redis_watcher.server.publish(channel = self.channel, message = json_data)
            self.ips_forged += 1
            self._logger.info(
                f"Published random IP "
                f"[{utilities.colorize(f'{self.ips_forged}', 'gold_1')}]"
            )
            
            self._logger.debug(f"{json.dumps(data, indent = 4)}")
            
            if not self.script_mode and not self.silent:
                print("\033[A\033[K", end = '')
            
            time.sleep(self.interval)
    
    @staticmethod
    def ipv4() -> str:
        """
        To generate a more accurate representation of an IP address these rules are followed:
        https://www.quora.com/How-do-you-identify-an-invalid-IP-address
        1.Any address that begins with a 0 is invalid (except as a default route).
        2.Any address with a number above 255 in it is invalid.
        3.Any address that has more than 3 dots is invalid.
        4.Any address that begins with a number between 240 and 255 is reserved, and effectively invalid.
           (Theoretically, they’re usable, but I’ve never seen one in use.)
        5.Any address that begins with a number between 224 and 239 is reserved for multicast, and probably invalid.
        """
        
        # the left-most part of the address is calculated first as it has the most restrictions
        return ".".join(
            [
                str(randint(1, 222)),
                str(randint(1, 255)),
                str(randint(1, 255)),
                str(randint(1, 255)),
            ]
        )
    
    @property
    def method(self):
        return self._method
    
    @method.setter
    def method(self, value: str):
        available_methods = ['random', 'json', 'text', 'csv']
        
        if not isinstance(value, str):
            raise TypeError(f"method must be a string. Available methods: {','.join(available_methods)}")
        
        if value.lower() not in available_methods:
            raise ValueError(f"method {value} is not available. Available methods: {','.join(available_methods)}")
        
        self._method = value.lower()
    
    @property
    def ports(self):
        return self._ports
    
    @ports.setter
    def ports(self, value):
        if not isinstance(value, dict):
            raise TypeError("ports must a dict")
        self._ports = value
    
    @property
    def filepath(self) -> pathlib.Path:
        return self._filepath
    
    @filepath.setter
    def filepath(self, value):
        if value is not None:
            if not isinstance(value, pathlib.Path) or not isinstance(value, str):
                raise TypeError("filepath must be a string or a pathlib.Path object")
            self._filepath = pathlib.Path(value)


# region Command Line Tool section

# region command settings
@click.group(
    cls = HelpColorsGroup,
    help_headers_color = 'green',
    help_options_color = 'bright_red',
    name = "Attacks Generator",
    context_settings = {
        "help_option_names": ['-h', '--help'],
        "ignore_unknown_options": True
    },
    no_args_is_help = False,
    invoke_without_command = True,
    options_metavar = "<options>"
)
# endregion
# region channel option
@click.option(
    '-c',
    '--channel',
    default = "raw-cyberattacks",
    type = click.STRING,
    metavar = "string",
    help = "Redis channel in which the attacks will be forwarded"

)
# endregion
# region interval option
@click.option(
    "-i",
    "--interval",
    default = 0.05,
    metavar = "Float",
    type = click.FloatRange(0.05, 100),
    help = "Interval between each publication"
)
# endregion
# region autostart option
@click.option(
    "-a",
    "--autostart",
    metavar = "switch",
    is_flag = True,
    help = "Immediately start publishing generated attacks"
)
# endregion
# region verbose option
@click.option(
    "--verbose",
    metavar = "switch",
    is_flag = True,
    help = "Enables verbose logging messages"
)
# endregion
# region silent option
@click.option(
    "--silent",
    metavar = "switch",
    is_flag = True,
    help = "Disables ALL logging messages"
)
# endregion
# region script-mode option
@click.option(
    "--script-mode",
    metavar = "switch",
    is_flag = True,
    help = "Enables script mode which uses dynamic printing features in the terminal."
           "CAUTION: using this flag when initializing Attacks Generator from another module may break some "
           "logging messages"
)
# endregion
@click.pass_context
def main(ctx, channel: str, interval: float, verbose: bool, silent: bool, script_mode: bool, autostart: bool):
    """
    Custom command line utility to generate cyberattacks for publishing to a redis channel
    """
    
    ctx.obj = {
        "channel": channel,
        "interval": interval,
        "verbose": verbose,
        "silent": silent,
        "script_mode": script_mode,
        "autostart": autostart
    }
    
    if ctx.invoked_subcommand is None:
        ctx.invoke(random)
    else:
        # click.echo('I am about to invoke %s' % ctx.invoked_subcommand)
        pass


@main.command()
# region forge option
@click.option(
    "-f",
    "--forge",
    "ips_to_forge",
    default = INFINITE,
    metavar = "float",
    type = click.FLOAT,
    help = "Number of IP to forge"
)
# endregion
@click.pass_context
def random(ctx, ips_to_forge):
    
    generator = AttacksGenerator(
        method = "RaNdOm",
        channel = ctx.obj["channel"],
        ips_to_generate = ips_to_forge,
        interval = ctx.obj["interval"],
        silent = ctx.obj["silent"],
        script_mode = ctx.obj["script_mode"]
    )
    
    try:
        generator()
    except KeyboardInterrupt:
        if ctx.obj["script_mode"] and not ctx.obj["silent"]:
            sys.stdout.write("\033[1000D\033[K")


# endregion

if __name__ == '__main__':
    main()
