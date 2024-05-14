from mysql.connector.aio import connect, MySQLConnection
from mysql.connector.aio.cursor import MySQLCursor


class DBWrapper:

    def __init__(self, db: MySQLConnection, cursor: MySQLCursor):
        self._db: MySQLConnection = db
        self._cursor: MySQLCursor = cursor

    @property
    def cursor(self) -> MySQLCursor:
        return self._cursor

    async def commit(self):
        await self._db.commit()


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

    def access(self) -> DBContext:
        return DBContext(self.credentials)
