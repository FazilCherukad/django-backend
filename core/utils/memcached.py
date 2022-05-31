import json
from pymemcache.client.base import Client
from config import (
    MEMCACHED_LOCATION
)

class JsonSerde(object):
    def serialize(self, key, value):
        if isinstance(value, str):
            return value, 1
        return json.dumps(value), 2

    def deserialize(self, key, value, flags):
       if flags == 1:
           return value
       if flags == 2:
           return json.loads(value)
       raise Exception("Unknown serialization format")

client = Client(MEMCACHED_LOCATION, serde=JsonSerde(), connect_timeout=1000, timeout=1000)