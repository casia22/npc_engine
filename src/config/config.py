import json

# KEYS
ZHIPU_KEY = "3fe121b978f1f456cfac1d2a1a9d8c06.iQsBvb1F54iFYfZq"
OPENAI_KEY = "sk-8p38chfjXbbL1RT943B051229a224a8cBdE1B53b5e2c04E2"
OPENAI_BASE = "https://api.ai-yyds.com/v1"

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
   		"language":"{language}"
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
        "observation": "{observations}",
        "starting": "{starting}",
        "player_desc": "{player_desc}",
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
        "interruption": "{interruption}"
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
    "pinecone_api_key": PINECONE_CONFIG["pinecone_api_key"],
    "pinecone_environment": PINECONE_CONFIG["pinecone_environment"],
    "pinecone_index_name": PINECONE_CONFIG["pinecone_index_name"],
    "pinecone_index_dim": PINECONE_CONFIG["pinecone_index_dim"],
    "hf_token": HF_TOKEN,
    "hf_model_id": HF_EMBEDDING_SBERT_CHINESE["model_id"],
    "hf_dim": HF_EMBEDDING_SBERT_CHINESE["dim"],
    "hf_api_url": HF_EMBEDDING_SBERT_CHINESE["hf_url"],
    "hf_headers": {"Authorization": f"Bearer {HF_TOKEN}"},
}

# assert dim of hf model == dim of pinecone index
assert (
    PINECONE_CONFIG["pinecone_index_dim"] == NPC_MEMORY_CONFIG["hf_dim"]
), "dim of hf model != dim of pinecone index"


if __name__ == "__main__":
    pass
