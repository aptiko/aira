import os

SECRET_KEY = "topsecret"
DEBUG = False
SITE_ID = 1


ALLOWED_HOSTS = []


INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.flatpages",
    "django.contrib.gis",
    "aira",
    "registration",
    "django.contrib.admin",
    "bootstrap4",
    "mathfilters",
    "captcha",
]


MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "aira.middleware.PermissionsMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

CACHES = {"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}

ROOT_URLCONF = "aira_project.urls"
WSGI_APPLICATION = "aira_project.wsgi.application"

DATABASES = {}
LANGUAGE_CODE = "en-us"
LANGUAGES = (("en", "English"), ("el", "Greek"))
TIME_ZONE = "Europe/Athens"
USE_I18N = True
USE_L10N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

STATIC_URL = "/static/"


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
                "aira.context_processors.map",
            ]
        },
    }
]

ACCOUNT_ACTIVATION_DAYS = 3
LOGIN_REDIRECT_URL = "/my_fields/"

AIRA_DATA_HISTORICAL = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../rasters_historical")
)

AIRA_DATA_FORECAST = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../rasters_forecast")
)

AIRA_DATA_SOIL = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../rasters_soil")
)

AIRA_TIMESERIES_CACHE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../timeseries_cache")
)

AIRA_MAPSERVER_BASE_URL = "/mapserver/"

AIRA_MAP_DEFAULT_CENTER = (20.98, 39.15)
AIRA_MAP_DEFAULT_ZOOM = 10

AIRA_EMAIL_HEADER = ""
AIRA_EMAIL_FOOTER = ""

CELERY_TASK_SERIALIZER = "pickle"
CELERY_ACCEPT_CONTENT = ["pickle"]
AIRA_CELERY_SEND_TASK_ERROR_EMAILS = False

if os.environ.get("SELENIUM_BROWSER", False):
    from selenium import webdriver

    SELENIUM_WEBDRIVERS = {
        "default": {
            "callable": webdriver.__dict__[os.environ["SELENIUM_BROWSER"]],
            "args": (),
            "kwargs": {},
        }
    }

AIRA_THE_THINGS_NETWORK_ACCESS_KEY = ""
AIRA_THE_THINGS_NETWORK_BASE_URL = ""
