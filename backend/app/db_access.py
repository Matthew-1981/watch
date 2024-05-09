import asyncio
import sqlite3 as sl3


class DBContext:

    def __init__(self, db_path: str):
        self.lock = asyncio.Lock()
        self.db_path = db_path

    async def __aenter__(self):
        await self.lock.acquire()
        self.conn = sl3.connect(self.db_path)
        return self.conn

    async def __aexit__(self, exc_type, exc_value, traceback):
        self.conn.close()
        self.lock.release()
        if exc_type:
            raise exc_value.with_traceback(traceback)


class DBAccess:

    def __init__(self, db_path: str):
        self.db_path = db_path

    def access(self) -> DBContext:
        return DBContext(self.db_path)
