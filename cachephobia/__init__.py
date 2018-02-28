VERSION = (0, 1)
__version__ = '.'.join(map(str, VERSION if VERSION[-1] else VERSION[:2]))


from .query import *
from .behavior import *
from .redis import cache
from .decorators import *
