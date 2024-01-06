import sys
from datetime import timedelta
from pathlib import Path
import environ
from django.conf import settings

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve(strict=True).parent.parent.parent
APPS_DIR = BASE_DIR / "AfanChatServer"

# 环境变量
# ------------------------------------------------------------------------------
env = environ.Env()
READ_DOT_ENV_FILE = env.bool("DJANGO_READ_DOT_ENV_FILE", default=True)
if READ_DOT_ENV_FILE:
    # OS environment variables take precedence over variables from .env
    if 'local' in settings.SETTINGS_MODULE:
        env.read_env(str(BASE_DIR / ".envs" / '.local'))
    else:
        env.read_env(str(BASE_DIR / ".envs" / '.production'))
# 常规配置
# ------------------------------------------------------------------------------
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DJANGO_DEBUG", False)
# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/
LANGUAGE_CODE = "zh-Hans"

TIME_ZONE = "Asia/Shanghai"

DOMAIN = env.str("DOMAIN", "localhost:8000")

USE_I18N = True

USE_TZ = True

LOCALE_PATHS = [str(BASE_DIR / "locale")]

# Database
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    "default": env.db("DATABASE_URL", default="sqlite:///{}".format(BASE_DIR / "db.sqlite3")),
}
DATABASES["default"]["ATOMIC_REQUESTS"] = True  # 将HTTP请求封装到事务
# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# URLS
# ------------------------------------------------------------------------------
ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# APPS
# ------------------------------------------------------------------------------
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',

    "daphne",

    'django.contrib.staticfiles',
]
THIRD_PARTY_APPS = [
    "channels",
    'ninja_extra',
    # 'django_rest_passwordreset',
    # 'corsheaders'
    'ninja_jwt',
    "django_celery_beat",
    "django_celery_results",
]

LOCAL_APPS = [
    'users',
    "contacts",
    "chat",

]
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# MIGRATIONS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#migration-modules
MIGRATION_MODULES = {"sites": "AfanChatServer.contrib.sites.migrations"}

# AUTHENTICATION
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-user-model
AUTH_USER_MODEL = 'users.CustomUser'

# Password validation
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# MIDDLEWARE
# ------------------------------------------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# SECURITY WARNING: keep the secret key used in production secret!
# ------------------------------------------------------------------------------

SECRET_KEY = env.str("DJANGO_SECRET_KEY", default='django-insecure-^ga@7%5lnh@)_a*v!0&g)tbrf-2r2p*t%hei$bf%drp*)wj8f_')

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["*"])

# TEMPLATES
# ------------------------------------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [APPS_DIR / "static"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',

            ],
        },
    },
]

# Static files (CSS, JavaScript, Images)
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/4.2/howto/static-files/
STATIC_URL = 'static/'

# NINJA_JWT
# ------------------------------------------------------------------------------
NINJA_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=10),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
}

# Celery
# ------------------------------------------------------------------------------
# celery时区设置，建议与Django settings中TIME_ZONE同样时区，防止时差
# Django设置时区需同时设置USE_TZ=True和TIME_ZONE = 'Asia/Shanghai'
if USE_TZ:
    # https://docs.celeryq.dev/en/stable/userguide/configuration.html#std:setting-timezone
    CELERY_TIMEZONE = TIME_ZONE
# https://docs.celeryq.dev/en/stable/userguide/configuration.html#std:setting-broker_url
# 最重要的配置，设置消息broker,格式为：db://user:password@host:port/dbname
# 如果redis安装在本机，使用localhost
# 如果docker部署的redis，使用redis://redis:6379
CELERY_BROKER_URL = env.str("CELERY_BROKER_URL", default="redis://localhost:6379/0")
# https://docs.celeryq.dev/en/stable/userguide/configuration.html#std:setting-result_backend
# 为django_celery_results存储Celery任务执行结果设置后台
# 格式为：db+scheme://user:password@host:port/dbname
# 支持数据库django-db和缓存django-cache存储任务状态及结果
CELERY_RESULT_BACKEND = env.str("CELERY_RESULT_BACKEND", default="django-db")
# https://docs.celeryq.dev/en/stable/userguide/configuration.html#result-extended
# 设置为True，支持任务结果的序列化和反序列化
CELERY_RESULT_EXTENDED = True
# https://docs.celeryq.dev/en/stable/userguide/configuration.html#result-backend-always-retry
# https://github.com/celery/celery/pull/6122
# 设置为True，即使任务结果失败也会重试
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
# https://docs.celeryq.dev/en/stable/userguide/configuration.html#result-backend-max-retries
# 设置任务结果最大重试次数
CELERY_RESULT_BACKEND_MAX_RETRIES = 10
# https://docs.celeryq.dev/en/stable/userguide/configuration.html#std:setting-accept_content
# 设置接受的内容类型
CELERY_ACCEPT_CONTENT = ['application/json']
# https://docs.celeryq.dev/en/stable/userguide/configuration.html#std:setting-task_serializer
# 设置任务序列化器
CELERY_TASK_SERIALIZER = 'json'
# https://docs.celeryq.dev/en/stable/userguide/configuration.html#std:setting-result_serializer
# 设置任务结果序列化器
CELERY_RESULT_SERIALIZER = 'json'
# https://docs.celeryq.dev/en/stable/userguide/configuration.html#task-time-limit
# 设置任务执行时间限制，超过此限制任务将被强制中止。
CELERY_TASK_TIME_LIMIT = 5 * 60
# https://docs.celeryq.dev/en/stable/userguide/configuration.html#task-soft-time-limit
# 设置任务软时间限制，超过此限制任务将收到一个软中止信号。
CELERY_TASK_SOFT_TIME_LIMIT = 60
# https://docs.celeryq.dev/en/stable/userguide/configuration.html#beat-scheduler
# 设置定时任务调度器，用了 Django Celery Beat 提供的 DatabaseScheduler，该调度器将调度信息存储在数据库中。
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
# https://docs.celeryq.dev/en/stable/userguide/configuration.html#worker-send-task-events
# 设置Celery worker发送任务事件，可以用于监控任务的执行情况。
CELERY_SEND_TASK_EVENTS = True
# https://docs.celeryq.dev/en/stable/userguide/configuration.html#std-setting-task_send_sent_event
# 设置任务发送事件，表示启用任务发送 "sent" 事件，以便能够在任务发送时接收通知。
CELERY_TASK_SEND_SENT_EVENT = True

CELERY_TASK_DEFAULT_QUEUE = 'default'
CELERY_QUEUES = [
    {"name": "default", "exchange": "default", "routing_key": "default"},
    {"name": "send_message_queue", "exchange": "send_message_queue", "routing_key": "send_message_queue"},
    {"name": "single_process_queue", "exchange": "single_process_queue", "routing_key": "single_process_queue"},
]
CELERY_TASK_ROUTES = {
    'users.tasks.send_message_all_async': {'queue': 'send_message_queue'},
    'users.tasks.refresh_ip_detail_async': {'queue': 'single_process_queue'},
}