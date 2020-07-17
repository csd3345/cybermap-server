import os
from copy import deepcopy

import redis
import socket
import uuid

from options import Options
from typing import Optional, Any, Dict, List, Type

from .colors import colorize
from .logging import get_console_logger
from .platform import confirmation

from redis.exceptions import ExecAbortError


class RedisWatcher(object):
    
    active_watchers: Dict[int, Any] = dict()
    active_services: List[Any] = list()
    IDs: List[int] = list()
    
    class Service(object):
        
        def __init__(self, host: str, port: int):
            self.host = host
            self.port = port
        
        def __eq__(self, other):
            if not isinstance(other, RedisWatcher.Service):
                # don't attempt to compare against unrelated types
                return NotImplemented
            return self.host == other.host and self.port == other.port
        
        def __str__(self):
            return f"{colorize(f'{self.host}:{self.port}', color = 'gold_1')}"
    
    def __init__(
            self,
            ip: Optional[str] = "127.0.0.1",
            port: Optional[int] = 6379,
            silent: Optional[bool] = False
    ):
        unique_id: int = int(str(uuid.uuid4().int)[:-29])  # make a completely random UUID
        if unique_id in self.IDs:
            raise Exception(f"ID {unique_id} already exists for a RedisWatcher instance. Something went wrong")

        self._logger = get_console_logger(name = f"RedisWatcher-{unique_id}", disable_stream = True if silent else False)
        
        self.options: Options = Options(**{
            "ip": ip,
            "port": port,
            "id": unique_id
        })
        
        if not self.start_service(autostart = True):
            raise ExecAbortError()

        self.server: Optional[redis.client.Redis] = self.connect()
        self.IDs.append(unique_id)
        self.active_watchers[unique_id] = self
        self._logger.info(f"Watcher created for {self}")
    
    def connect(self) -> redis.Redis:
        try:
            server = redis.Redis(
                host = self.ip,
                port = self.port,
                db = 0,
                health_check_interval = 0
            )
            return server
        except redis.exceptions.RedisError:
            self._logger.exception(
                f"Something went while connecting to redis server {self.options.ip}:{self.options.port}"
            )
            raise
    
    def disconnect(self) -> Optional[bool]:
        try:
            self.server.close()
        except socket.error:
            return None
        return True
    
    def start_service(self, autostart: bool = True) -> Optional[bool]:
        """
        Start the Redis Server (on linux) if it isn't already running.
        Make sure system can use a lot of memory and overcommit memory
        """
        try:
            connection = redis.Connection(
                host = self.ip,
                port = self.port,
                db = 0,
                health_check_interval = 5
            )
            connection.check_health()
            connection.disconnect()
        except redis.ConnectionError:
            self._logger.warning("Redis Server is not currently active")
            if not autostart:
                if not confirmation(msg = "Do you want to enable redis-server now"):
                    self._logger.info("As you wish.")
                    raise ExecAbortError()
            
            self._logger.info("Starting")
            # because we are surely on a linux system we can use directly os.system() command
            if os.system("service redis-server start") == 0:  # service started
                self._logger.info(f"Started {colorize('successfully', 'gold_1')}")
            else:
                self._logger.critical("Redis server could not be started.")
                self._logger.warning("If this was due to root permissions please use sudo or login as root")
                return None
        
        service = RedisWatcher.Service(self.ip, self.port)
        
        if service not in self.active_services:
            self._logger.info(f"Redis Server {service} is {colorize('live')}")
            self.active_services.append(service)
        
        return True
    
    def update_options(self, **kwargs):
        self.options.set(**kwargs)
    
    def __str__(self):
        return f"{colorize(self.id, color = 'sky_blue_1')} -> {colorize(f'{self.ip}:{self.port}', color = 'gold_1')}"
    
    def __repr__(self):
        return f"{self.ip}:{self.port}"
    
    # region Getters & Setters
    @property
    def ip(self):
        return self.options.ip
    
    @ip.setter
    def ip(self, value):
        self.update_options(ip = value)
    
    @property
    def port(self):
        return self.options.port
    
    @port.setter
    def port(self, value):
        self.update_options(port = value)
    
    @property
    def id(self):
        return self.options.id
    
    @id.setter
    def id(self, value):
        self.update_options(id = value)
    
    # endregion
