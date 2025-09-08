import os
import sys

def _normalize_db_uri(uri: str | None) -> str | None:
    if not uri:
        return uri
    if uri.startswith("postgres://"):
        return uri.replace("postgres://", "postgresql://", 1)
    return uri

class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    JSON_SORT_KEYS = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = _normalize_db_uri(
        os.getenv("DATABASE_URL", "sqlite:///dev.sqlite3")
    )

class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    RATELIMIT_ENABLED = False
    CACHE_TYPE = "NullCache"

class ProductionConfig(BaseConfig):
    DEBUG = False

    def __init__(self):
        super().__init__()
        self.SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")
        # Only raise if not running under pytest (i.e., not in CI test collection)
        if not self.SQLALCHEMY_DATABASE_URI and "pytest" not in sys.modules:
            raise RuntimeError("SQLALCHEMY_DATABASE_URI not set for ProductionConfig")
