from pathlib import Path

env_path = (Path(__file__).parents[2] / '.env.tests').resolve()
if not env_path.exists():
    raise FileNotFoundError('File .env.tests does not exist')

from dotenv import load_dotenv
load_dotenv(Path(__file__).parents[2] / '.env.tests')

sql_delete_all = """
DROP TABLE IF EXISTS log;
DROP TABLE IF EXISTS watch;
DROP TABLE IF EXISTS session_token;
DROP TABLE IF EXISTS users;
"""
