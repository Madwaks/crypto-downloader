"""
Default Application settings. Override these with settings in the module pointed to
by the APP_SETTINGS_MODULE environment variable.
"""

import os
from pathlib import Path

from utils.functional import convert_to_bool


####################
# CORE             #
####################


class RunLevel_State(object):
    DEV = "Development"
    TESTING = "Testing"
    STAGING = "Staging"
    STABLE = "Stable"
    PROD = "Production"

    def __init__(self, value="DEV"):
        self._state = getattr(self.__class__, value)

    def __repr__(self):
        return self._state

    def __str__(self):
        return self._state

    def is_development(self):
        return self._state == self.DEV

    def is_testing(self):
        return self._state == self.TESTING

    def is_staging(self):
        return self._state == self.STAGING

    def is_stable(self):
        return self._state == self.STABLE

    def is_production(self):
        return self._state in (self.PROD, self.STABLE)

    def is_published(self):
        return self._state in (self.STAGING, self.PROD, self.STABLE)


DEBUG = False
IS_CI = convert_to_bool(os.getenv("CI", False))
IS_ADHOC = convert_to_bool(os.getenv("ADHOC", False))

PROJECT_ROOT = Path().absolute()

LOGS_PATH = PROJECT_ROOT / "logs"

default_log_level = "DEBUG" if DEBUG else "INFO"

LOGGING_CONFIG = "logging.config.dictConfig"

LOGGING = {}

"""
{
    'default': {
        'name': str,
        'host': str,
        'port': int,
        'username': str,
        'password': str,
        'ssl': bool,
    },
}
"""
MONGO_DATABASES = {}

"""
{
    'db': int,
    'host': str,
    'port': int
    'password': str,
    'encoding': str('utf-8'),
    'ssl': bool,
}
"""
REDIS_DATABASE = {}


