"""
Filename: config.py
Author: Mengshi*, Yangzejun
Contact: ..., yzj_cs_ilstar@163.com
"""
from pathlib import Path


# NUWA主路径
CODE_ROOT_PATH = Path(__file__).parent.parent.parent
MODEL_BASE_PATH = CODE_ROOT_PATH / "material" / "models"

# KEYS
ZHIPU_KEY = "3fe121b978f1f456cfac1d2a1a9d8c06.iQsBvb1F54iFYfZq"
OPENAI_KEY = "sk-hJs89lkQMzlzoOcADb6739A9091d41229c2c3c0547932fBe"
OPENAI_BASE = "https://api.qaqgpt.com/v1"
OPENAI_MODEL = "gpt-3.5-turbo-16k"


# get your token in http://hf.co/settings/tokens
HF_TOKEN = "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"

HF_EMBEDDING_GANYMEDENIL = {
    # https://huggingface.co/GanymedeNil/text2vec-large-chinese
    "model_id": "GanymedeNil/text2vec-large-chinese",
    "dim": 768,
    "hf_url": "https://api-inference.huggingface.co/pipeline/feature-extraction/GanymedeNil/text2vec-large-chinese",
}

HF_EMBEDDING_SBERT_CHINESE = {
    # https://huggingface.co/uer/sbert-base-chinese-nli
    "model_id": "uer/sbert-base-chinese-nli",
    "dim": 768,
    "hf_url": "https://api-inference.huggingface.co/pipeline/feature-extraction/uer/sbert-base-chinese-nli",
}

HF_EMBEDDING_MINILM = {
    # https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
    "model_id": "sentence-transformers/all-MiniLM-L6-v2",
    "dim": 384,
    "hf_url": "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2",
}

PINECONE_CONFIG = {
    "pinecone_api_key": "c977466b-6661-4caf-b281-81655366d149",
    "pinecone_environment": "us-west1-gcp-free",
    "pinecone_index_name": "npc-engine",
    "pinecone_index_dim": 768,
}

NPC_MEMORY_CONFIG = {
    # pinecone
    "pinecone_api_key": PINECONE_CONFIG["pinecone_api_key"],
    "pinecone_environment": PINECONE_CONFIG["pinecone_environment"],
    "pinecone_index_name": PINECONE_CONFIG["pinecone_index_name"],
    "pinecone_index_dim": PINECONE_CONFIG["pinecone_index_dim"],
    # huggingface
    "hf_token": HF_TOKEN,
    "hf_model_id": HF_EMBEDDING_SBERT_CHINESE["model_id"],
    "hf_dim": HF_EMBEDDING_SBERT_CHINESE["dim"],
    "hf_api_url": HF_EMBEDDING_SBERT_CHINESE["hf_url"],
    "hf_headers": {"Authorization": f"Bearer {HF_TOKEN}"},
    "hf_embedding_online": False,  # 默认离线推理模型
    # db
    "db_dir": "./npc_memory.db",
}

# assert dim of hf model == dim of pinecone index
assert (
    PINECONE_CONFIG["pinecone_index_dim"] == NPC_MEMORY_CONFIG["hf_dim"]
), "dim of hf model != dim of pinecone index"