import logging

from .base import *  # noqa
from .base import env

DEBUG = True
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["*"])
SECRET_KEY = env.str("DJANGO_SECRET_KEY", default='django-insecure-^ga@7%5lnh@)_a*v!0&g)tbrf-2r2p*t%hei$bf%drp*)wj8f_')

# CHANNEL
# ------------------------------------------------------------------------------
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": env.str("CHANNEL_LAYERS_BACKEND", default="channels_redis.core.InMemoryChannelLayer"),
        "CONFIG": {
            "hosts": [env.str('REDIS_URL', None)],
        },
    },
}
# CACHES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#caches
DEFAULT_CACHE_CONFIG = {
    'BACKEND': 'django.core.cache.backends.redis.RedisCache',
    'LOCATION': env.str('REDIS_URL'),
    'OPTIONS': {
        'parser_class': 'redis.connection._HiredisParser',
        'pool_class': 'redis.ConnectionPool',
    }
}


def create_cache_config(key_prefix):
    config = DEFAULT_CACHE_CONFIG.copy()
    config['KEY_PREFIX'] = key_prefix
    return config


CACHES = {
    'default': create_cache_config(key_prefix='default:'),
    'item_cache': create_cache_config(key_prefix='item:'),
}

# # django-debug-toolbar
# # ------------------------------------------------------------------------------
# # https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#prerequisites
# INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
# # https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#middleware
# MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]  # noqa: F405
# # https://django-debug-toolbar.readthedocs.io/en/latest/configuration.html#debug-toolbar-config
# DEBUG_TOOLBAR_CONFIG = {
#     "DISABLE_PANELS": ["debug_toolbar.panels.redirects.RedirectsPanel"],
#     "SHOW_TEMPLATE_CONTEXT": True,
# }
# # https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#internal-ips
# INTERNAL_IPS = ["127.0.0.1", "10.0.2.2"]
# if env("USE_DOCKER") == "yes":
#     import socket
#
#     hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
#     INTERNAL_IPS += [".".join(ip.split(".")[:-1] + ["1"]) for ip in ips]
#     try:
#         _, _, ips = socket.gethostbyname_ex("node")
#         INTERNAL_IPS.extend(ips)
#     except socket.gaierror:
#         # The node container isn't started (yet?)
#         pass
#
# Log
# ------------------------------------------------------------------------------
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {'format': '[%(asctime)s] [%(filename)s:%(lineno)d] [%(module)s:%(funcName)s] [%(levelname)s]- %('
                               'message)s'},
        'simple': {'format': '%(levelname)s %(message)s'},
    },
    'handlers': {
        'servers': {
            'class': 'utils.log.LoguruStreamHandler',  # 这个路径看你本地放在哪里(下面的log文件)
            'filename': Path('server.log'),
            'formatter': 'standard',
        },
        'db': {
            'class': 'utils.log.LoguruStreamHandler',
            'filename': Path('db.log'),
            'formatter': 'standard',
            'logging_levels': ['debug']  # 😒注意这里，这是自定义类多了一个参数，因为我只想让db日志有debug文件，所以我只看sql，这个可以自己设置
        }
    },
    'loggers': {
        # Django全局绑定
        '': {
            'handlers': ['servers'],
            'propagate': True,
            'level': "INFO"
        },
        'django.db.backends': {
            'handlers': ['db'],
            'propagate': False,
            'level': "DEBUG"
        }
    }
}

