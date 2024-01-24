from django.utils import timezone

from config.settings.base import *

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")
SECRET_KEY = env.str("DJANGO_SECRET_KEY")

SECURE_SSL_REDIRECT = True
SECURE_CONTENT_TYPE_NOSNIFF = True

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
