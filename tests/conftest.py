import os

os.environ.setdefault("EUROPILOT_DB_PATH", ":memory:")
import django
import pytest


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "europilot.settings")
django.setup()


@pytest.fixture(autouse=True)
def seed_demo_data(db):
    from django.core.management import call_command

    call_command("seed_demo", verbosity=0)
