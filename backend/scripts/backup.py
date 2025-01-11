import argparse
from enum import Enum
from pathlib import Path
import sqlite3

from mysql.connector import connect

schema_root = (Path(__file__).parents[1] / 'app' / 'db' / 'schema').resolve()
schema_files = schema_root / 'user.sql', schema_root / 'watch.sql'

sqlite_schemas = '''
CREATE TABLE IF NOT EXISTS users
(
    user_id          INT AUTO_INCREMENT PRIMARY KEY,
    user_name        VARCHAR(32) NOT NULL,
    password_hash    VARCHAR(64) NOT NULL,
    date_of_creation DATETIME
);
CREATE TABLE IF NOT EXISTS watch
(
    watch_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(32),
    date_of_creation DATETIME,
    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS log
(
    log_id   INT AUTO_INCREMENT PRIMARY KEY,
    watch_id INT NOT NULL,
    cycle    INT NOT NULL,
    timedate DATETIME NOT NULL,
    measure  FLOAT NOT NULL,
    FOREIGN KEY (watch_id) REFERENCES watch (watch_id) ON DELETE CASCADE
);
'''


def make_backup(db_credentials: dict[str, str], sqlite_output: Path):
    if sqlite_output.exists():
        raise FileExistsError(f'Sqlite file {sqlite_output} already exists.')
    sqlite_ctx = sqlite3.connect(sqlite_output)
    for statement in sqlite_schemas.split(';'):
        if statement.strip():
            sqlite_ctx.execute(statement)

    mysql_ctx = connect(**db_credentials)
    mysql_cursor = mysql_ctx.cursor()

    mysql_cursor.execute('SELECT * FROM users')
    users = mysql_cursor.fetchall()
    for user_id, user_name, password_hash, date_of_creation in users:
        sqlite_ctx.execute('INSERT INTO users (user_id, user_name, password_hash, date_of_creation) '
                           'VALUES (?, ?, ?, ?)', (user_id, user_name, password_hash, date_of_creation))

    mysql_cursor.execute('SELECT * FROM watch')
    watches = mysql_cursor.fetchall()
    for watch_id, user_id, name, date_of_creation in watches:
        sqlite_ctx.execute('INSERT INTO watch (watch_id, user_id, name, date_of_creation) '
                           'VALUES (?, ?, ?, ?)', (watch_id, user_id, name, date_of_creation))

    mysql_cursor.execute('SELECT * FROM log')
    logs = mysql_cursor.fetchall()
    for log_id, watch_id, cycle, timedate, measure in logs:
        sqlite_ctx.execute('INSERT INTO log (log_id, watch_id, cycle, timedate, measure) '
                           'VALUES (?, ?, ?, ?, ?)', (log_id, watch_id, cycle, timedate, measure))

    mysql_cursor.close()
    mysql_ctx.close()

    sqlite_ctx.commit()
    sqlite_ctx.close()


mysql_delete_tables = '''
DROP TABLE IF EXISTS log;
DROP TABLE IF EXISTS watch;
DROP TABLE IF EXISTS session_token;
DROP TABLE IF EXISTS users;
'''


def restore_backup(db_credentials: dict[str, str], sqlite_input: Path):
    if not sqlite_input.exists():
        raise FileNotFoundError(f'Sqlite file {sqlite_input} not found.')
    sqlite_ctx = sqlite3.connect(sqlite_input)

    mysql_ctx = connect(**db_credentials)
    mysql_cursor = mysql_ctx.cursor()
    for statement in mysql_delete_tables.split(';'):
        if statement.strip():
            mysql_cursor.execute(statement)
    for schema in schema_files:
        with open(schema) as f:
            statements = f.read()
        for statement in statements.split(';'):
            if statement.split():
                mysql_cursor.execute(statement)

    sqlite_cursor = sqlite_ctx.execute('SELECT * FROM users')
    users = sqlite_cursor.fetchall()
    for user_id, user_name, password_hash, date_of_creation in users:
        mysql_cursor.execute('INSERT INTO users (user_id, user_name, password_hash, date_of_creation) '
                             'VALUES (%s, %s, %s, %s)', (user_id, user_name, password_hash, date_of_creation))

    sqlite_cursor = sqlite_ctx.execute('SELECT * FROM watch')
    watches = sqlite_cursor.fetchall()
    for watch_id, user_id, name, date_of_creation in watches:
        mysql_cursor.execute('INSERT INTO watch (watch_id, user_id, name, date_of_creation) '
                             'VALUES (%s, %s, %s, %s)', (watch_id, user_id, name, date_of_creation))

    sqlite_cursor = sqlite_ctx.execute('SELECT * FROM log')
    logs = sqlite_cursor.fetchall()
    for log_id, watch_id, cycle, timedate, measure in logs:
        mysql_cursor.execute('INSERT INTO log (log_id, watch_id, cycle, timedate, measure) '
                             'VALUES (%s, %s, %s, %s, %s)', (log_id, watch_id, cycle, timedate, measure))

    sqlite_ctx.close()

    mysql_ctx.commit()
    mysql_cursor.close()
    mysql_ctx.close()


class Operation(Enum):
    BACKUP = 'backup'
    RESTORE = 'restore'


def main():
    parser = argparse.ArgumentParser(description='Backup and restore database.')
    parser.add_argument('operation', type=Operation, choices=list(Operation), help='Operation to perform: backup or restore')
    parser.add_argument('--mysql_user', required=True, help='Database user')
    parser.add_argument('--mysql_password', required=True, help='Database password')
    parser.add_argument('--mysql_host', required=True, help='Database host')
    parser.add_argument('--mysql_database', required=True, help='Database name')
    parser.add_argument('--sql_file', type=Path, required=True, help='Path to the SQL file')
    args = parser.parse_args()

    db_config = {
        'user': args.mysql_user,
        'password': args.mysql_password,
        'host': args.mysql_host,
        'database': args.mysql_database,
    }

    if args.operation == Operation.BACKUP:
        make_backup(db_config, args.sql_file)
    elif args.operation == Operation.RESTORE:
        restore_backup(db_config, args.sql_file)
    else:
        raise ValueError("Unknown operation")


if __name__ == '__main__':
    main()
