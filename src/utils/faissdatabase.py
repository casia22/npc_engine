
from sentence_transformers import SentenceTransformer
# import typing like List etc
from typing import List
import openai
import os
import numpy as np
import faiss
import pickle
import hashlib
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.text_splitter import MarkdownHeaderTextSplitter
from langchain.vectorstores import FAISS
from langchain.document_loaders import TextLoader
from langchain.document_loaders import TextLoader
from langchain.document_loaders import PyPDFLoader
# openai.api_key = "sk-hzqDmA2VFMqIXEOo4aE36e753fC145808178FcDcA6D3627d"
# openai.api_base = "https://api.ai-yyds.com/v1"

class VectorDatabase:
    def __init__(self, dim, vdb_file_path):
        self.dim = dim
        self.vdb_file_path = vdb_file_path
        self.index = None
        self.key2vector = {}

        # 加载已存在的数据库
        if os.path.exists(self.vdb_file_path):
            print('Loading database from', self.vdb_file_path)
            self._load_db()
        else:
            print('Creating new database', self.vdb_file_path)
            self._init_db()

    def _init_db(self):
        # 初始化数据库
        self.index = faiss.IndexFlatIP(self.dim)

    def _load_db(self):
        # 加载数据库
        with open(self.vdb_file_path, 'rb') as f:
            data = pickle.load(f)
            self.index = faiss.deserialize_index(data['index'])
            self.key2vector = data['key2vector']

    def _save_db(self):
        # 保存数据库
        with open(self.vdb_file_path, 'wb') as f:
            data = {
                'index': faiss.serialize_index(self.index),
                'key2vector': self.key2vector,
            }
            pickle.dump(data, f)

    def put(self, key, vector):
        # 存储向量
        assert len(vector) == self.dim, "The dimension of the vector does not match the database."
        self.key2vector[key] = np.array(vector, dtype=np.float32)
        self.index.add(np.array([self.key2vector[key]]))

    def save(self):
        self._save_db()

    def search(self, vector, k=1, thresh=0.8):
        """
        cosine similarity search
        """
        # 搜索向量
        assert len(vector) == self.dim, "The dimension of the vector does not match the database."
        vector = np.array([vector], dtype=np.float32)
        D, I = self.index.search(vector, k)

        keys = []
        distances = []
        for i, d in zip(I[0], D[0]):
            if d > thresh:  # 修改这里以适应你的度量
                try:
                    keys.append(list(self.key2vector.keys())[i])
                    distances.append(d)
                except:
                    continue
        return keys, distances

    def remove(self):
        # 删除向量数据库文件
        if os.path.exists(self.vdb_file_path):
            os.remove(self.vdb_file_path)



def generate_random_vector(dim):
    return np.random.rand(dim)


# 测试VectorDatabase
def vector_database():
    # 定义向量维度和数据库文件路径
    dim = 128
    vdb_file_path = r"D:\pythoncode\npc_engine\src\npc\src\data\test"

    # 创建数据库实例
    db = VectorDatabase(dim, vdb_file_path)

    # 添加向量到数据库
    num_vectors = 10
    for i in range(num_vectors):
        key = f"vector_{i}"
        vector = generate_random_vector(dim)
        db.put(key, vector)

    # 保存数据库
    db.save()

    # 搜索近似向量
    search_vector = generate_random_vector(dim)
    keys, distances = db.search(search_vector, k=3)  # 搜索最近的3个向量

    # 删除数据库文件
    db.remove()

    return keys, distances


# 执行测试
# test_keys, test_distances = vector_database()
# print(test_keys)
# print(test_distances)