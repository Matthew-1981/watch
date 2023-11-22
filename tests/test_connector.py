import unittest
import os
import shutil
from pathlib import Path

from watch.connector import WatchDB, QueryError, NullWatchError


class ConnectorTest(unittest.TestCase):
    directory = Path(__file__).parent.parent

    def setUp(self) -> None:
        shutil.copy(self.directory / "example.sqlite3", self.directory / "test.sqlite3")
        self.dbc = WatchDB(str(self.directory / 'test.sqlite3'))

    def tearDown(self) -> None:
        self.dbc.close()
        os.remove(self.directory / "test.sqlite3")

    def test_watch_info(self):
        out = self.dbc.watch_info_by_id(1)
        self.assertEqual("Seamaster 300m", out.name)
        self.assertRaises(QueryError, self.dbc.watch_info_by_id, 0)
        out = self.dbc.watch_info_by_name("Seamaster 300m")
        self.assertEqual(1, out.id)
        self.assertRaises(QueryError, self.dbc.watch_info_by_name, "noName")
        self.assertRaises(NullWatchError, self.dbc.cur_watch_info)
        self.dbc.change_watch(1)
        out = self.dbc.watch_info_by_id(1)
        self.assertEqual(1, out.id)
        out = set(i.name for i in self.dbc.database_info())
        self.assertEqual({"Seamaster 300m", "Percidrive DS Sport"}, out)


if __name__ == '__main__':
    unittest.main()
