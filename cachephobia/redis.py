from __future__ import absolute_import
import six
import redis
from .conf import settings


class LazyRedis(object):
    def _setup(self):
        if isinstance(settings.CACHEPHOBIA_REDIS, six.string_types):
            client = redis.StrictRedis.from_url(settings.CACHEPHOBIA_REDIS)
        else:
            client = redis.StrictRedis(**settings.CACHEPHOBIA_REDIS)

        object.__setattr__(self, '__class__', client.__class__)
        object.__setattr__(self, '__dict__', client.__dict__)

    def __getattr__(self, name):
        self._setup()
        return getattr(self, name)

    def __setattr__(self, name, value):
        self._setup()
        return setattr(self, name, value)


cache = LazyRedis()
