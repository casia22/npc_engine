import os
"""
使用https://hf-mirror.com镜像站下载模型,这里支持huggingface上所有的模型,不用翻墙,但是依然有可能会卡
"""
# 设置环境变量
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'


from huggingface_hub import hf_hub_download
from huggingface_hub import snapshot_download

snapshot_download(repo_id="uer/sbert-base-chinese-nli", local_dir=r'C:\python_code\npc_engine-main\nuwa\material\models\embedding')

"""
使用阿里的魔塔,也就是modelscope下载模型.这里下载模型会很快,但是模型不全,需要先查看有没有我们需要的模型
"""
# from modelscope import snapshot_download
# """
# 下载glm-6b
# """
# model_dir = snapshot_download("THUDM/chatglm3-6b", cache_dir=r'npc_engine/material/models/llm_model', revision ="v1.0.0")
# """
# 下载qwen1.8b int4量化
# """
#model_dir = snapshot_download('qwen/Qwen-1_8B-Chat-Int4',cache_dir=r"npc_engine/material/models/llm_model",revision ="v1.0.0")
