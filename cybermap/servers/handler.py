# encoding: utf-8
import uuid
from pprint import pprint
from typing import Optional, List, Dict, Any, Union, Set

import tornado.web
import tornado.escape
import tornado.ioloop
import tornado.gen
import tornado.concurrent
from tornado.ioloop import PeriodicCallback

import time
import json
import hashlib
import logging

import aioredis
import aioredis.pubsub

from tornado.httputil import HTTPConnection


logger = logging.getLogger()

CHANNEL = 'cyberattacks'
STATS_CHANNEL = 'cyberstats'


class SSEHandler(tornado.web.RequestHandler):
    # class items
    cache = list()
    cache_limit = 200
    redis_pool: aioredis.Redis = None
    online_clients: Dict[str, Any] = dict()
    
    
    def initialize(self):
        self.con_id: str = hashlib.md5(f"{self.request.remote_ip}-{time.time()}".encode()).hexdigest()
        self.channels_names = ['cyberattacks', 'cyberstats']
        self.aioredis_channels: List[aioredis.Channel] = list()
        self.set_sse_headers()
    
    def set_sse_headers(self):
        self.set_header("Content-Type", "text/event-stream")
        self.set_header("Cache-Control", "no-cache")
        self.set_header("Connection", "keep-alive")
        self.set_header("Access-Control-Allow-Origin", "*")
    
    async def get(self, *args, **kwargs):
        if not self.channels_names:
            self.set_status(403)
            await self.finish()
        else:
            await self.on_open(*args, **kwargs)
    
    async def on_open(self, *args, **kwargs):
        """ Invoked for a new connection opened. """
        logger.info(
            f"New /events incoming connection with id {self.con_id} for channels [{', '.join(self.channels_names)}]")
        
        self.online_clients[self.con_id] = self
        
        if not self.redis_pool:
            try:
                # This is the IP address of the Proxy
                self.redis_pool = await aioredis.create_redis_pool(address = ("127.0.0.1", 6379))
            except Exception:
                logger.exception("Could not connect to Redis server.")
                raise
        
        event_id = self.request.headers.get('Last-Event-ID', None)
        if event_id:
            pass
        
        await self.subscribe()
    
    async def subscribe(self):
        self.receiver = aioredis.pubsub.Receiver()
        for channel in self.channels_names:
            ch: aioredis.Channel = self.receiver.channel(name = channel)
            await self.redis_pool.subscribe(ch)
            self.aioredis_channels.append(ch)
        
        logger.info(
            f"[CLIENT {self.con_id}] is listening for messages in channels [{','.join(self.channels_names)}]")
        async for channel, msg in self.receiver.iter():
            assert isinstance(channel, aioredis.pubsub.AbcChannel)
            sse = None
            msg_id = str(uuid.uuid4())
            decoded = msg.decode("utf-8")
            channel_name = channel.name.decode("utf-8")
            if channel_name == "cyberattacks":
                sse = f"\n" \
                      f"event: message\n" \
                      f"data: {decoded}\n" \
                      f"id: {msg_id}\n" \
                      f"\n"
                
                if len(self.cache) > self.cache_limit:
                    self.cache = self.cache[-self.cache_limit:]
                
                self.cache.append({
                    'id': msg_id,
                    'channel': channel,
                    'body': sse,
                })
            elif channel_name == "cyberstats":
                sse = f"\n" \
                      f"event: stats\n" \
                      f"data: {decoded}\n" \
                      f"id: {msg_id}\n" \
                      f"\n"
            if sse:
                self.send_message(sse)
    
    async def unsubscribe(self):
        for ch in self.aioredis_channels:
            await self.redis_pool.unsubscribe(ch)
        self.redis_pool.close()
        logger.info("redis pool unsubscribe success")
    
    def send_message(self, message):
        self.write(message)
        self.flush()
    
    @classmethod
    def send_to_all(cls):
        """ Sends a message to all live connections """
        for connection in cls.online_clients.values():
            connection.send_message()
    
    def on_connection_close(self):
        """ Closes the connection for this instance """
        logger.info('Connection %s is closed' % self.con_id)
        
        del self.online_clients[self.con_id]
        
        tornado.ioloop.IOLoop.current().add_callback(self.unsubscribe)
        
        
        self.request.connection.finish()
