from settings import DATABASE_CONFIG
from .db import access

db_access = access.DBAccess(DATABASE_CONFIG)
