import unittest
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parents[2] / '.env')

from app.settings import DATABASE_CONFIG
from app.db import users, access, exceptions, watches

sql_delete_all = """
DROP TABLE IF EXISTS log;
DROP TABLE IF EXISTS watch;
DROP TABLE IF EXISTS session_token;
DROP TABLE IF EXISTS users;
"""

schema_root = Path(__file__).parents[1] / 'app' / 'schema'


class TestUsers(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.db = access.DBAccess(DATABASE_CONFIG)
        await self.db.run_sql(sql_delete_all)
        for schema in ['user.sql', 'watch.sql']:
            await self.db.run_sql_file(schema_root / schema)

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
            with self.assertRaises(exceptions.OperationError):
                await users.UserRecord.get_user_by_name(wp.cursor, 'test')

    async def test_get_user_by_id_not_found(self):
        async with self.db.access() as wp:
            with self.assertRaises(exceptions.OperationError):
                await users.UserRecord.get_user_by_id(wp.cursor, 999)

    async def test_get_user_by_name_not_found(self):
        async with self.db.access() as wp:
            with self.assertRaises(exceptions.OperationError):
                await users.UserRecord.get_user_by_name(wp.cursor, 'nonexistent')


class TestTokens(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.db = access.DBAccess(DATABASE_CONFIG)
        await self.db.run_sql(sql_delete_all)
        for schema in ['user.sql', 'watch.sql']:
            await self.db.run_sql_file(schema_root / schema)

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
                token='TOKEN123',
                expiration=datetime.now() + timedelta(days=1)
            )
            token_record = await users.TokenRecord.new_token(wp.cursor, new_token)
            await wp.commit()

        async with self.db.access() as wp:
            token = await users.TokenRecord.get_token_by_value(wp.cursor, 'TOKEN123')

        self.assertEqual(new_token.token, token.data.token)
        tmp = new_token.expiration.replace(microsecond=0)
        self.assertTrue(token.data.expiration in [tmp + timedelta(seconds=1), tmp])

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
                token='TOKEN123',
                expiration=datetime.now() + timedelta(days=1)
            )
            token_record = await users.TokenRecord.new_token(wp.cursor, new_token)
            token_record.data.token = 'NEW_TOKEN'
            token_record.data.expiration = datetime.now() + timedelta(days=2)
            await token_record.update(wp.cursor)
            await wp.commit()

        async with self.db.access() as wp:
            updated_token = await users.TokenRecord.get_token_by_value(wp.cursor, 'NEW_TOKEN')

        self.assertEqual(updated_token.data.token, 'NEW_TOKEN')
        tmp = token_record.data.expiration.replace(microsecond=0)
        self.assertTrue(updated_token.data.expiration in [tmp + timedelta(seconds=1), tmp])

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
                token='TOKEN123',
                expiration=datetime.now() + timedelta(days=1)
            )
            token_record = await users.TokenRecord.new_token(wp.cursor, new_token)
            await token_record.delete(wp.cursor)
            await wp.commit()

        async with self.db.access() as wp:
            with self.assertRaises(exceptions.OperationError):
                await users.TokenRecord.get_token_by_value(wp.cursor, 'TOKEN123')

    async def test_get_token_by_id_not_found(self):
        async with self.db.access() as wp:
            with self.assertRaises(exceptions.OperationError):
                await users.TokenRecord.get_token_by_id(wp.cursor, 999)

    async def test_get_token_by_value_not_found(self):
        async with self.db.access() as wp:
            with self.assertRaises(exceptions.OperationError):
                await users.TokenRecord.get_token_by_value(wp.cursor, 'nonexistent')


class TestWatches(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.db = access.DBAccess(DATABASE_CONFIG)
        await self.db.run_sql(sql_delete_all)
        for schema in ['user.sql', 'watch.sql']:
            await self.db.run_sql_file(schema_root / schema)

        # Add a user to the database
        new_user = users.NewUser(
            user_name='test_user',
            password_hash='password_hash',
            date_of_creation=datetime.now()
        )
        async with self.db.access() as wp:
            await users.UserRecord.new_user(wp.cursor, new_user)
            await wp.commit()

    async def test_insert_watch(self):
        new_watch = watches.NewWatch(
            user_id=1,
            name='test_watch',
            date_of_creation=datetime.now()
        )
        async with self.db.access() as wp:
            await watches.WatchRecord.new_watch(wp.cursor, new_watch)
            await wp.commit()

        async with self.db.access() as wp:
            watch = await watches.WatchRecord.get_watch_by_name(wp.cursor, new_watch.user_id, new_watch.name)

        self.assertEqual(new_watch.name, watch.data.name)

    async def test_update_watch(self):
        new_watch = watches.NewWatch(
            user_id=1,
            name='test_watch',
            date_of_creation=datetime.now()
        )
        async with self.db.access() as wp:
            watch_record = await watches.WatchRecord.new_watch(wp.cursor, new_watch)
            watch_record.data.name = 'updated_watch'
            await watch_record.update(wp.cursor)
            await wp.commit()

        async with self.db.access() as wp:
            updated_watch = await watches.WatchRecord.get_watch_by_name(wp.cursor, new_watch.user_id, 'updated_watch')

        self.assertEqual(updated_watch.data.name, 'updated_watch')

    async def test_delete_watch(self):
        new_watch = watches.NewWatch(
            user_id=1,
            name='test_watch',
            date_of_creation=datetime.now()
        )
        async with self.db.access() as wp:
            watch_record = await watches.WatchRecord.new_watch(wp.cursor, new_watch)
            await watch_record.delete(wp.cursor)
            await wp.commit()

        async with self.db.access() as wp:
            with self.assertRaises(exceptions.OperationError):
                await watches.WatchRecord.get_watch_by_name(wp.cursor, new_watch.user_id, new_watch.name)

    async def test_get_watch_by_id_not_found(self):
        async with self.db.access() as wp:
            with self.assertRaises(exceptions.OperationError):
                await watches.WatchRecord.get_watch_by_id(wp.cursor, 999)

    async def test_get_watch_by_name_not_found(self):
        async with self.db.access() as wp:
            with self.assertRaises(exceptions.OperationError):
                await watches.WatchRecord.get_watch_by_name(wp.cursor, 1, 'nonexistent')


class TestLogs(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.db = access.DBAccess(DATABASE_CONFIG)
        await self.db.run_sql(sql_delete_all)
        for schema in ['user.sql', 'watch.sql']:
            await self.db.run_sql_file(schema_root / schema)

        # Add a user to the database
        new_user = users.NewUser(
            user_name='test_user',
            password_hash='password_hash',
            date_of_creation=datetime.now()
        )
        async with self.db.access() as wp:
            await users.UserRecord.new_user(wp.cursor, new_user)
            await wp.commit()

        # Add a watch to the database
        new_watch = watches.NewWatch(
            user_id=1,
            name='test_watch',
            date_of_creation=datetime.now()
        )
        async with self.db.access() as wp:
            await watches.WatchRecord.new_watch(wp.cursor, new_watch)
            await wp.commit()

    async def test_insert_log(self):
        new_log = watches.NewLog(
            watch_id=1,
            cycle=1,
            timedate=datetime.now(),
            measure=123.45
        )
        async with self.db.access() as wp:
            await watches.LogRecord.new_log(wp.cursor, new_log)
            await wp.commit()

        async with self.db.access() as wp:
            log = await watches.LogRecord.get_log_by_id(wp.cursor, 1)

        self.assertEqual(new_log.measure, log.data.measure)

    async def test_update_log(self):
        new_log = watches.NewLog(
            watch_id=1,
            cycle=1,
            timedate=datetime.now(),
            measure=123.45
        )
        async with self.db.access() as wp:
            log_record = await watches.LogRecord.new_log(wp.cursor, new_log)
            log_record.data.measure = 543.21
            await log_record.update(wp.cursor)
            await wp.commit()

        async with self.db.access() as wp:
            updated_log = await watches.LogRecord.get_log_by_id(wp.cursor, log_record.data.log_id)

        self.assertEqual(updated_log.data.measure, 543.21)

    async def test_delete_log(self):
        new_log = watches.NewLog(
            watch_id=1,
            cycle=1,
            timedate=datetime.now(),
            measure=123.45
        )
        async with self.db.access() as wp:
            log_record = await watches.LogRecord.new_log(wp.cursor, new_log)
            await log_record.delete(wp.cursor)
            await wp.commit()

        async with self.db.access() as wp:
            with self.assertRaises(exceptions.OperationError):
                await watches.LogRecord.get_log_by_id(wp.cursor, log_record.data.log_id)

    async def test_get_log_by_id_not_found(self):
        async with self.db.access() as wp:
            with self.assertRaises(exceptions.OperationError):
                await watches.LogRecord.get_log_by_id(wp.cursor, 999)


if __name__ == '__main__':
    unittest.main()
