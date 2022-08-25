import os
import dj_database_url

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# SECURITY WARNING: keep the secret key used in production secret!
DEFAULT_SECRET_KEY = 'mj4%3@87asupersecretdefaultkey90sd_$f8907a)*'
SECRET_KEY = os.environ.get('SECRET_KEY', DEFAULT_SECRET_KEY)

DEBUG = False
TEMPLATE_DEBUG = False
ALLOWED_HOSTS = ['*'] #TODO: change this once we have a domain
ROOT_URLCONF = 'membot.config.base.urls'
WSGI_APPLICATION = 'membot.config.base.wsgi.application'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'membot.apps.membot',
    'corsheaders',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

# CORS
CORS_ORIGIN_WHITELIST = tuple(os.environ['ALLOWED_MESSAGE_HOSTS'].split(','))

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/Chicago'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/
STATIC_URL = '/static/'
STATIC_ROOT = 'staticfiles'
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)


ADMINS = (
    ('Ryan Pitts', 'ryan.a.pitts@gmail.com'),
)
MANAGERS = ADMINS
