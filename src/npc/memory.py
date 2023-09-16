"""
NPC的记忆处理类
    NPCMemory
    MemoryItem
"""
import hashlib
import json
import queue
import asyncio
from typing import Any, Dict, List

import numpy as np
import pinecone
import requests
import logging

from langchain.text_splitter import RecursiveCharacterTextSplitter

from npc_engine.src.config.config import NPC_MEMORY_CONFIG, CONSOLE_HANDLER, FILE_HANDLER, PROJECT_ROOT_PATH, \
    MEMORY_DB_PATH
from npc_engine.src.utils.database import PickleDB
from npc_engine.src.utils.embedding import LocalEmbedding, SingletonEmbeddingModel, BaseEmbeddingModel
from npc_engine.src.utils.faissdatabase import VectorDatabase
import os

# LOGGER配置
logger = logging.getLogger("NPC_MEMORY")
logger.addHandler(CONSOLE_HANDLER)
logger.addHandler(FILE_HANDLER)
logger.setLevel(logging.DEBUG)  # 设为 DEBUG 级别以显示所有日志


class MemoryItem:
    def __init__(self, text: str, game_time: str, score: float = 0.0, **kwargs):
        self.text = text
        self.md5_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        self.game_time = game_time
        self.score = score

    def __str__(self):
        return f"MemoryItem(text={self.text},game_time={self.game_time},score={self.score},md5_hash={self.md5_hash})"

    def __repr__(self):
        return self.__str__()

    def to_json_str(self):
        return json.dumps(self.__dict__)

    @classmethod
    def from_json_str(cls, json_str):
        json_dict = json.loads(json_str)
        return cls(**json_dict)

    def set_score(self, score: float):
        self.score = score
        return self


class NPCMemory:
    """
    NPC的记忆类，提供本地队列latest_k记忆的存储、向量数据库记忆的查询。
    处理逻辑:
        1.记忆会优先被放入本地队列，当队列满了之后，会将队列中的记忆放入向量数据库中。
        2.检索时，根据相关性从向量数据库中检索top_p
        3.返回检索结果和latest_k的记忆字典
    """

    def __init__(
            self,
            npc_name: str,
            k: int,
            EmbeddingModel: BaseEmbeddingModel,
            the_npc_memory_config: Dict[str, Any] = NPC_MEMORY_CONFIG,

    ):
        """
        npc_name: NPC的名字
        k: latest_k队列的长度
        pinecone_api_key: Pinecone的API密钥
        pinecone_index_name: Pinecone的索引名称
        embeding_model: embedding模型的引用，需要提供embed_text(text)方法
        """
        # npc_memory设置
        self.npc_name = npc_name
        self.latest_k = queue.Queue(maxsize=k)
        self.base_path = os.path.join(PROJECT_ROOT_PATH, "src", "data")
        self.vdb_path = os.path.join(self.base_path, f"{self.npc_name}.pkl")
        print("vdb_path", self.vdb_path)
        """embedding model设置"""
        # ‼️huggingface local embedding model config. AlreadyDone in config.py
        self.embedding_model = EmbeddingModel
        if os.path.exists(self.vdb_path):
            print(f"'{self.vdb_path}' exists.")
        else:
            print(f"'{self.vdb_path}' does not exist.")
        # openai embedding model
        # TODO

        """vector database设置"""
        self.vector_database = VectorDatabase(dim=NPC_MEMORY_CONFIG["hf_dim"], vdb_file_path=self.vdb_path)
        
        # 如果向量数据库文件不存在，立即保存新创建的数据库
        if not os.path.exists(self.vdb_path):
            self.vector_database.save()
        logger.debug(f"{self.npc_name} memory init done, k={k}, model_name=sbert-base-chinese-nli")

        """数据库设置"""
        self.memory_db = PickleDB(MEMORY_DB_PATH)

    def embed_text(self, text: str) -> list:
        """使用用户指定的embedding模型对文本进行embedding，返回一个list
        默认模型:
            LocalEmbedding(model_name="uer/sbert-base-chinese-nli", vector_width=768)
        模型在引擎启动时初始化，可以通过修改配置文件更换模型以及是否本地化推理(配置文件也就是config.py)。
        """
        vector = self.embedding_model.embed_text(text)
        return vector

    async def add_memory_text(self, text: str, game_time: str, direct_upload: bool = False):
        """
        将一条新的记忆文本添加到机器人的记忆中。
        记忆先被放入latest_k队列中，当队列满了之后，最老的记忆会被上传到向量数据库。
        game_time 是记忆文本对应的游戏时间戳，用于计算记忆的时效性。

        :param text: 新的记忆文本
        :param game_time: 记忆文本对应的游戏时间戳
        :param direct_upload: 是否直接上传到向量数据库
        """
        # 构造记忆对象
        new_memory_item = MemoryItem(text, game_time)
        if direct_upload:
            # 直接上传语义向量,存入数据库
            asyncio.run(self.add_memory(new_memory_item))
            return

        # 如果满了就将最老的记忆上传到向量数据库,放入数据库
        if self.latest_k.full():
            old_memory_item = self.latest_k.get()
            # embed最老的记忆并上传到向量数据库
            asyncio.create_task(self.add_memory(old_memory_item))
        # 将新的记忆加入到latest_k队列中
        self.latest_k.put(new_memory_item)

    async def add_memory(self, memory_item: MemoryItem):
        """
        将一条需要持久化检索的记忆文本：
            1.向量化
            2.存入向量数据库
            3.存入KV数据库
        :param memory_item:
        :return:
        """
        embedding = self.embed_text(memory_item.text)
        self.vector_database.put(key=memory_item.md5_hash, vector=embedding)

        self.memory_db.set(key=memory_item.md5_hash, value=memory_item.to_json_str())
        logger.debug(f"add memory {memory_item.md5_hash} done")

    async def add_memory_file(self, file_path: str, game_time: str, chunk_size: int = 50, chunk_overlap: int = 10):
        """
        将一个文本txt文件中的记忆，分片split长传到向量数据库作为记忆
        game_time 是上传文本的记忆时间戳，用于计算记忆的时效性。(可能没有什么意义)

        :param file_path: .txt结尾的文件
        :param game_time: 上传记忆文件对应的游戏时间戳
        """
        # 读取文本并进行拆分
        with open(file_path, "r", encoding="utf-8") as file:
            input_text_file = file.read()
        text_splitter = RecursiveCharacterTextSplitter(
            # Set a tiny chunk size, just to show.
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            add_start_index=True,
        )
        texts: List = text_splitter.create_documents([input_text_file])
        text_chunks: List[str] = [doc.page_content for doc in texts]
        # 构造记忆对象
        memory_items: List[MemoryItem] = [MemoryItem(text, game_time) for text in text_chunks]
        logger.info(
            f"NPC:{self.npc_name} 的文本记忆文件 {file_path} 拆分为{[len(each.text) for each in memory_items]}, 为{len(text_chunks)}个片段，每个片段长度为{chunk_size}，重叠长度为{chunk_overlap}")
        logger.debug(f"NPC:{self.npc_name} 的文本记忆文件 {file_path} 拆分为{[each.text for each in memory_items]}")
        # 将记忆上传到向量数据库，存入KV数据库
        for memory_item in memory_items:
            asyncio.run(self.add_memory(memory_item))
            logger.debug(f"NPC:{self.npc_name} 的文本记忆文件 {file_path} 的片段 {memory_item.text} 上传到向量数据库")

    def time_score(self, game_time: str, memory_game_time: str) -> float:
        """
        本来打算：计算记忆的时间分数，记忆越新分数越高。
        实现：均匀给分，无视时间的差；也就是说只有相关度被考虑
        :param game_time: 当前游戏时间戳
        :param memory_game_time: 记忆的游戏时间戳
        :return:
        """
        # TODO：实现记忆的时间分数
        # score = float(game_time) - float(memory_game_time)
        return 1

    async def search_memory(self, query_text: str, query_game_time: str, k: int, top_p: float = 1) -> Dict[
        str, List[MemoryItem]]:

        logger.debug(f"NPC:{self.npc_name} 开始搜索记忆, 检索语句为：{query_text}，检索数量为：{k}，top_p为：{top_p}")

        # 对query_text进行embedding
        query_embedding = self.embed_text(query_text)
        logger.debug(f"Query embedding: {query_embedding}")

        # 从pinecone中搜索与query_text最相似的2k条记忆
        response = self.vector_database.search(vector=query_embedding, k=2 * k, thresh=0.8)
        logger.debug(f"Vector database response: {response}")

        keys, distances = response
        vdb_response = [{"id": key, "score": distance} for key, distance in zip(keys, distances)]
        logger.debug(f"vdb_response: {vdb_response}")

        match_items: List[MemoryItem] = [
            MemoryItem.from_json_str(self.memory_db.get(match["id"])) for match in vdb_response
        ]
        logger.debug(f"Matched memory items: {match_items}")

        # 提取每个match到的MemoryItem中的cosine score
        match_scores: List[float] = [float(match["score"]) for match in vdb_response]
        logger.debug(f"Match scores: {match_scores}")

        # MemoryItem中的game_time，结合query_game_time和cosine score筛选出k个importance最大的match
        time_scores: List[float] = [
            self.time_score(match_item.game_time, query_game_time)
            for match_item in match_items
        ]
        logger.debug(f"Time scores: {time_scores}")

        importance_scores: List[float] = [
            time_score * match_score
            for time_score, match_score in zip(time_scores, match_scores)
        ]
        logger.debug(f"Importance scores: {importance_scores}")

        match_items: List[MemoryItem] = [
            item.set_score(score) for item, score in zip(match_items, importance_scores)
        ]

        # 选取最大的k个importance_scores所对应的match_items
        importance_scores_array: np.array = np.array(importance_scores)
        top_k_indices = np.argsort(importance_scores_array)[-k:]
        logger.debug(f"Top k indices: {top_k_indices}")

        top_k_match_items: List[MemoryItem] = [match_items[index] for index in top_k_indices]

        # 将MemoryItem按importance_scores从大到小排序
        top_k_match_items.sort(key=lambda x: x.score, reverse=True)

        top_k_match_items_scores: List[float] = [match_item.score for match_item in top_k_match_items]
        softmax = lambda x: np.exp(x) / np.sum(np.exp(x))
        softmax_scores = softmax(top_k_match_items_scores)
        sorted_indices = np.argsort(softmax_scores)[::-1]  # 按得分降序排序
        cumulative_sum = np.cumsum(softmax_scores[sorted_indices])

        # 寻找满足累积和>=top_p的最小索引
        selected_index = np.where(cumulative_sum >= top_p)[0]
        if selected_index.size > 0:
            selected_index = selected_index[0] + 1  # +1是因为索引是0-based，我们需要的是数量
        else:
            selected_index = len(top_k_match_items_scores)

        selected_items = [top_k_match_items[i] for i in sorted_indices[:selected_index]]

        # 和latest_k中的内容做合并成为related_memorys_list并返回
        related_memorys_list = {
            "related_memories": selected_items,
            "latest_memories": list(self.latest_k.queue),
        }
        logger.debug(
            f"NPC:{self.npc_name} 检索记忆完成，得分:{importance_scores}, 过滤后检索数量为：{len(selected_items)}, 检索结果为：{related_memorys_list}")

        return related_memorys_list

    def abstract_memory(self, importance_threshold):
        """摘要记忆"""
        # TODO: 抽取pincone数据库中最老的记忆进行摘要然后变为一条信息上传到pinecone
        pass

    def clear_memory(self):
        """
        清空向量数据库中的记忆
        但是不清空KV数据库中的记忆
        """
        self.vector_database.remove()
        logger.debug("NPC: {} 向量库记忆已清空".format(self.npc_name))

    def shutdown(self):
        """关闭方法，将latest_k队列中的text按照语义上传到向量数据库,并存入KV数据库"""
        logger.debug("NPC: {} 的{}条向量库记忆上传中...".format(self.npc_name, self.latest_k.qsize()))
        while not self.latest_k.empty():
            memory_item = self.latest_k.get()
            asyncio.run(self.add_memory(memory_item))
            logger.debug(f"NPC{self.npc_name} 记忆 {memory_item.text} 的向量库记忆已上传")
        logger.debug("NPC: {} 的向量库记忆上传完成".format(self.npc_name))


async def main():
    # logger设置
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(CONSOLE_HANDLER)
    logger.addHandler(FILE_HANDLER)

    """NPC测试"""
    npcM = NPCMemory(npc_name="stone9111", k=3)
    """
    NPC 文件检索测试
    stone91_mem.txt 中包含AK武器介绍、喜羊羊的介绍,检索回复应该都是关于武器的而不是喜羊羊的
    """
    await npcM.add_memory_file(file_path=PROJECT_ROOT_PATH / 'src' / 'data' / 'stone91_mem.txt',
                               game_time="2021-08-01 12:00:00", chunk_size=100, chunk_overlap=10)
    print(await npcM.search_memory("我想要攻击外星人，有什么趁手的装备吗？", "2021-08-01 12:00:00", k=3))

    """
    NPC问句检索测试
    回复应当是关于AK47的而不是喜羊羊和食物的
    """
    await npcM.add_memory_text("AK47可以存放30发子弹", "2021-08-01 12:00:00")
    await npcM.add_memory_text("我去年买了一个防弹衣", "2021-08-01 12:00:00")
    await npcM.add_memory_text("我上午吃了大西瓜", "2021-08-01 12:00:00")
    await npcM.add_memory_text("我中午吃了大汉堡", "2021-08-01 12:00:00")
    await npcM.add_memory_text("我下午吃了小猪蹄", "2021-08-01 12:00:00")
    await npcM.add_memory_text("我去年爱上了她，我的CSGO", "2021-08-01 12:00:00")
    await npcM.add_memory_text("喜羊羊说一定要给我烤羊肉串吃", "2021-08-01 12:00:00")
    await npcM.add_memory_text("喜羊羊说一定要给我烤羊肉串吃", "2021-08-01 12:00:00")
    await npcM.add_memory_text("喜羊羊说一定要给我烤羊肉串吃", "2021-08-01 12:00:00")
    await npcM.add_memory_text("喜羊羊说一定要给我烤羊肉串吃", "2021-08-01 12:00:00")
    print(await npcM.search_memory("AK有多少发子弹？", "2021-08-01 12:00:00", k=3))


if __name__ == "__main__":
    asyncio.run(main())
