from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parents[2]
SECRET_KEY = "europilot-local-synthetic-only"
DEBUG = False
ROOT_URLCONF = "europilot.urls"
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]
INSTALLED_APPS = ["rest_framework", "europilot"]
MIDDLEWARE = []
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": os.environ.get("EUROPILOT_DB_PATH", str(BASE_DIR / "europilot.sqlite3"))}}
REST_FRAMEWORK = {
    "UNAUTHENTICATED_USER": None,
}
