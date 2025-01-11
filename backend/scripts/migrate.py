import argparse
from pathlib import Path
import sqlite3

from mysql.connector import connect


def migrate(sqlite_db: Path, db_config: dict[str, str], user_name: str):
    lite = sqlite3.connect(sqlite_db)
    sqlite_cursor = lite.execute('SELECT * FROM info')
    watches = sqlite_cursor.fetchall()
    sqlite_cursor.close()

    conn = connect(**db_config)
    mysql_cursor = conn.cursor()

    mysql_cursor.execute('SELECT user_id FROM users WHERE user_name = %s', (user_name,))
    user_id = mysql_cursor.fetchone()[0]
    assert isinstance(user_id, int)

    for watch_id, name, date in watches:
        mysql_cursor.execute(
            'INSERT INTO watch (user_id, name, date_of_creation) VALUES (%s, %s, %s)',
            (user_id, name, date)
        )
        mysql_cursor.execute('SELECT watch_id FROM watch WHERE name = %s', (name,))
        mysql_watch_id = mysql_cursor.fetchone()[0]

        sqlite_cursor = lite.execute('SELECT * FROM logs WHERE watch_id = ?', (watch_id,))
        logs = sqlite_cursor.fetchall()
        sqlite_cursor.close()
        for _, _, cycle, timedate, measure in logs:
            mysql_cursor.execute(
                'INSERT INTO log (watch_id, cycle, timedate, measure) VALUES (%s, %s, %s, %s)',
                (mysql_watch_id, cycle, timedate, measure)
            )

    conn.commit()
    mysql_cursor.close()
    conn.close()


def main():
    parser = argparse.ArgumentParser(description='Migrate data from SQLite to MySQL.')
    parser.add_argument('sqlite_db', type=Path, help='Path to the SQLite database file.')
    parser.add_argument('watch_user', type=str, help='Username for the watch database.')
    parser.add_argument('--mysql_user', type=str, required=True, help='MySQL username.')
    parser.add_argument('--mysql_password', type=str, required=True, help='MySQL password.')
    parser.add_argument('--mysql_host', type=str, required=True, help='MySQL host.')
    parser.add_argument('--mysql_database', type=str, required=True, help='MySQL database name.')

    args = parser.parse_args()

    db_config = {
        'user': args.mysql_user,
        'password': args.mysql_password,
        'host': args.mysql_host,
        'database': args.mysql_database,
    }

    migrate(args.sqlite_db, db_config, args.watch_user)


if __name__ == '__main__':
    main()
