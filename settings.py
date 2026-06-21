import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-drdo-kb-change-in-production-xyz-123'

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'knowledge_base',
    'crawler',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'drdo_kb.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'drdo_kb.wsgi.application'

# --- Database: SQLite (easy to swap to PostgreSQL) ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'drdo_knowledge_base.db',
    }
}

# --- PostgreSQL (uncomment & fill to use instead) ---
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': os.environ.get('DB_NAME', 'drdo_kb'),
#         'USER': os.environ.get('DB_USER', 'postgres'),
#         'PASSWORD': os.environ.get('DB_PASSWORD', ''),
#         'HOST': os.environ.get('DB_HOST', 'localhost'),
#         'PORT': os.environ.get('DB_PORT', '5432'),
#     }
# }

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Crawler Settings ---
CRAWLER_OUTPUT_DIR = BASE_DIR / 'crawler_output'
RAW_JSON_DIR = BASE_DIR / 'crawler_output' / 'raw'
CLEAN_JSON_DIR = BASE_DIR / 'crawler_output' / 'clean'

DRDO_BASE_URL = 'https://www.drdo.gov.in'
CRAWLER_DELAY = 1.5          # seconds between requests (be respectful)
CRAWLER_MAX_PAGES = 500      # cap to avoid infinite crawls
CRAWLER_TIMEOUT = 30         # seconds per request
CRAWLER_USER_AGENT = (
    'DRDO-KnowledgeBase-Crawler/1.0 '
    '(Academic/Internship Project; +https://www.drdo.gov.in)'
)

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'verbose'},
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'crawler.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'crawler': {'handlers': ['console', 'file'], 'level': 'INFO', 'propagate': False},
        'knowledge_base': {'handlers': ['console', 'file'], 'level': 'INFO', 'propagate': False},
    },
}
