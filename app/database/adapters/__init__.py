from app.database.adapters.sqlite import SQLiteAdapter

__all__ = ["SQLiteAdapter"]

try:
    from app.database.adapters.postgres import PostgresAdapter
    __all__.append("PostgresAdapter")
except ImportError:
    pass

try:
    from app.database.adapters.mysql import MySQLAdapter
    __all__.append("MySQLAdapter")
except ImportError:
    pass

try:
    from app.database.adapters.mongo import MongoAdapter
    __all__.append("MongoAdapter")
except ImportError:
    pass
