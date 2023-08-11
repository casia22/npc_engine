from dataclasses import dataclass

from zhipuai.model_api.params import ModelParams


@dataclass
class ChatGLM130bParams(ModelParams):
    model: str = "chatglm_130b"


@dataclass
class ChatGLM6bParams(ModelParams):
    model: str = "chatglm_6b"
