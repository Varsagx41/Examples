from django.conf import settings as base_settings
import logging


class Settings(object):
    CACHEPHOBIA_ENABLED = True
    CACHEPHOBIA_DEBUG = False
    CACHEPHOBIA_REDIS = {}
    CACHEPHOBIA_DEFAULTS = {
        'timeout': 60 * 60,
    }

    def __getattribute__(self, name):
        if hasattr(base_settings, name):
            return getattr(base_settings, name)
        return object.__getattribute__(self, name)


settings = Settings()

logger = logging.getLogger('cachephobia')
