import pytest

from npc_engine.src.config.config import NPC_MEMORY_CONFIG

from npc_engine.src.utils.embedding import LocalEmbedding, HuggingFaceEmbedding

# 测试样例
test_cases = [
    ("你好", NPC_MEMORY_CONFIG["hf_model_id"], NPC_MEMORY_CONFIG["hf_dim"]),
    ("世界和平", NPC_MEMORY_CONFIG["hf_model_id"], NPC_MEMORY_CONFIG["hf_dim"]),
]


@pytest.mark.parametrize("input_string,model_name,vector_width", test_cases)
def test_LocalEmbedding(input_string, model_name, vector_width):
    embedding = LocalEmbedding(model_name=model_name, vector_width=vector_width)
    vector = embedding.embed_text(input_string)
    # 检查返回的向量长度是否正确
    assert len(vector) == vector_width


@pytest.mark.parametrize("input_string,model_name,vector_width", test_cases)
def test_HuggingFaceEmbedding(input_string, model_name, vector_width):
    embedding = HuggingFaceEmbedding(model_name=model_name, vector_width=vector_width)
    vector = embedding.embed_text(input_string)
    # 检查返回的向量长度是否正确
    assert len(vector) == vector_width
