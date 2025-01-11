import unittest
from datetime import datetime
from pathlib import Path
from fastapi.testclient import TestClient
from dotenv import load_dotenv

load_dotenv(Path(__file__).parents[2] / '.env.tests')
from app.main import app
from app.db import DBAccess, schema_files
from app.settings import DATABASE_CONFIG
from communication import messages

client = TestClient(app)

sql_delete_all = """
DROP TABLE IF EXISTS log;
DROP TABLE IF EXISTS watch;
DROP TABLE IF EXISTS session_token;
DROP TABLE IF EXISTS users;
"""

class TestUserCRUD(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.db_access = DBAccess(DATABASE_CONFIG)
        await self.db_access.run_sql(sql_delete_all)
        for schema in schema_files:
            await self.db_access.run_sql_file(schema)

    async def test_register_user(self):
        response = client.post('/register', json={
            "user_name": "test_user",
            "password": "test_password"
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("user_name", response.json())
        self.assertIn("creation_date", response.json())

    async def test_register_user_bad_request(self):
        response = client.post('/register', json={
            "user_name": "",
            "password": "test_password"
        })
        self.assertEqual(response.status_code, 422)

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

    async def test_login_user_bad_request(self):
        response = client.post('/login', json={
            "user_name": "nonexistent_user",
            "password": "test_password",
            "expiration_minutes": 10
        })
        self.assertEqual(response.status_code, 400)


class TestWatchCRUD(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.db_access = DBAccess(DATABASE_CONFIG)
        await self.db_access.run_sql(sql_delete_all)
        for schema in schema_files:
            await self.db_access.run_sql_file(schema)
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

    async def test_add_watch_bad_request(self):
        response = client.post('/watch/add', content=messages.EditWatchMessage(
            auth=messages.AuthMessage(
                token=self.token,
                expiration_minutes=10
            ),
            name='ttttttt'
        ).json().replace('ttttttt', ''))
        self.assertEqual(response.status_code, 422)

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

    async def test_delete_watch_bad_request(self):
        response = client.post('/watch/delete', content=messages.EditWatchMessage(
            auth=messages.AuthMessage(
                token=self.token,
                expiration_minutes=10
            ),
            name='nonexistent_watch'
        ).json())
        self.assertEqual(response.status_code, 400)


class TestLogCRUD(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.db_access = DBAccess(DATABASE_CONFIG)
        await self.db_access.run_sql(sql_delete_all)
        for schema in schema_files:
            await self.db_access.run_sql_file(schema)
        await self.test_register_and_login_user()
        await self.add_watch()

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

    async def add_watch(self):
        response = client.post('/watch/add', content=messages.EditWatchMessage(
            auth=messages.AuthMessage(
                token=self.token,
                expiration_minutes=10
            ),
            name='test_watch'
        ).json())
        self.assertEqual(response.status_code, 200)

    async def test_add_log(self):
        response = client.post('/logs/add', content=messages.CreateMeasurementMessage(
            auth=messages.AuthMessage(
                token=self.token,
                expiration_minutes=10
            ),
            watch_name='test_watch',
            cycle=1,
            datetime=datetime.now(),
            measure=10.0
        ).json())
        self.assertEqual(response.status_code, 200)
        self.assertIn("log_id", response.json())
        self.assertIn("time", response.json())
        self.assertIn("measure", response.json())

    async def test_add_log_bad_request(self):
        response = client.post('/logs/add', content=messages.CreateMeasurementMessage(
            auth=messages.AuthMessage(
                token=self.token,
                expiration_minutes=10
            ),
            watch_name='nonexistent_watch',
            cycle=1,
            datetime=datetime.now(),
            measure=10.0
        ).json())
        self.assertEqual(response.status_code, 400)

    async def test_delete_log(self):
        await self.test_add_log()
        response = client.post('/logs/delete', content=messages.SpecifyLogDataMessage(
            auth=messages.AuthMessage(
                token=self.token,
                expiration_minutes=10
            ),
            watch_name='test_watch',
            cycle=1,
            log_id=1
        ).json())
        self.assertEqual(response.status_code, 200)

    async def test_delete_log_bad_request(self):
        response = client.post('/logs/delete', content=messages.SpecifyLogDataMessage(
            auth=messages.AuthMessage(
                token=self.token,
                expiration_minutes=10
            ),
            watch_name='test_watch',
            cycle=1,
            log_id=999
        ).json())
        self.assertEqual(response.status_code, 400)

    async def test_get_log_list(self):
        await self.test_add_log()
        response = client.post('/logs/list', content=messages.SpecifyWatchDataMessage(
            auth=messages.AuthMessage(
                token=self.token,
                expiration_minutes=10
            ),
            watch_name='test_watch',
            cycle=1
        ).json())
        self.assertEqual(response.status_code, 200)
        self.assertIn("logs", response.json())

    async def test_get_log_list_bad_request(self):
        response = client.post('/logs/list', content=messages.SpecifyWatchDataMessage(
            auth=messages.AuthMessage(
                token=self.token,
                expiration_minutes=10
            ),
            watch_name='nonexistent_watch',
            cycle=1
        ).json())
        self.assertEqual(response.status_code, 400)

    async def test_get_stats(self):
        await self.test_add_log()
        response = client.post('/logs/stats', content=messages.SpecifyWatchDataMessage(
            auth=messages.AuthMessage(
                token=self.token,
                expiration_minutes=10
            ),
            watch_name='test_watch',
            cycle=1
        ).json())
        self.assertEqual(response.status_code, 200)
        self.assertIn("average", response.json())
        self.assertIn("deviation", response.json())
        self.assertIn("delta", response.json())

    async def test_get_stats_bad_request(self):
        response = client.post('/logs/stats', content=messages.SpecifyWatchDataMessage(
            auth=messages.AuthMessage(
                token=self.token,
                expiration_minutes=10
            ),
            watch_name='nonexistent_watch',
            cycle=1
        ).json())
        self.assertEqual(response.status_code, 400)


if __name__ == '__main__':
    unittest.main()
