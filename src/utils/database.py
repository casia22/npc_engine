"""
实验性的数据库模块，使用 RocksDB/pickleDB/SQLite 作为后端。
目前遇到问题：
    ROCKSDB好像不能拿来就用，需要先安装
    如果把记忆数据以ID的形式上传到pinecone，中文会被转成unicode编码，512的字符限制很容易超出(最多40个字左右)
    这里的想法是采用KV-store作为本地数据库，用来存储NPC的记忆，然后再把记忆数据上传到pinecone，用来做相似度搜索
RocksDB：
    需要手动make安装，不知道怎么实现平台无关
PickleDB：
    不需要手动安装，嵌入式的python kv存储，支持序列化
SQLite：
    嵌入式文件数据库，不是KV store。按理来说性能应该比KV store要差，但是需要确认是否不如pickleDB
"""
import os
import pickledb
import logging
from pathlib import Path
from npc_engine.src.config.config import NPC_MEMORY_CONFIG,CONSOLE_HANDLER,FILE_HANDLER,PROJECT_ROOT_PATH,MEMORY_DB_PATH

# LOGGER配置
logger = logging.getLogger("DATABASE")
logger.addHandler(CONSOLE_HANDLER)
logger.addHandler(FILE_HANDLER)

class PickleDB:
    _instances = {}

    def __new__(cls, db_path, auto_dump=True):
        """
        单例模式，不同的路径对应不同的数据库，相同的路径对应同一个数据库对象
        :param db_path:
        :param auto_dump:
        """
        if db_path not in cls._instances:
            instance = super(PickleDB, cls).__new__(cls)
            instance.__init__(db_path, auto_dump)
            cls._instances[db_path] = instance
        return cls._instances[db_path]

    def __init__(self, db_path, auto_dump=True):
        """
        初始化函数
        :param db_path: 数据库文件的路径
        :param auto_dump: 是否自动保存更改，默认为True
        """
        self.db_path = db_path
        self.auto_dump = auto_dump
        if not hasattr(self, 'db'):
            self.db = self.load_db()

    def load_db(self):
        """
        从db_path加载数据库
        :return: 返回数据库对象
        """
        if os.path.exists(self.db_path):
            logger.info(f"使用已有数据库：{self.db_path}")
        else:
            logger.info(f"不存在数据库：{self.db_path}，创建新数据库")
        result = pickledb.load(self.db_path, self.auto_dump)
        logger.info(f"数据库已加载：{self.db_path}")
        return result

    def get(self, key):
        """
        获取键值
        :param key: 键
        :return: 返回键对应的值，如果键不存在，返回None
        """
        return self.db.get(key)

    def set(self, key, value):
        """
        设置键值
        :param key: 键
        :param value: 值
        :return: 如果设置成功，返回True，否则返回False
        """
        return self.db.set(key, value)

    def delete(self, key):
        """
        删除键值
        :param key: 键
        :return: 如果删除成功，返回True，否则返回False
        """
        try:
            result:bool = self.db.rem(key)
        except KeyError:
            return False
        logger.debug(f"键{key}已删除")
        return result

    def dump(self):
        """
        手动保存数据库
        :return: 如果保存成功，返回True，否则返回False
        """
        result = self.db.dump()
        logger.debug(f"database {self.db_path} 已持久化到{self.db_path}")
        return result

    def clear(self):
        """
        清空数据库
        :return:
        """
        result =self.db.deldb()
        logger.debug(f"database {self.db_path} 已清空")
        return result
