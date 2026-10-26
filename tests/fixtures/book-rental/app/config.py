"""Settings. Values here are defaults; deployments override them through the environment."""

import os

DATA_PATH = os.environ.get("LIBRARY_DATA_PATH", "data/library.json")

MAX_FAILED_LOGINS = 5
SESSION_TTL_SECONDS = 30 * 60

RENTAL_DAYS = 14
LATE_FEE_PER_DAY_CENTS = 50
LATE_FEE_CAP_CENTS = 2000

SMTP_HOST = os.environ.get("SMTP_HOST", "localhost")
ADMIN_PASSWORD_SHA256 = os.environ.get("ADMIN_PASSWORD_SHA256", "")
