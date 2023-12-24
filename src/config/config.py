"""
Filename: config.py
Author: Mengshi*, Yangzejun
Contact: ..., yzj_cs_ilstar@163.com
"""

import json
import logging
from pathlib import Path
import time
import os

# 项目主路径
PROJECT_ROOT_PATH = Path(__file__).parent.parent.parent
LOG_FILE_PATH = PROJECT_ROOT_PATH / "logs"
CONFIG_PATH = PROJECT_ROOT_PATH / "src" / "config"
MEMORY_DB_PATH = PROJECT_ROOT_PATH / "src" / "data" / "npc_memory.db"
MODEL_BASE_PATH = PROJECT_ROOT_PATH / "material" / "models"

# 时间(兼容windows文件名)
time_format = "%Y-%m-%d-%H-%M-%S"
time_str = time.strftime(time_format, time.localtime())

# LOGGER配置
# 日志格式
LOG_FORMAT = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'

# 日志级别
CONSOLE_LOG_LEVEL = logging.INFO
FILE_LOG_LEVEL = logging.DEBUG

# 控制台处理器
CONSOLE_HANDLER = logging.StreamHandler()
CONSOLE_HANDLER.setLevel(CONSOLE_LOG_LEVEL)
CONSOLE_HANDLER.setFormatter(logging.Formatter(LOG_FORMAT))

# 文件处理器
if not os.path.exists(LOG_FILE_PATH):
    os.makedirs(LOG_FILE_PATH)
FILE_HANDLER = logging.FileHandler(LOG_FILE_PATH / f'engine_{time_str}.log')
FILE_HANDLER.setLevel(FILE_LOG_LEVEL)
FILE_HANDLER.setFormatter(logging.Formatter(LOG_FORMAT))

# KEYS
ZHIPU_KEY = "3fe121b978f1f456cfac1d2a1a9d8c06.iQsBvb1F54iFYfZq"
OPENAI_KEY = "sk-hJs89lkQMzlzoOcADb6739A9091d41229c2c3c0547932fBe"
OPENAI_BASE = "https://api.qaqgpt.com/v1"
OPENAI_MODEL = "gpt-3.5-turbo-16k"

# get OPENAI KEY and BASE_URL from local json file
OPENAI_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "llm_config.json")
openai_config_data = json.load(open(OPENAI_CONFIG_PATH, "r"))

ACTION_MODEL = openai_config_data["ACTION_MODEL"]

# PACKS
INIT_PACK = json.loads(
    """
{
        "func":"init",
		 "npc":"{npc_list}",
		 "knowledge":{
			"all_actions": "{all_actions}",
			 "all_places": "{all_places}",
			 "all_moods": "{all_moods}",
			 "all_people": "{all_people}"
				     },
   		"language": "{language}"
}
"""
)

NPC_CONFIG = json.loads(
    """
    {
        "name": "{name}",
        "desc": "{desc}",
        "mood": "{mood}",
        "location": "{location}",
        "memory": "{memory}"
    }
"""
)

CONV_CONFIG = json.loads(
    """
    {
        "func": "create_conversation",
        "npc": "{npc}",
        "location": "{location}",
        "topic": "{topic}",
        "observations": "{observations}",
        "starting": "{starting}",
        "player_desc": "{player_desc}",
        "memory_k": "{memory_k}",
        "length": "{length}"
    }
"""
)

CONV_SCRIPT = json.loads(
    """
    {
        "name": "conversation",
        "id": "{id}",
        "length": "{length}",
        "location": "{location}",
        "lines": "{lines}"
    }
"""
)

CONV_CNFM = json.loads(
    """
    {
        "func": "confirm_conversation_line",
        "conversation_id": "{id}",
        "index": "{index}"
    }
"""
)

CONV_LINE = json.loads(
    """
    {
    "type": "{type}",
    "state": "{state}",
    "name": "{name}",
    "mood": "{mood}",
    "words": "{words}",
    "action": "{action}"
    }
"""
)

CONV_RECRE = json.loads(
    """
    {
        "func": "re_create_conversation",
        "id": "{id}",
        "character": "{character}",
        "interruption": "{interruption}",
        "player_desc": "{player_desc}",
        "length": "{length}"
    }
"""
)

ALL_ACTIONS = ["stay", "move", "chat"]
ALL_PLACES = ["李大爷家", "王大妈家", "广场", "瓜田", "酒吧", "警局"]
ALL_MOODS = ["正常", "焦急", "严肃", "开心", "伤心"]

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
"""
LLM api config
"""

"""
百度
"""
BAIDU_API_CONFIG = {

    "API_KEY": "qq7WLVgNX88unRoUVLtNz8fQ",
    "SECRET_KEY": "gA3VOdcRnGM4gKKkKKi93A79Dwevm3zo",  # gA3VOdcRnGM4gKKkKKi93A79Dwevm3zo
    "API_BASE": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/eb-instant?access_token=",
    "URL": "https://aip.baidubce.com/oauth/2.0/token",
    'ACCESS_TOKEN': None
}
CPM_BEE_API_CONFIG = {
    "CLIENT_NAME": 'sagemaker-runtime',
    "CLIENT_REGION": 'us-west-2',
    "AWS_ACCESS_KEY_ID": "AKIAQSLD5VQOWP3HFUHU",
    "AWS_SECRET_ACCESS_KEY": "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",
    "ENDPOINT_NAME": 'cpm-bee-230915134716SHWT',
    "MAX_NEW_TOKENS": 1024
}
BAICHUAN2_CONFIG = {
    "REGION_NAME": "us-east-1",
    "ACCESS_KEY": "AKIAQ33DL5YJDAN2VH4L",
    "SECRET_KEY": "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",
    "ENDPOINT_NAME": "bc2-13b-stream-2023-10-22-11-39-50-913-endpoint",
    "MAX_LENGTH": 1024,
    "TEMPERATURE": 0.1,
    "TOP_P": 0.8
}
OPENAI_CONFIG = {
    "API_BASE": OPENAI_BASE,
    "API_KEY": OPENAI_KEY,
    "MAX_TOKENS": 1024,
    "TEMPERATURE": 0.5,
    "STOP": None
}
QWEN_CONFIG = {
    "API_BASE": "http://localhost:5001/v1",
    "API_KEY": "None",
}
GLM3_6B_CONFIG={
    "API_BASE":"http://127.0.0.1:5001",
}

# assert dim of hf model == dim of pinecone index
assert (
        PINECONE_CONFIG["pinecone_index_dim"] == NPC_MEMORY_CONFIG["hf_dim"]
), "dim of hf model != dim of pinecone index"
