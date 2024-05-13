from pathlib import Path
import sqlite3 as sl3

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 8001

BASE_DIR = Path(__file__).parent.parent
DATABASE_PATH = BASE_DIR / 'watchDB.sqlite3'

if not DATABASE_PATH.exists():
    SCHEMA_PATH = BASE_DIR / 'db' / 'schema.sql'
    sl3.connect(DATABASE_PATH).executescript(SCHEMA_PATH.read_text())
