from rest_framework.response import Response
from functools import wraps
from hashlib import md5
from inspect import getsource
import ujson as json
from .conf import settings
from .redis import cache


def cachephobic_api(**kwargs):
    '''
    Cache Rest Framework APIView methods (without invalidation)
    Allowed only GET method.
    Cached only HTTP status code = 200.
    '''

    timeout = kwargs.pop('timeout', settings.CACHEPHOBIA_DEFAULTS['timeout'])
    debug = kwargs.pop('debug', settings.CACHEPHOBIA_DEBUG)
    request_attr = kwargs.pop('request_attr', 'GET')

    if kwargs:
        raise TypeError('Unexpected keyword arguments %s' % ', '.join(kwargs))

    def hash_api(func, instance, request, debug=False):
        factors = [
            func.__module__,
            instance.__class__.__name__,
            func.__name__,
            request.method,
            getattr(request, request_attr)
        ]

        if debug:
            factors.append(getsource(func))
            factors.append(getsource(cachephobic_api))

        return md5(json.dumps(factors, sort_keys=True)).hexdigest()

    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            if not settings.CACHEPHOBIA_ENABLED:
                return func(self, request, *args, **kwargs)

            if request.method != 'GET':
                raise Exception('Only GET method can be cached')

            key = 'cp:api:' + hash_api(func, self, request, debug=debug)
            cached = cache.get(key)
            if cached is not None:
                data = json.loads(cached)
                return Response(data, status=200)
            else:
                response = func(self, request, *args, **kwargs)
                if response.status_code == 200:
                    cache.set(key, json.dumps(response.data), timeout)
                return response

        return wrapper
    return decorator
