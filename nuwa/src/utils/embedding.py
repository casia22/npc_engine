"""
用来向量化文本的组件，按照config，加载本地的huggingface权重并进行推理
"""
import os
import logging
import requests
from sentence_transformers import SentenceTransformer
from typing import Any, Dict, List

from nuwa.src.config.config import MODEL_BASE_PATH,NPC_MEMORY_CONFIG


class SingletonEmbeddingModel(type):
    """
    用来实现单例模式的基类
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonEmbeddingModel, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class BaseEmbeddingModel(metaclass=SingletonEmbeddingModel):
    """
    所有向量化模型的基类，必须实现embed_text方法
    """
    # 必须实现的一个属性:model_name
    model_name:str = None
    def embed_text(self, input_string:str)->List[float]:
        pass


class LocalEmbedding(BaseEmbeddingModel):
    def __init__(self, model_name: str = "uer/sbert-base-chinese-nli", vector_width: int = 768):
        self.logger = logging.getLogger("EMBEDDING")

        # 使用Path构造路径，确保跨平台兼容性
        self.model_path_hf = MODEL_BASE_PATH / "embedding" / model_name.replace("/", "_")
        print("model_path_hf", self.model_path_hf)
        self.model_name = model_name
        os.environ["TOKENIZERS_PARALLELISM"] = "false"

        # 将Path对象转换为字符串路径，以便传递给需要字符串路径的函数
        model_path_hf_str = str(self.model_path_hf)  # 这里将Path对象转换为字符串

        if not os.path.exists(model_path_hf_str):
            self.logger.info(f"模型{model_name}的权重不存在，正在下载... 目标路径：{model_path_hf_str}")
            model = SentenceTransformer(model_name)
            model.save(model_path_hf_str)  # 注意这里也需要传递字符串路径
            self.model = model
        else:
            self.logger.info(f"模型{model_name}的权重已存在，加载本地权重... 路径：{model_path_hf_str}")
            # 在这里，也确保传入字符串路径
            self.model = SentenceTransformer(model_path_hf_str)

        vector_width_from_weights = self.model.get_sentence_embedding_dimension()
        assert vector_width == vector_width_from_weights, f"模型{model_name}的向量宽度为{vector_width_from_weights}，与用户指定的{vector_width}不符"
        self.vector_width = vector_width

        self.logger.info(f"模型{model_name}的权重已加载，向量宽度为{vector_width_from_weights}")
    def embed_text(self, input_string:str):
        try:
            vector = self.model.encode(input_string).tolist()
        except Exception as e:
            import traceback
            self.logger.error(f"向量化文本时出现错误：{e}")
            vector = [0.0]*self.vector_width
        return vector


class HuggingFaceEmbedding(BaseEmbeddingModel):
    """
    用来向量化文本的组件，按照config，向Web API请求huggingface嵌入向量
    """
    def __init__(self, model_name:str="uer/sbert-base-chinese-nli", vector_width:int=768):
        """embedding model设置"""
        self.logger = logging.getLogger("EMBEDDING")
        # huggingface embedding model
        self.hf_api_url = NPC_MEMORY_CONFIG["hf_api_url"]
        self.hf_headers = NPC_MEMORY_CONFIG["hf_headers"]
        self.hf_dim = NPC_MEMORY_CONFIG["hf_dim"]

        self.vector_width = vector_width
        self.model_name = model_name
        self.logger.info(f"模型{model_name}WEB EMBED API 已经初始化")

    def embed_text(self, text: str) -> list:
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
            self.logger.info(f"The embedding request of {text} timed out")
            return [0.0] * self.hf_dim
        except requests.HTTPError as http_err:
            print(f"The embedding of {text} HTTP error occurred: {http_err}")
            return [0.0] * self.hf_dim
        except Exception as err:
            print(f"The embedding of {text} other error occurred: {err}")
            return [0.0] * self.hf_dim
        vector: List[float] = response.json()
        assert (
            len(vector) == self.hf_dim
        ), f"len(vector)={len(vector)} != self.hf_dim={self.hf_dim}"
        return vector



if __name__ == "__main__":
    # local embedding
    embedding = LocalEmbedding(model_name=NPC_MEMORY_CONFIG["hf_model_id"], vector_width=NPC_MEMORY_CONFIG["hf_dim"])
    print(embedding.embed_text("你好"))
    # hugingface embedding
    embedding = HuggingFaceEmbedding(model_name=NPC_MEMORY_CONFIG["hf_model_id"], vector_width=NPC_MEMORY_CONFIG["hf_dim"])
    print(embedding.embed_text("你好"))
    """ 下面是几个可用的模型例子
    "model_id": "uer/sbert-base-chinese-nli",
    "dim": 768,
     
    "model_id": "sentence-transformers/all-MiniLM-L6-v2",
    "dim": 384,
    
    代码例：
    "uer/sbert-base-chinese-nli" ==> LocalEmbedding(model_name="uer/sbert-base-chinese-nli", vector_width=768)
    embedding = LocalEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2", vector_width=384)
    #组件会检查material/embedding文件夹下是否有对应的权重，如果没有，会自动下载(没有的话就需要互联网链接)
    
    embedding = HuggingFaceEmbedding(model_name=NPC_MEMORY_CONFIG["hf_model_id"], vector_width=NPC_MEMORY_CONFIG["hf_dim"])
    # 线上的API请求非常不稳定会有超时的情况，所以不推荐使用
    """




