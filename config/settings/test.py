from .base import *  # noqa: F401,F403

DEBUG = False

# Hash rápido de senhas acelera a suíte de testes (nunca usar em produção).
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Os testes nunca devem depender de credenciais reais do Google — todas as
# chamadas à API são mockadas (ver apps/google_drive/tests). Uma chave Fernet
# fixa evita a necessidade de um .env só para rodar a suíte.
FIELD_ENCRYPTION_KEY = env(  # noqa: F405
    "FIELD_ENCRYPTION_KEY", default="jlVwWM0RxTSHZYHXGfadByH0qBN6EZaZ3ejGMq19_eY="
)
GOOGLE_DRIVE_ROOT_FOLDER_ID = "test-root-folder-id"

MESSAGE_STORAGE = "django.contrib.messages.storage.cookie.CookieStorage"

STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
