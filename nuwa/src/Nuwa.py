"""
面向用户程序的入口脚本，会被打包为exe/pkg/dmg等
条件：
    项目假设在当前目录下有project文件夹，里面有config/llm_config.json
功能：
    根据project文件夹的项目配置启动Nuwa
"""

import os
from pathlib import Path
from nuwa.src.engine import NPCEngine


if __name__ == "__main__":
    # 获取PROJECT_DIR
    PROJECT_DIR = os.path.join(os.getcwd(), "project")
    # 检测PROJECT_DIR是否存在
    if not os.path.exists(PROJECT_DIR):
        raise FileNotFoundError("PROJECT_DIR=./project not found in current directory.")
    # 检测PROJECT_DIR下是否有config文件夹
    if not os.path.exists(os.path.join(PROJECT_DIR, "config")):
        raise FileNotFoundError("config folder not found in PROJECT_DIR.")
    # 检测PROJECT_DIR下是否有llm_config.json
    if not os.path.exists(os.path.join(PROJECT_DIR, "config", "llm_config.json")):
        raise FileNotFoundError("llm_config.json not found in PROJECT_DIR/config.")
    # 启动Nuwa
    engine = NPCEngine(project_root_path=Path(PROJECT_DIR))



