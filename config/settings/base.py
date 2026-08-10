"""
Configurações base do Sistema Escolar Demo.

Todas as configurações sensíveis ou que variam por ambiente vêm de variáveis
de ambiente (arquivo .env em desenvolvimento) — nunca hardcoded aqui.
"""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
env_file = BASE_DIR / ".env"
if env_file.exists():
    environ.Env.read_env(str(env_file))

SECRET_KEY = env("SECRET_KEY", default="insecure-dev-key-change-me")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # third-party
    "rest_framework",
    "django_htmx",
    # apps do domínio
    "apps.accounts",
    "apps.students",
    "apps.classes",
    "apps.documents",
    "apps.grades",
    "apps.google_drive",
    "apps.dashboard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.google_drive.context_processors.drive_status",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": env.db("DATABASE_URL", default="sqlite:///" + str(BASE_DIR / "db.sqlite3")),
}

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "dashboard:home"
LOGOUT_REDIRECT_URL = "accounts:login"

LANGUAGE_CODE = "pt-br"
TIME_ZONE = env("TIME_ZONE", default="America/Sao_Paulo")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

# ------------------------------------------------------------------------
# Upload de arquivos
#
# Importante: o Django SEMPRE usa um buffer em memória (InMemoryUploadedFile)
# para arquivos pequenos e um arquivo temporário do sistema operacional
# (TemporaryUploadedFile) para arquivos maiores que FILE_UPLOAD_MAX_MEMORY_SIZE.
# Esse arquivo temporário é excluído automaticamente ao final do request —
# o sistema NUNCA copia o upload para um MEDIA_ROOT persistente. Por isso
# MEDIA_ROOT não é usado como destino de armazenamento (ver apps.documents).
# ------------------------------------------------------------------------
MAX_UPLOAD_SIZE_MB = env.int("MAX_UPLOAD_SIZE_MB", default=15)
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_SIZE_BYTES
FILE_UPLOAD_MAX_MEMORY_SIZE = 2621440  # 2.5 MB — acima disso vira TemporaryUploadedFile

ALLOWED_UPLOAD_EXTENSIONS = env.list(
    "ALLOWED_UPLOAD_EXTENSIONS",
    default=[".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx", ".xls", ".xlsx", ".txt", ".csv"],
)

# ------------------------------------------------------------------------
# Criptografia de campos sensíveis (tokens OAuth do Google em repouso)
# ------------------------------------------------------------------------
FIELD_ENCRYPTION_KEY = env("FIELD_ENCRYPTION_KEY", default=None)

# ------------------------------------------------------------------------
# Integração Google Drive / Sheets
# ------------------------------------------------------------------------
GOOGLE_CLIENT_ID = env("GOOGLE_CLIENT_ID", default="")
GOOGLE_CLIENT_SECRET = env("GOOGLE_CLIENT_SECRET", default="")
GOOGLE_REDIRECT_URI = env("GOOGLE_REDIRECT_URI", default="http://localhost:8000/google-drive/oauth2callback/")
GOOGLE_OAUTH_SCOPES = env.list(
    "GOOGLE_OAUTH_SCOPES",
    default=[
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/spreadsheets",
    ],
)
GOOGLE_DRIVE_ROOT_FOLDER_ID = env("GOOGLE_DRIVE_ROOT_FOLDER_ID", default="")

# Nomes das pastas de topo dentro da pasta raiz "Sistema Escolar"
GOOGLE_DRIVE_STUDENTS_FOLDER_NAME = "Alunos"
GOOGLE_DRIVE_CLASSES_FOLDER_NAME = "Turmas"
GOOGLE_DRIVE_REPORTS_FOLDER_NAME = "Relatórios"

MESSAGE_TAGS = {}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "apps.google_drive": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
