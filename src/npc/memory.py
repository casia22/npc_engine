"""
NPC的记忆处理类
    NPCMemory
    MemoryItem
"""

import json
import queue
from typing import Any, Dict, List

import numpy as np
import pinecone
import requests
from npc_engine.src.config.config import NPC_MEMORY_CONFIG


class MemoryItem:
    def __init__(self, text: str, game_time: str, score: float = 0.0):
        self.text = text
        self.game_time = game_time
        self.score = score

    def __str__(self):
        return f"MemoryItem(text={self.text}, game_time={self.game_time},score={self.score})"

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
        model_name: str = "huggingface",
        the_npc_memory_config: Dict[str, Any] = NPC_MEMORY_CONFIG,
    ):
        """
        npc_name: NPC的名字
        k: latest_k队列的长度
        pinecone_api_key: Pinecone的API密钥
        pinecone_index_name: Pinecone的索引名称
        model_name: 使用的模型名称，可以是'openai'或'huggingface'
        """
        # npc_memory设置
        self.npc_name = npc_name
        self.latest_k = queue.Queue(maxsize=k)
        self.model_name = model_name

        """embedding model设置"""
        # huggingface embedding model
        self.hf_api_url = the_npc_memory_config["hf_api_url"]
        self.hf_headers = the_npc_memory_config["hf_headers"]
        self.hf_dim = the_npc_memory_config["hf_dim"]
        # openai embedding model
        # TODO

        """pinecone设置"""
        self.pinecone_api_key = the_npc_memory_config["pinecone_api_key"]
        self.pinecone_environment = the_npc_memory_config["pinecone_environment"]
        self.pinecone_index_name = the_npc_memory_config["pinecone_index_name"]

        pinecone.init(
            api_key=self.pinecone_api_key, environment=self.pinecone_environment
        )
        self.vector_engine = pinecone.Index(self.pinecone_index_name)

    def embed_text_openai(self, text: str) -> list:
        """使用OpenAI模型对文本进行嵌入"""
        pass

    def embed_text_huggingface(self, text: str) -> list:
        """使用Hugging Face模型对文本进行嵌入"""
        try:
            response = requests.post(
                self.hf_api_url,
                headers=self.hf_headers,
                json={"inputs": text, "options": {"wait_for_model": True}},
                timeout=10,
            )
            response.raise_for_status()  # Raises stored HTTPError, if one occurred.
        except requests.Timeout:
            print("The request timed out")
            return []
        except requests.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
            return []
        except Exception as err:
            print(f"Other error occurred: {err}")
            return []
        vector: List[float] = response.json()
        assert (
            len(vector) == self.hf_dim
        ), f"len(vector)={len(vector)} != self.hf_dim={self.hf_dim}"
        return vector

    def add_memory_text(self, text: str, game_time: str):
        """
        将一条新的记忆文本添加到机器人的记忆中。
        记忆先被放入latest_k队列中，当队列满了之后，最老的记忆会被上传到pinecone。
        game_time 是记忆文本对应的游戏时间戳，用于计算记忆的时效性。

        :param text: 新的记忆文本
        :param game_time: 记忆文本对应的游戏时间戳
        """
        # 构造记忆对象
        new_memory_item = MemoryItem(text, game_time)
        # 如果满了就将最老的记忆上传到pinecone
        if self.latest_k.full():
            old_memory_item = self.latest_k.get()
            # embed最老的记忆并上传到pinecone
            embedding = self.embed_text(old_memory_item.text)

            self.vector_engine.upsert(
                vectors=[(old_memory_item.to_json_str(), embedding)],
                namespaces=[self.npc_name],
            )
        # 将新的记忆加入到latest_k队列中
        self.latest_k.put(new_memory_item)

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

    def embed_text(self, text: str):
        """
        根据model_name选择不同的embedding方法
        :param text:
        :return:
        """
        if self.model_name == "openai":
            embedding = self.embed_text_openai(text)
        else:
            embedding = self.embed_text_huggingface(text)
            assert (
                len(embedding) == self.hf_dim
            ), f"len(embedding)={len(embedding)} != self.hf_dim={self.hf_dim}"
        assert len(embedding) != 0, "The embedding vector should not be empty."

        return embedding

    def search_memory(
        self, query_text: str, query_game_time: str, k: int, top_p: float = 0.8
    ) -> Dict[str, List[MemoryItem]]:
        """
        在机器人的记忆中搜索与query_text最相似的2k条记忆，结合游戏时间计算importance，取得分最高的k条记忆，然后返回top_p。
        然后结合latest_k队列中的记忆返回两个list。
        :param query_text: 查询文本
        :param query_game_time: 当前游戏时间戳，用于计算记忆的时效性。
        :param k: 返回的队列记忆、pinecone记忆的各自数量.
        :return: {
            'queue_memory': [MemoryItem, MemoryItem, ...], # 最新的k条记忆
            'pinecone_memory': [MemoryItem, MemoryItem, ...] # 最相关的k条记忆, 按照importance从大到小排序
        }
        """
        # 对query_text进行embedding
        query_embedding = self.embed_text(query_text)
        # 从pinecone中搜索与query_text最相似的2k条记忆(# 返回数据格式参照：https://docs.pinecone.io/docs/quickstart)
        pinecone_response = self.vector_engine.query(
            vector=query_embedding, top_k=2 * k, include_values=False
        )
        pinecone_response_matches: str = pinecone_response["matches"]  # 匹配结果
        match_items: List[MemoryItem] = [
            MemoryItem.from_json_str(match["id"]) for match in pinecone_response_matches
        ]  # 将匹配结果转换为MemoryItem对象

        # 提取每个match到的MemoryItem中的cosine score,方便后面按照重要性排序
        match_scores: List[float] = [
            float(match["score"]) for match in pinecone_response_matches
        ]

        # MemoryItem中的game_time，结合query_game_time和cosine score筛选出k个importance最大的match
        time_scores: List[float] = [
            self.time_score(match_item.game_time, query_game_time)
            for match_item in match_items
        ]  # 计算每个match_item的time_score, 越新则值越大(目前未实现，是固定值)
        importance_scores: List[float] = [
            time_score * match_score
            for time_score, match_score in zip(time_scores, match_scores)
        ]  # 计算每个MemoryItem的importance_score
        match_items: List[MemoryItem] = [
            item.set_score(score) for item, score in zip(match_items, importance_scores)
        ]

        # 选取最大的k个importance_scores所对应的match_items
        importance_scores: np.array = np.array(importance_scores)
        top_k_indices = np.argsort(importance_scores)[-k:]
        top_k_match_items: List[MemoryItem] = [
            match_items[index] for index in top_k_indices
        ]

        # 将MemoryItem按importance_scores从大到小排序
        top_k_match_items.sort(key=lambda x: x.score, reverse=True)

        # 对top_k_match_items中的每个元素的score进行softmax，然后取top_p的累积和
        top_k_match_items_scores: List[float] = [
            match_item.score for match_item in top_k_match_items
        ]
        top_k_match_items_scores: np.array = np.array(top_k_match_items_scores)
        softmax = lambda x: np.exp(x) / np.sum(np.exp(x))
        top_k_match_items_scores: np.array = softmax(top_k_match_items_scores)
        top_k_match_items_scores: np.array = np.cumsum(top_k_match_items_scores)
        top_k_match_items_scores: List[float] = list(top_k_match_items_scores)
        top_k_match_items_scores: List[float] = [
            score for score in top_k_match_items_scores if score <= top_p
        ]
        top_k_match_items: List[MemoryItem] = top_k_match_items[
            : len(top_k_match_items_scores)
        ]

        # 和latest_k中的内容做合并成为related_memorys_list并返回
        related_memorys_list = {
            "related_memories": top_k_match_items,
            "latest_memories": self.latest_k.queue,
        }
        return related_memorys_list

    def abstract_memory(self, importance_threshold):
        """摘要记忆"""
        # TODO: 抽取pincone数据库中最老的记忆进行摘要然后变为一条信息上传到pinecone
        pass

    def clear_memory(self):
        """清空记忆"""
        self.vector_engine.delete(delete_all=True, namespace=self.npc_name)

    def shutdown(self):
        """关闭方法，将lastest_k队列中的text按照语义上传到pinecone"""
        while not self.latest_k.empty():
            memory_item = self.latest_k.get()
            embedding = self.embed_text(memory_item.text)
            memory_item = MemoryItem(
                text=memory_item.text, game_time=memory_item.game_time
            )
            self.vector_engine.upsert(
                vectors=[(memory_item.to_json_str(), embedding)],
                namespaces=[self.npc_name],
            )


if __name__ == "__main__":
    npcM = NPCMemory(npc_name="stone91", k=3, model_name="huggingface")
    npcM.add_memory_text("AK47可以存放30发子弹", "2021-08-01 12:00:00")
    npcM.add_memory_text("我去年买了一个防弹衣", "2021-08-01 12:00:00")
    npcM.add_memory_text("我上午吃了大西瓜", "2021-08-01 12:00:00")
    npcM.add_memory_text("我中午吃了大汉堡", "2021-08-01 12:00:00")
    npcM.add_memory_text("我下午吃了小猪蹄", "2021-08-01 12:00:00")
    npcM.add_memory_text("我去年爱上了她，我的CSGO", "2021-08-01 12:00:00")
    npcM.add_memory_text("喜羊羊说一定要给我烤羊肉串吃", "2021-08-01 12:00:00")
    npcM.add_memory_text("喜羊羊说一定要给我烤羊肉串吃", "2021-08-01 12:00:00")
    npcM.add_memory_text("喜羊羊说一定要给我烤羊肉串吃", "2021-08-01 12:00:00")
    npcM.add_memory_text("喜羊羊说一定要给我烤羊肉串吃", "2021-08-01 12:00:00")
    print(npcM.search_memory("有人要开枪打你 你有什么东西可以保护自己吗？", "2021-08-01 12:00:00", k=3))
    npcM.clear_memory()
    """
    实验结果应该是：
        {'related_memories': [MemoryItem(text=AK47可以存放30发子弹, game_time=2021-08-01 12:00:00,score=0.209733307), 
                                MemoryItem(text=我去年买了一个防弹衣, game_time=2021-08-01 12:00:00,score=0.160766095)], 
        'latest_memories': deque([MemoryItem(text=喜羊羊说一定要给我烤羊肉串吃, game_time=2021-08-01 12:00:00,score=0.0), 
                                MemoryItem(text=喜羊羊说一定要给我烤羊肉串吃, game_time=2021-08-01 12:00:00,score=0.0), 
                                MemoryItem(text=喜羊羊说一定要给我烤羊肉串吃, game_time=2021-08-01 12:00:00,score=0.0)])}
    """
