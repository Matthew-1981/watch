from pathlib import Path

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 8001

BASE_DIR = Path(__file__).parent.parent
DATABASE_PATH = BASE_DIR / 'watchDB.sqlite3'
