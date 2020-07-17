import redis
import re
import io
import os
import sys
import json
import time
import datetime
import redis
import click
from click_help_colors import HelpColorsCommand
import timeit
import pickle
import random
import logging
import pathlib
import colored
import maxminddb
import cryptography.fernet
import threading
import shutil

from itertools import islice
from datetime import timedelta

# import keyring
from options import Options
from pprint import pprint
from copy import copy, deepcopy
from typing import Optional, List, Dict, Any, Set, Union
from textwrap import dedent

import cybermap.servers.utilities as utilities
from cybermap.servers.utilities import RedisWatcher
from cybermap.servers.attacks_generator import AttacksGenerator


_script_path = pathlib.Path(__file__)
_script_stem = _script_path.stem
_script_name = _script_path.name


def erase_line():
    sys.stdout.write("\033[1000D\033[K")
    sys.stdout.flush()


class ServerStats(object):
    
    def __init__(self):
        self.types = {
            "TOTAL": 0,
            "AUTH": 0,
            "DNS": 0,
            "DoS": 0,
            "EMAIL": 0,
            "FTP": 0,
            "HTTP": 0,
            "HTTPS": 0,
            "ICMP": 0,
            "RDP": 0,
            "SFTP": 0,
            "SMB": 0,
            "SNMP": 0,
            "SQL": 0,
            "SSH": 0,
            "TELNET": 0,
            "WHOIS": 0,
        }
        self.ips = {
            "TOTAL": 0
        }
        self.countries: Dict[str, Union[Dict, int]] = {
            "TOTAL": 0,
        }
        
        file = pathlib.Path("/var/log/cybermap/cybermap_stats.json")
        if file.exists():
            os.remove(file)
    
    def update_type(self, type_of_attack: str, where: str = "types"):
        if hasattr(self, where):
            self.__dict__[where]["TOTAL"] += 1
            if type_of_attack not in self.__dict__[where].keys():
                self.__dict__[where][type_of_attack] = 1
            else:
                self.__dict__[where][type_of_attack] += 1
    
    def update_country(self, country, type_of_attack, direction = "incoming"):
        self.countries["TOTAL"] += 1
        if country in self.countries:
            self.countries[country]["TOTAL"] += 1
            if direction in self.countries[country].keys():
                self.countries[country][direction]["TOTAL"] += 1
                if type_of_attack not in self.countries[country][direction].keys():
                    self.countries[country][direction][type_of_attack] = 1
                else:
                    self.countries[country][direction][type_of_attack] += 1
            else:
                self.countries[country][direction] = dict()
                self.countries[country][direction]["TOTAL"] = 1
                self.countries[country][direction][type_of_attack] = 1
        else:
            self.countries[country] = {"TOTAL": 1}
            self.countries[country][direction] = {type_of_attack: 1, "TOTAL": 1}
    
    def export_stats(self, file: Optional[Union[pathlib.Path, str]] = "cybermap_stats.json", mode: str = "a"):
        if pathlib.Path(file).suffix != ".json":
            raise ValueError
        
        if pathlib.Path(file).is_dir():
            raise ValueError("file argument must be file not a directory")
        
        folder = pathlib.Path("/var/log/cybermap")
        if not folder.exists():
            folder.mkdir()
        
        full_path: pathlib.Path = folder / file
        with full_path.open(mode = mode, encoding = 'utf-8') as f:
            json.dump(self.types, f, ensure_ascii = False, indent = 4, sort_keys = True)


class Proxy(object):
    _logger: logging.Logger
    
    def __init__(
            self,
            redis_ip: Optional[str] = "127.0.0.1",
            redis_port: Optional[int] = 6379,
            database: Optional[Union[str, pathlib.Path]] = None,
            verbose: bool = False,
            silent: bool = False
    ):
        self.options = Options(**{
            "platform": utilities.get_platform(),
            "path_geolite_db": database,
            "redis_ip": redis_ip,
            "redis_port": redis_port,
            "receive_channel": "raw-cyberattacks",
            "forward_channel": "cyberattacks",
            "stats_channel": "cyberstats",
            "verbose": verbose,
            "silent": silent,
            "stats": None,
            "geolite_db": None,
            "redis_watcher": None,
            "redis_pubsub": None,
            "start_time": None,
            "end_time": None,
            "total_time": None
        })
        
        self._logger = utilities.logging.get_console_logger(
            name = _script_stem,
            level = logging.DEBUG if verbose else logging.INFO,
            disable_stream = True if silent else False
        )
        
        # make sure the script is running on a linux machine (windows not supported yet)
        if self.platform.capitalize() != "Linux":
            self._logger.warning(f"{utilities.colorize(self.platform)} is not supported yet.")
            self._logger.warning("The program is only available for Linux machines")
            raise EnvironmentError()
        
        # make sure the script is run as root (or with sudo)
        if os.getuid() != 0:
            self._logger.warning(
                f"Running proxy server as {utilities.colorize('root', color = 'gold_1')} is suggested.")
        
        self.connect_to_database()
        
        try:
            self.redis_watcher = RedisWatcher(ip = redis_ip, port = redis_port, silent = self.silent)
        except redis.exceptions.ExecAbortError:
            self._logger.exception(f"Proxy needs a redis-server to work properly. Aborting execution")
            raise
    
    def send_statistics(self):
        while True:
            attack_types = {k: v for k, v in
                            sorted(self.stats.types.items(), key = lambda item: item[1], reverse = True)}
            countries = dict()
            
            for country_name, obj in self.stats.countries.items():
                if country_name == "TOTAL":
                    countries[country_name] = obj
                    continue
                
                if country_name not in countries.keys():
                    countries[country_name] = dict()
                
                for key in obj.keys():
                    if key == "TOTAL":
                        country_types = obj[key]
                    else:
                        country_types = {k: v for k, v in
                                         sorted(obj[key].items(), key = lambda item: item[1], reverse = True)}
                    
                    countries[country_name][key] = country_types
            
            def sorterer(key):
                if key[0] == "TOTAL":
                    return key[1]
                return key[1]["TOTAL"]
            
            countries = {k: v for k, v in sorted(countries.items(), key = sorterer, reverse = True)}
            
            top_incoming = {k: v["incoming"] for k, v in countries.items() if k != "TOTAL" and "incoming" in v}
            top_incoming = {k: v for k, v in sorted(top_incoming.items(), key = lambda item: item[1]["TOTAL"], reverse = True)}
            top_incoming = {k: top_incoming[k] for k in list(top_incoming)[:5]}

            top_outgoing = {k: v["outgoing"] for k, v in countries.items() if k != "TOTAL" and "outgoing" in v}
            top_outgoing = {k: v for k, v in sorted(top_outgoing.items(), key = lambda item: item[1]["TOTAL"], reverse = True)}
            top_outgoing = {k: top_outgoing[k] for k in list(top_outgoing)[:5]}
            
            data = {
                "types": attack_types,
                "countries": countries,
                "top_incoming": top_incoming,
                "top_outgoing": top_outgoing,
            }
            data = json.dumps(data)
            self.redis_watcher.server.publish(self.stats_channel, data)
            time.sleep(3)
    
    def run(self, *args, **kwargs):
        
        self.stats = ServerStats()
        
        self._logger.info(
            f"Proxy Server started at: "
            f"{utilities.colorize(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), 'gold_1')}"
        )
        self.start_time = timeit.default_timer()
        
        self.redis_pubsub: redis.client.PubSub = self.redis_watcher.server.pubsub()
        self.redis_pubsub.subscribe(self.receive_channel)
        
        # after subscription the main thread launches a periodic task to send data on a stats channel
        thread = threading.Thread(target = self.send_statistics, args = ())
        thread.name = "stats-worker"
        thread.daemon = True  # Daemonize thread
        thread.start()  # Start the execution
        
        self._logger.info(f"Listening on {utilities.colorize(self.receive_channel, 'yellow')} channel")
        
        subscription_msg_received: bool = False
        message = None
        previous_published = False
        total_recv = 0
        wait_interval: float = 5.0  # secs
        while True:
            
            if not self.silent:
                erase_line()
                self._logger.info(f"Waiting for data...")
                print("\033[A\033[53C\033[s", end = '')
                
                for i in utilities.frange(wait_interval, 0, -0.01):
                    sys.stdout.write(f"\033[u[{utilities.colorize(f'{i:.2f}', 'gold_1')}]")
                    sys.stdout.flush()
                    message = self.redis_pubsub.get_message(timeout = 0.01)
                    if message:
                        print(f"\033[u[{utilities.colorize(f'{0:.2f}', 'gold_1')}]")
                        break
            else:
                message = self.redis_pubsub.get_message(timeout = 5)
            
            if message:
                if not message['type'] == "subscribe":
                    data = json.loads(message['data'].decode('utf-8'))
                    
                    if not self.verbose and not self.silent:
                        print("\033[A\033[K", end = '')
                        if total_recv != 0:
                            
                            print("\033[A\033[K", end = '')
                            print("\033[A\033[K", end = '')
                            print("\033[A\033[K", end = '')
                            if previous_published:
                                print("\033[A\033[K", end = '')
                    
                    self._logger.info(
                        f"Received data from {utilities.colorize(self.receive_channel, 'yellow_4a')} message id "
                        f"[{utilities.colorize(total_recv, 'gold_1')}]"
                    )
                    self._logger.debug(f"\n{json.dumps(data, indent = 4)}")
                    
                    src_ip_info = self.get_info_of_ip_from_maxminddb(data['src']['ip'], prefix = "source")
                    dst_ip_info = self.get_info_of_ip_from_maxminddb(data['dst']['ip'], prefix = "destination")
                    
                    if src_ip_info and dst_ip_info:
                        message = {
                            "protocol": data['type'],
                            "src": src_ip_info,
                            "dst": dst_ip_info,
                            "cve": data['cve'],
                            "event_time": utilities.get_time(),
                        }
                        
                        # Track Stats
                        self.stats.update_type(message['protocol'])
                        self.stats.update_country(src_ip_info["country"], message["protocol"], "incoming")
                        self.stats.update_country(dst_ip_info["country"], message["protocol"], "outgoing")
                        self.stats.export_stats()
                        
                        json_data = json.dumps(message)
                        self.redis_watcher.server.publish(self.forward_channel, json_data)
                        self._logger.info(
                            f"Published data to "
                            f"{utilities.colorize(self.forward_channel)} channel"
                        )
                        previous_published = True
                        
                        self._logger.debug(f"\n{json.dumps(message, indent = 4)}")
                        
                        # TODO: Later
                        # self.stats.export_stats()
                    else:
                        previous_published = False
                    
                    total_recv += 1
                else:
                    subscription_msg_received = True
    
    def get_info_of_ip_from_maxminddb(self, ip, prefix = None) -> Optional[Dict]:
        
        if not self.silent:
            setattr(self._logger.handlers[0], 'terminator', '')
            self._logger.info(f"Checking geolocation of {prefix} ip [{ip}]... ")
        
        def clean_ip(ip_info):
            """Create clean dictionary using unclean db dictionary contents"""
            if not ip_info:
                return dict()
            
            selected = {
                "continent": ip_info.get("continent", dict()).get("names", dict()).get("en", None),
                "continent_code": ip_info.get("continent", dict()).get("code", None),
                "country": ip_info.get("country", dict()).get("names", dict()).get("en", None),
                "city": ip_info.get("city", dict()).get("names", dict()).get("en", None),
                "iso_code": ip_info.get("country", dict()).get("iso_code", None),
                "latitude": ip_info.get("location", dict()).get("latitude", None),
                "longitude": ip_info.get("location", dict()).get("longitude", None),
            }
            
            return selected
        
        try:
            unclean_ip_info = self.geolite_db.get(ip)
            self._logger.debug(f"unclean ip info \n{json.dumps(unclean_ip_info, indent = 4)}")
            clean_ip_info = clean_ip(unclean_ip_info)
            if not clean_ip_info.get("latitude") and not clean_ip_info.get("longitude"):
                if not self.silent:
                    print(f"no data found")
                    setattr(self._logger.handlers[0], 'terminator', '\n')
                return None
            
            if not self.silent:
                print("data found")
                setattr(self._logger.handlers[0], 'terminator', '\n')
                self._logger.debug(f"\n{json.dumps(clean_ip_info, indent = 4)}")
            
            return clean_ip_info
        except ValueError:
            self._logger.warning(f"Looked up for an invalid IP address.")
            return None
    
    def connect_to_database(self) -> Optional[maxminddb.reader.Reader]:
        try:
            self.geolite_db: maxminddb.reader.Reader = maxminddb.open_database(
                database = self.path_geolite_db,
                mode = maxminddb.MODE_FILE
            )
        except FileNotFoundError:
            self._logger.warning(f"MaxMind database file: {self.path_geolite_db} could not be found")
            # ask the user to switch to manual IP mode
            if not utilities.confirmation(msg = "Do you want to enable manual IP analysis"):
                self._logger.info("As you wish.")
                raise redis.exceptions.ExecAbortError()
            else:
                self._logger.info("Manual IP analysis initiated")
        except maxminddb.InvalidDatabaseError:
            self._logger.exception(f"MaxMind database {self.path_geolite_db.name} is corrupted or invalidly configured")
            raise
        
        return None
    
    def disconnect_from_database(self):
        self.geolite_db.close()
    
    def shutdown(self):
        if not self.silent and self._logger:
            setattr(self._logger.handlers[0], 'terminator', '\n')
        self._logger.info("Stopping Proxy Server")
        
        if self.redis_watcher:
            self.redis_watcher.disconnect()
        
        if self.geolite_db:
            self.disconnect_from_database()
        
        self._logger.info(f"Proxy Server {utilities.colorize('successfully', 'gold_1')} stopped")
        
        self.end_time = timeit.default_timer()
        
        if self.start_time:
            without_microseconds, microseconds = str(
                datetime.timedelta(seconds = self.end_time - self.start_time)).split(".")
            microseconds = microseconds[:-3]
            self.total_time = f"{without_microseconds}.{microseconds}"
            
            self._logger.info(
                "Total time online: "
                f"{utilities.colorize(f'{self.total_time}', color = 'gold_1')}"
            )  # Time in days, hours:minutes:seconds.milliseconds format
            
            self._logger.info(
                "Total IPs published "
                f"{utilities.colorize(self.stats.types['TOTAL'], 'gold_1')}"
            )
    
    def wait_counter(self):
        pass
    
    def __del__(self):
        if not self.silent and not self.verbose:
            erase_line()
        self.shutdown()
    
    # region Getters & Setters
    def update_options(self, **kwargs):
        self.options.set(**kwargs)
    
    @property
    def geolite_db(self):
        return self.options.geolite_db
    
    @geolite_db.setter
    def geolite_db(self, value):
        self.update_options(geolite_db = value)
    
    @property
    def platform(self):
        return self.options.platform
    
    @property
    def redis_watcher(self):
        return self.options.redis_watcher
    
    @redis_watcher.setter
    def redis_watcher(self, value):
        self.update_options(redis_watcher = value)
    
    @property
    def redis_pubsub(self):
        return self.options.redis_pubsub
    
    @redis_pubsub.setter
    def redis_pubsub(self, value):
        self.update_options(redis_pubsub = value)
    
    @property
    def start_time(self):
        return self.options.start_time
    
    @start_time.setter
    def start_time(self, value):
        self.update_options(start_time = value)
    
    @property
    def end_time(self):
        return self.options.end_time
    
    @end_time.setter
    def end_time(self, value):
        self.update_options(end_time = value)
    
    @property
    def receive_channel(self):
        return self.options.receive_channel
    
    @receive_channel.setter
    def receive_channel(self, value):
        self.update_options(receive_channel = value)
    
    @property
    def forward_channel(self):
        return self.options.forward_channel
    
    @forward_channel.setter
    def forward_channel(self, value):
        self.update_options(forward_channel = value)
    
    @property
    def stats_channel(self):
        return self.options.stats_channel
    
    @stats_channel.setter
    def stats_channel(self, value):
        self.update_options(stats_channel = value)
    
    @property
    def path_geolite_db(self):
        return self.options.path_geolite_db
    
    @path_geolite_db.setter
    def path_geolite_db(self, value):
        self.update_options(path_geolite_db = value)
    
    @property
    def total_time(self):
        return self.options.total_time
    
    @total_time.setter
    def total_time(self, value):
        self.update_options(total_time = value)
    
    @property
    def verbose(self):
        return self.options.verbose
    
    @verbose.setter
    def verbose(self, value):
        self.update_options(verbose = value)
    
    @property
    def silent(self):
        return self.options.silent
    
    @silent.setter
    def silent(self, value):
        self.update_options(silent = value)
    
    @property
    def stats(self):
        return self.options.stats
    
    @stats.setter
    def stats(self, value: ServerStats):
        self.update_options(stats = value)
    
    # endregion


def validate_ip(ctx, param, value: str):
    if value.lower() == "localhost":
        return "127.0.0.1"
    
    # Validate IPv4 or IPv6 address as described here https://www.regexpal.com/?fam=104038
    pattern = re.search(
        r"((^\s*((([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))\s*$)|(^\s*((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,4}|((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,3})|((:[0-9A-Fa-f]{1,4})?:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|((:[0-9A-Fa-f]{1,4}){0,2}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})|((:[0-9A-Fa-f]{1,4}){0,3}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){1}(((:[0-9A-Fa-f]{1,4}){1,6})|((:[0-9A-Fa-f]{1,4}){0,4}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(:(((:[0-9A-Fa-f]{1,4}){1,7})|((:[0-9A-Fa-f]{1,4}){0,5}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:)))(%.+)?\s*$))",
        value
    )
    if not pattern:
        raise click.BadParameter(f"'{value}' is NOT a valid IPv4 or IPv6 address")
    
    return pattern.group(1)


# region Click Options
# region command settings
@click.command(
    cls = HelpColorsCommand,
    help_headers_color = 'green',
    help_options_color = 'red',
    name = "Proxy",
    context_settings = {
        "help_option_names": ['-h', '--help', '?'],
        "ignore_unknown_options": True
    },
    no_args_is_help = False,
    options_metavar = "<options>"
)
# endregion
# region redis-ip option
@click.option(
    "--redis-ip",
    default = "127.0.0.1",
    type = click.STRING,
    metavar = "<string>",
    callback = validate_ip,
    help = "Redis-server IP"
)
# endregion
# region redis-port option
@click.option(
    "--redis-port",
    default = 6379,
    metavar = "<integer>",
    type = click.IntRange(1024, 49151),
    help = "Redis-server port (range is 1024 - 49151)"
)
# endregion
# region db option
@click.option(
    "-db",
    "--database",
    type = click.Path(
        file_okay = True,
        dir_okay = False
    ),
    metavar = "<File Path>",
    default = _script_path.parent.joinpath("databases/GeoLite2-City.mmdb"),
    help = "Path to maxmind database"
)
# endregion
# region logs option
@click.option(
    "-l",
    "--logs",
    type = click.Path(
        file_okay = False,
        dir_okay = True,
    ),
    metavar = "<File Path>",
    default = pathlib.Path("logs"),
    help = "Path to store log files"
)
# endregion
# region verbose option
@click.option(
    "--verbose",
    metavar = "<boolean>",
    is_flag = True,
    help = "Enables verbose logging messages"
)
# endregion
# region silent option
@click.option(
    "--silent",
    metavar = "<boolean>",
    is_flag = True,
    help = "Disables ALL logging messages"
)
# endregion
# region demo option
@click.option(
    "--demo",
    metavar = "<switch>",
    is_flag = True,
    help = "Disables ALL logging messages"
)
# endregion
@click.pass_context
# endregion
def main(ctx, redis_ip: str, redis_port: int, database: pathlib.Path, logs: pathlib.Path, verbose: bool, silent: bool,
         demo: bool):
    try:
        if demo:
            generator = AttacksGenerator(
                silent = True
            )
            
            thread = threading.Thread(target = generator, args = ())
            thread.daemon = True  # Daemonize thread
            thread.start()  # Start the execution
        
        proxy: Proxy = Proxy(
            redis_ip = redis_ip,
            redis_port = redis_port,
            database = database,
            verbose = verbose,
            silent = silent
        )
        proxy.run()
    except redis.exceptions.ExecAbortError:
        exit(0)


if __name__ == '__main__':
    main()
