"""Deployment script"""

import sys
import shutil
from pathlib import Path

from watch.connector import WatchDB

PROJECT_PATH = Path(__file__).parent / 'watch'
WATCH_DB_NAME = 'watchDB.sqlite3'


def main():
    deployment_path = Path(sys.argv[1]) / 'watch'
    tmp = shutil.ignore_patterns("__pycache__", WATCH_DB_NAME)
    shutil.copytree(PROJECT_PATH, deployment_path, ignore=tmp)
    WatchDB.create_watch_database(deployment_path / WATCH_DB_NAME)


if __name__ == '__main__':
    main()
