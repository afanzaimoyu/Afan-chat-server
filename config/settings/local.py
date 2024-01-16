from .base import *  # noqa
from .base import env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = True
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="shqfr08LEXFYzi3zGQIGTTZZDoD1jGQOcLN97yd4RHXz3ZsRk5VtcZeuVlYk0EIr",
)
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ["*"]

# CHANNEL
# ------------------------------------------------------------------------------

# CHANNEL_LAYERS = {
#     "default": {
#         "BACKEND": "channels.layers.InMemoryChannelLayer"
#     }
# }
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [f"{env.str('REDIS_URL')}/0"],
        },
    },
}
# CACHES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#caches
DEFAULT_CACHE_CONFIG = {
    'BACKEND': 'django.core.cache.backends.redis.RedisCache',
    'LOCATION': f"{env.str('REDIS_URL')}/0",
    'OPTIONS': {
        'parser_class': 'redis.connection._HiredisParser',
        'pool_class': 'redis.ConnectionPool',
    }
}


def create_cache_config(key_prefix, db=0):
    config = DEFAULT_CACHE_CONFIG.copy()
    config['KEY_PREFIX'] = key_prefix
    config['LOCATION'] = f"{env.str('REDIS_URL')}/{db}"
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
