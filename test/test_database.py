import pytest
from npc_engine.src.utils.database import PickleDB
from npc_engine.src.config.config import PROJECT_ROOT_PATH
import os

class TestPickleDBManager:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        self.db_path = PROJECT_ROOT_PATH / "test" / "test.db"
        self.db = PickleDB(self.db_path, auto_dump=True)
        yield
        os.remove(self.db_path)

    def test_set_and_get(self):
        self.db.set('key1', 'value1')
        assert self.db.get('key1') == 'value1'
        assert self.db.get('key2') is False

    def test_delete(self):
        self.db.set('key1', 'value1')
        assert self.db.delete('key1') is True
        assert self.db.get('key1') is False
        assert self.db.delete('key2') is False

    def test_dump(self):
        self.db.set('key1', 'value1')
        assert self.db.dump() is True
