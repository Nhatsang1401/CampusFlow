"""Production environment settings."""

import os

from django.core.exceptions import ImproperlyConfigured

from .base import MIDDLEWARE as BASE_MIDDLEWARE

DEBUG = False

SECRET_KEY = os.getenv("SECRET_KEY", "").strip()

if not SECRET_KEY:
    raise ImproperlyConfigured("SECRET_KEY phải được cấu hình trong môi trường production.")

ALLOWED_HOSTS = [host.strip() for host in os.getenv("ALLOWED_HOSTS", "").split(",") if host.strip()]

if not ALLOWED_HOSTS:
    raise ImproperlyConfigured("ALLOWED_HOSTS phải chứa ít nhất một tên miền hợp lệ.")


MIDDLEWARE = list(BASE_MIDDLEWARE)

MIDDLEWARE.insert(
    1,
    "whitenoise.middleware.WhiteNoiseMiddleware",
)


STORAGES = {
    "default": {
        "BACKEND": ("django.core.files.storage.FileSystemStorage"),
    },
    "staticfiles": {
        "BACKEND": ("whitenoise.storage.CompressedManifestStaticFilesStorage"),
    },
}


SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "true").lower() in {"1", "true", "yes", "on"}

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "0"))

SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv("SECURE_HSTS_INCLUDE_SUBDOMAINS", "false").lower() in {
    "1",
    "true",
    "yes",
    "on",
}

SECURE_HSTS_PRELOAD = False

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
