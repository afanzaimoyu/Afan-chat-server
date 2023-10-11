import sys
from pathlib import Path
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve(strict=True).parent.parent.parent
APPS_DIR = BASE_DIR / "AfanChatServer"

# 环境变量
# ------------------------------------------------------------------------------
env = environ.Env()
READ_DOT_ENV_FILE = env.bool("DJANGO_READ_DOT_ENV_FILE", default=True)
if READ_DOT_ENV_FILE:
    # OS environment variables take precedence over variables from .env
    env.read_env(str(BASE_DIR / ".env"))

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

# APPS
# ------------------------------------------------------------------------------
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]
THIRD_PARTY_APPS = [
    # 'ninja_extra',
    # 'django_rest_passwordreset',
    # 'corsheaders'
    # # 'ninja_jwt'
]

LOCAL_APPS = [

]
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# MIGRATIONS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#migration-modules
MIGRATION_MODULES = {"sites": "AfanChatServer.contrib.sites.migrations"}

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
