import unittest
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parents[2] / '.env')

from settings import DATABASE_CONFIG
from app.db import users, db_access


class TestUsers(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.db = db_access.DBAccess(DATABASE_CONFIG)

    async def test_insert_user(self):
        new_user = users.NewUser(
            user_name='test',
            password_hash='AKDJKSJDHK',
            date_of_creation=datetime.now()
        )
        async with self.db.access() as wp:
            await users.UserRecord.new_user(wp.cursor, new_user)
            await wp.commit()

        async with self.db.access() as wp:
            user = await users.UserRecord.get_user_by_name(wp.cursor, 'test')

        self.assertEqual(new_user.password_hash, user.data.password_hash)


if __name__ == '__main__':
    unittest.main()
