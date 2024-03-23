import logging
import time
from pathlib import Path
from typing import List

import numpy as np  # 导入numpy库用于计算

from nuwa.src.utils.embedding import LocalEmbedding
from nuwa.src.npc.action import ActionItem

class FailSafe:
    def __init__(self, embedding_model:LocalEmbedding=None):
        if not embedding_model:
            pass
        else:
            self.embedding_model = embedding_model

    def action_fail_safe(self, action_name:str, action_list:List["ActionItem"], embedding_model:LocalEmbedding=None, threshold:float=0.6)->"ActionItem":
        """
        使用向量化和余弦相似度进行容错检索
        :param action_name: 需要容错的动作名称
        :param action_list: 可选的动作列表, Item是ActionItem对象
        :param embedding_model: 用于文本向量化的模型
        :param threshold: 超过这个值，才可能被认为是failSafe对象，否则落空。
        :return: 最接近的动作名称
        """


        # 1.将action_name和action_list使用embedding_model进行向量化
        if embedding_model is not None:
            action_name_vec = embedding_model.embed_text(action_name)
        else:
            action_name_vec = self.embedding_model.embed_text(action_name)
        action_list_vecs = [action.vec for action in action_list]

        # 2.检索最邻的action
        similarities = [self.cosine_similarity(action_name_vec, vec) for vec in action_list_vecs]
        print(similarities, [each.name for each in action_list])
        max_index = np.argmax(similarities)  # 找到最高相似度的索引
        closest_action = action_list[max_index]  # 根据索引找到最接近的动作

        # 3. threshold
        if similarities[max_index]>threshold:
            return closest_action

        return ""  # 如果没有匹配到 那么action为“”

    def cosine_similarity(self, vec1, vec2):
        """
        计算两个向量之间的余弦相似度
        :param vec1: 第一个向量
        :param vec2: 第二个向量
        :return: 余弦相似度
        """
        dot_product = np.dot(vec1, vec2)
        norm_vec1 = np.linalg.norm(vec1)
        norm_vec2 = np.linalg.norm(vec2)
        return dot_product / (norm_vec1 * norm_vec2)

if __name__ == "__main__":
    # 假设embedding_model已实现并且可以使用
    embedding_model = LocalEmbedding(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", vector_width=384)
    fail_safe = FailSafe()
    action_to_select = []
    for each in ["catch", "move", "talk", "attack", "release"]:
        action_item = ActionItem(
            name=each,
            definition="",
            example="",
            log_template="",
            multi_param=False,
        )
        action_item.vec = embedding_model.embed_text(action_item.name)
        action_to_select.append(action_item)
    closest_action = fail_safe.action_fail_safe("chat", action_to_select, embedding_model)
    print(f"最接近的动作是: {closest_action.name}")
