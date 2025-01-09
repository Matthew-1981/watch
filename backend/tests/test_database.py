import unittest
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parents[2] / '.env')

from settings import DATABASE_CONFIG
from app.db import users, access, common

sql_delete_all = """
DROP TABLE log;
DROP TABLE watch;
DROP TABLE session_token;
DROP TABLE users;
"""

sql_init_path = Path(__file__).parents[1] / 'app' / 'resources' / 'schema.sql'


class TestUsers(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.db = access.DBAccess(DATABASE_CONFIG)
        await self.db.run_sql(sql_delete_all)
        await self.db.run_sql_file(sql_init_path)

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

    async def test_update_user(self):
        new_user = users.NewUser(
            user_name='test',
            password_hash='AKDJKSJDHK',
            date_of_creation=datetime.now()
        )
        async with self.db.access() as wp:
            user_record = await users.UserRecord.new_user(wp.cursor, new_user)
            user_record.data.password_hash = 'NEW_HASH'
            await user_record.update(wp.cursor)
            await wp.commit()

        async with self.db.access() as wp:
            updated_user = await users.UserRecord.get_user_by_name(wp.cursor, 'test')

        self.assertEqual(updated_user.data.password_hash, 'NEW_HASH')

    async def test_delete_user(self):
        new_user = users.NewUser(
            user_name='test',
            password_hash='AKDJKSJDHK',
            date_of_creation=datetime.now()
        )
        async with self.db.access() as wp:
            user_record = await users.UserRecord.new_user(wp.cursor, new_user)
            await user_record.delete(wp.cursor)
            await wp.commit()

        async with self.db.access() as wp:
            with self.assertRaises(common.DatabaseError):
                await users.UserRecord.get_user_by_name(wp.cursor, 'test')

    async def test_get_user_by_id_not_found(self):
        async with self.db.access() as wp:
            with self.assertRaises(common.DatabaseError):
                await users.UserRecord.get_user_by_id(wp.cursor, 999)

    async def test_get_user_by_name_not_found(self):
        async with self.db.access() as wp:
            with self.assertRaises(common.DatabaseError):
                await users.UserRecord.get_user_by_name(wp.cursor, 'nonexistent')


class TestTokens(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.db = access.DBAccess(DATABASE_CONFIG)
        await self.db.run_sql(sql_delete_all)
        await self.db.run_sql_file(sql_init_path)

    async def test_insert_token(self):
        new_user = users.NewUser(
            user_name='test',
            password_hash='AKDJKSJDHK',
            date_of_creation=datetime.now()
        )
        async with self.db.access() as wp:
            user_record = await users.UserRecord.new_user(wp.cursor, new_user)
            new_token = users.NewToken(
                user_id=user_record.data.user_id,
                token='TOKEN123'
            )
            token_record = await users.TokenRecord.new_token(wp.cursor, new_token)
            await wp.commit()

        async with self.db.access() as wp:
            token = await users.TokenRecord.get_token_by_value(wp.cursor, 'TOKEN123')

        self.assertEqual(new_token.token, token.data.token)

    async def test_update_token(self):
        new_user = users.NewUser(
            user_name='test',
            password_hash='AKDJKSJDHK',
            date_of_creation=datetime.now()
        )
        async with self.db.access() as wp:
            user_record = await users.UserRecord.new_user(wp.cursor, new_user)
            new_token = users.NewToken(
                user_id=user_record.data.user_id,
                token='TOKEN123'
            )
            token_record = await users.TokenRecord.new_token(wp.cursor, new_token)
            token_record.data.token = 'NEW_TOKEN'
            await token_record.update(wp.cursor)
            await wp.commit()

        async with self.db.access() as wp:
            updated_token = await users.TokenRecord.get_token_by_value(wp.cursor, 'NEW_TOKEN')

        self.assertEqual(updated_token.data.token, 'NEW_TOKEN')

    async def test_delete_token(self):
        new_user = users.NewUser(
            user_name='test',
            password_hash='AKDJKSJDHK',
            date_of_creation=datetime.now()
        )
        async with self.db.access() as wp:
            user_record = await users.UserRecord.new_user(wp.cursor, new_user)
            new_token = users.NewToken(
                user_id=user_record.data.user_id,
                token='TOKEN123'
            )
            token_record = await users.TokenRecord.new_token(wp.cursor, new_token)
            await token_record.delete(wp.cursor)
            await wp.commit()

        async with self.db.access() as wp:
            with self.assertRaises(common.DatabaseError):
                await users.TokenRecord.get_token_by_value(wp.cursor, 'TOKEN123')

    async def test_get_token_by_id_not_found(self):
        async with self.db.access() as wp:
            with self.assertRaises(common.DatabaseError):
                await users.TokenRecord.get_token_by_id(wp.cursor, 999)

    async def test_get_token_by_value_not_found(self):
        async with self.db.access() as wp:
            with self.assertRaises(common.DatabaseError):
                await users.TokenRecord.get_token_by_value(wp.cursor, 'nonexistent')


if __name__ == '__main__':
    unittest.main()
