from pathlib import Path

from mysql.connector.aio import connect, MySQLConnection
from mysql.connector.aio.cursor import MySQLCursor


class DBWrapper:

    def __init__(self, db: MySQLConnection, cursor: MySQLCursor):
        self.db: MySQLConnection = db
        self._cursor: MySQLCursor = cursor

    @property
    def cursor(self) -> MySQLCursor:
        return self._cursor

    async def commit(self):
        await self.db.commit()

    async def rollback(self):
        await self.db.rollback()


class DBContext:

    def __init__(self, db_credentials: dict):
        self.db_credentials = db_credentials

    async def __aenter__(self) -> DBWrapper:
        self.conn = await connect(**self.db_credentials)
        self.cursor = await self.conn.cursor()
        return DBWrapper(self.conn, self.cursor)

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.cursor.close()
        await self.conn.close()
        if exc_type:
            raise exc_value.with_traceback(traceback)


class DBAccess:

    def __init__(self, db_credentials: dict):
        self.credentials = db_credentials

    async def run_sql(self, sql_script: str):
        async with self.access() as wp:
            sql_statements = sql_script.split(';')
            for statement in sql_statements:
                if statement.strip():
                    await wp.cursor.execute(statement)

    async def run_sql_file(self, file: Path):
        with open(file) as f:
            sql_script = f.read()
        await self.run_sql(sql_script)

    def access(self) -> DBContext:
        return DBContext(self.credentials)


async def db_initiate(db_access: DBAccess, *schema_files: Path):
    for file in schema_files:
        await db_access.run_sql_file(file)
