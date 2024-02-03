from django.utils import timezone

from config.settings.base import *

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")
SECRET_KEY = env.str("DJANGO_SECRET_KEY")

# SECURE_SSL_REDIRECT = True
SECURE_CONTENT_TYPE_NOSNIFF = True
# CORS
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_HEADERS = ('*')
# CORS_ALLOWED_ORIGINS = [
#     'https://www.afanchat.cn',
#     'https://afanchat.cn',
#     'https://minio.afanchat.cn',
#     'https://api.afanchat.cn',
#     # Add more origins if needed
# ]
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
    "TIMEOUT": None,
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

# Log
# ------------------------------------------------------------------------------
PRODUCTION_LOG_ROOT = LOG_ROOT / 'production_log'

# 检查文件夹是否存在，如果不存在则创建
PRODUCTION_LOG_ROOT.mkdir(parents=True, exist_ok=True)
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
            'class': 'utils.log.InterceptTimedRotatingFileHandler',  # 这个路径看你本地放在哪里(下面的log文件)
            'filename': PRODUCTION_LOG_ROOT / 'server.log',
            'when': "W",
            'interval': 1,
            'formatter': 'standard',
            'encoding': 'utf-8',
        },
        'db': {
            'class': 'utils.log.InterceptTimedRotatingFileHandler',
            'filename': PRODUCTION_LOG_ROOT / 'db.log',
            'when': "W",
            'interval': 1,
            'formatter': 'standard',
            'encoding': 'utf-8',
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
