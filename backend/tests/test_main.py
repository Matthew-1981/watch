import unittest
from pathlib import Path
from fastapi.testclient import TestClient
from dotenv import load_dotenv

load_dotenv(Path(__file__).parents[2] / '.env')
from app.main import app
from app.db import DBAccess
from app.settings import DATABASE_CONFIG
from app import messages

client = TestClient(app)

sql_delete_all = """
DROP TABLE IF EXISTS log;
DROP TABLE IF EXISTS watch;
DROP TABLE IF EXISTS session_token;
DROP TABLE IF EXISTS users;
"""

schema_root = Path(__file__).parents[1] / 'app' / 'schema'

class TestUserCRUD(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.db_access = DBAccess(DATABASE_CONFIG)
        await self.db_access.run_sql(sql_delete_all)
        for schema in ['user.sql', 'watch.sql']:
            await self.db_access.run_sql_file(schema_root / schema)

    async def test_register_user(self):
        response = client.post('/register', json={
            "user_name": "test_user",
            "password": "test_password"
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("user_name", response.json())
        self.assertIn("creation_date", response.json())

    async def test_login_user(self):
        await self.test_register_user()
        response = client.post('/login', json={
            "user_name": "test_user",
            "password": "test_password",
            "expiration_minutes": 10
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.json())
        self.assertIn("expiration_date", response.json())

class TestWatchCRUD(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.db_access = DBAccess(DATABASE_CONFIG)
        await self.db_access.run_sql(sql_delete_all)
        for schema in ['user.sql', 'watch.sql']:
            await self.db_access.run_sql_file(schema_root / schema)
        await self.test_register_and_login_user()

    async def test_register_and_login_user(self):
        client.post('/register', json={
            "user_name": "test_user",
            "password": "test_password"
        })
        response = client.post('/login', json={
            "user_name": "test_user",
            "password": "test_password",
            "expiration_minutes": 10
        })
        self.token = response.json()["token"]

    async def test_add_watch(self):
        response = client.post('/watch/add', content=messages.EditWatchMessage(
            auth=messages.AuthMessage(
                token=self.token,
                expiration_minutes=10
            ),
            name='test_watch'
        ).json())
        self.assertEqual(response.status_code, 200)
        self.assertIn("name", response.json())
        self.assertIn("date_of_creation", response.json())

    async def test_delete_watch(self):
        await self.test_add_watch()
        response = client.post('/watch/delete', content=messages.EditWatchMessage(
            auth=messages.AuthMessage(
                token=self.token,
                expiration_minutes=10
            ),
            name='test_watch'
        ).json())
        self.assertEqual(response.status_code, 200)
        self.assertIn("name", response.json())
        self.assertIn("date_of_creation", response.json())

if __name__ == '__main__':
    unittest.main()
