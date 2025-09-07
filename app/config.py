import os

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
    #SQLALCHEMY_DATABASE_URI = _normalize_db_uri(os.getenv("DATABASE_URL"))
    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")
    if not SQLALCHEMY_DATABASE_URI:
        raise RuntimeError("SQLALCHEMY_DATABASE_URI not set for ProductionConfig")
