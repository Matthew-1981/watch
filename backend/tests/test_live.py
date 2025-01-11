import unittest
import json
from datetime import datetime
from pathlib import Path
from fastapi.testclient import TestClient
import subprocess

from .db_tests_settings import sql_delete_all

from app.main import app
from app.db import DBAccess, schema_files
from app.settings import DATABASE_CONFIG
from communication import messages

client = TestClient(app)

class TestWatchAndLogOperations(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.db_access = DBAccess(DATABASE_CONFIG)
        await self.db_access.run_sql(sql_delete_all)
        for schema in schema_files:
            await self.db_access.run_sql_file(schema)
        await self.register_and_login_user()
        await self.run_migrate_script()

    async def run_migrate_script(self):
        sqlite_db = Path(__file__).parents[0] / 'watch.db'
        subprocess.run([
            'python3', str(Path(__file__).parents[1] / 'scripts' / 'migrate.py'),
            str(sqlite_db), 'test_user',
            '--mysql_user', DATABASE_CONFIG['user'],
            '--mysql_password', DATABASE_CONFIG['password'],
            '--mysql_host', DATABASE_CONFIG['host'],
            '--mysql_database', DATABASE_CONFIG['database']
        ], check=True)

    async def register_and_login_user(self):
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

    async def test_add_log(self):
        await self.test_add_watch()
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

    async def test_get_log_list(self):
        await self.test_add_log()
        response = client.post('/logs/list', content=messages.SpecifyWatchDataMessage(
            auth=messages.AuthMessage(
                token=self.token,
                expiration_minutes=10
            ),
            watch_name='Seamaster 300m',
            cycle=1
        ).json())
        print(json.dumps(json.loads(response.content), indent=2))
        self.assertEqual(response.status_code, 200)

    async def test_get_stats(self):
        await self.test_add_log()
        response = client.post('/logs/stats', content=messages.SpecifyWatchDataMessage(
            auth=messages.AuthMessage(
                token=self.token,
                expiration_minutes=10
            ),
            watch_name='Seamaster 300m',
            cycle=1
        ).json())
        print(json.dumps(json.loads(response.content), indent=2))
        self.assertEqual(response.status_code, 200)
        self.assertIn("average", response.json())
        self.assertIn("deviation", response.json())
        self.assertIn("delta", response.json())

if __name__ == '__main__':
    unittest.main()
