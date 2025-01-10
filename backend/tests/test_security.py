import unittest
from pathlib import Path
from datetime import datetime, timedelta

from fastapi import HTTPException, status

from dotenv import load_dotenv
load_dotenv(Path(__file__).parents[2] / '.env')

from settings import DATABASE_CONFIG
from app.security import GetUserCreator, create_token
from app.db import DBAccess, UserRecord, NewUser
from app.messages import LoggedInUserMessage, AuthMessage

sql_delete_all = """
DROP TABLE log;
DROP TABLE watch;
DROP TABLE session_token;
DROP TABLE users;
"""

schema_root = Path(__file__).parents[1] / 'app' / 'schema'


class TestGetUserCreator(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.db_access = DBAccess(DATABASE_CONFIG)
        await self.db_access.run_sql(sql_delete_all)
        for schema in ['user.sql', 'watch.sql']:
            await self.db_access.run_sql_file(schema_root / schema)
        self.get_user_creator = GetUserCreator(self.db_access)
        self.user = NewUser(
            user_name='test_user',
            password_hash='hashed_password',
            date_of_creation=datetime.now()
        )
        async with self.db_access.access() as wp:
            self.user_record = await UserRecord.new_user(wp.cursor, self.user)
            self.token_record = await create_token(wp.cursor, self.user_record.data.user_id, 10)
            await wp.commit()

    async def asyncTearDown(self):
        async with self.db_access.access() as wp:
            await wp.cursor.execute("DELETE FROM session_token WHERE user_id = %s", (self.user_record.data.user_id,))
            await wp.cursor.execute("DELETE FROM users WHERE user_id = %s", (self.user_record.data.user_id,))
            await wp.commit()

    async def test_get_user_success(self):
        request = LoggedInUserMessage(auth=AuthMessage(token=self.token_record.data.token, expiration_minutes=10))
        user = await self.get_user_creator(request)
        self.assertEqual(user.data.user_id, self.user_record.data.user_id)

    async def test_get_user_invalid_token(self):
        request = LoggedInUserMessage(auth=AuthMessage(token='invalid_token', expiration_minutes=10))
        with self.assertRaises(HTTPException) as context:
            await self.get_user_creator(request)
        self.assertEqual(context.exception.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(context.exception.detail, "Token invalid or expired.")

    async def test_get_user_expired_token(self):
        async with self.db_access.access() as wp:
            self.token_record.data.expiration = datetime.now() - timedelta(minutes=10)
            await self.token_record.update(wp.cursor)
            await wp.commit()
        request = LoggedInUserMessage(auth=AuthMessage(token=self.token_record.data.token, expiration_minutes=10))
        with self.assertRaises(HTTPException) as context:
            await self.get_user_creator(request)
        self.assertEqual(context.exception.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(context.exception.detail, "Expired token.")


if __name__ == '__main__':
    unittest.main()
