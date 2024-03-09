import os
import numpy as np
import faiss
import pickle
from pathlib import Path


class VectorDatabase:
    def __init__(self, npc_name: str, dim: int, base_path: Path = Path("npc_vector_databases")):
        self.dim = dim
        self.npc_name = npc_name
        self.base_path = base_path / npc_name  # 每个NPC的基础路径
        self.index_path = self.base_path / f"{npc_name}.db"  # FAISS数据库文件路径
        self.pkl_path = self.base_path / f"{npc_name}.pkl"  # key到向量映射的Pickle文件路径
        self.index = None
        self.key2vector = {}

        self.base_path.mkdir(parents=True, exist_ok=True)  # 确保NPC的目录存在

        # 加载或初始化数据库
        if self.index_path.exists():
            print(f'Loading database for NPC "{npc_name}" from', self.index_path)
            self._load_db()
        else:
            print(f'Creating new database for NPC "{npc_name}"')
            self._init_db()

    def _init_db(self):
        self.index = faiss.IndexFlatIP(self.dim)

    def _load_db(self):
        self.index = faiss.read_index(str(self.index_path))
        with self.pkl_path.open('rb') as f:
            self.key2vector = pickle.load(f)

    def _save_db(self):
        faiss.write_index(self.index, str(self.index_path))
        with self.pkl_path.open('wb') as f:
            pickle.dump(self.key2vector, f)

    def put(self, key, vector):
        assert len(vector) == self.dim, "The dimension of the vector does not match the database."
        if key in self.key2vector:
            print(f"Warning: Overwriting existing vector for key '{key}'.")
        self.key2vector[key] = np.array(vector, dtype=np.float32)
        self.index.add(np.array([self.key2vector[key]]))

    def save(self):
        self._save_db()

    def search(self, vector, k=1, thresh=0.8):
        assert len(vector) == self.dim, "The dimension of the vector does not match the database."
        vector = np.array([vector], dtype=np.float32)
        D, I = self.index.search(vector, k)

        keys = []
        distances = []
        for i, d in zip(I[0], D[0]):
            if d > thresh:
                try:
                    key = list(self.key2vector.keys())[i]
                    keys.append(key)
                    distances.append(d)
                except IndexError:
                    continue
        return keys, distances

    def remove(self):
        # 删除向量数据库文件
        if self.index_path.exists():
            os.remove(self.index_path)
        if self.pkl_path.exists():
            os.remove(self.pkl_path)

def test_vector_database():
    npc_name = "3"
    dim = 128
    vdb = VectorDatabase(dim=dim, npc_name=npc_name)

    # 添加一些向量
    vdb.put("key1", np.random.rand(dim))
    vdb.put("key2", np.random.rand(dim))

    # 保存数据库
    vdb.save()

    # 搜索向量
    keys, distances = vdb.search(np.random.rand(dim), k=2)
    print("Found keys:", keys, "with distances:", distances)


"""
运行测试
"""
if __name__ == "__main__":
    test_vector_database()