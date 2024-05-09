from pathlib import Path
import os

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 8001

BASE_DIR = Path(__file__).parent.parent  # os.getenv('BASE_DIR')
DATABASE_PATH = BASE_DIR / 'watchDB.sqlite3'
