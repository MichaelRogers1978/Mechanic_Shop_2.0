from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from flask_migrate import Migrate

db = SQLAlchemy()
ma = Marshmallow()
limiter = Limiter(key_func=get_remote_address)
cache = Cache(config={'CACHE_TYPE': "SimpleCache"})
migrate = Migrate()