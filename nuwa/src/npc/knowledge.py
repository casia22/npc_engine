"""
负责存储地点、人物等知识配置文件的Public knowledge类
"""
import json
import logging
import os
from typing import List, Dict
from pathlib import Path
import concurrent.futures

from nuwa.src.config.config import OPENAI_KEY, OPENAI_BASE, OPENAI_MODEL, CONSOLE_HANDLER, FILE_HANDLER, PROJECT_ROOT_PATH, MEMORY_DB_PATH, CONFIG_PATH

# LOGGER配置
logger = logging.getLogger("KNOWLEDGE")
CONSOLE_HANDLER.setLevel(logging.DEBUG)
logger.addHandler(CONSOLE_HANDLER)
logger.addHandler(FILE_HANDLER)
logger.setLevel(logging.DEBUG)


class SceneConfig:
    """
    SceneConfig类，用于初始化和存储场景配置。
    """

    def __init__(self, config_name: str):
        """
        初始化SceneConfig类。

        参数:
        config_name (str): 配置文件名（不包括.json扩展名）
        """
        self.config_name = config_name
        self.all_actions: List[str] = []
        self.all_places: List[str] = []
        self.all_moods: List[str] = []
        self.all_people: List[str] = []

        with open(CONFIG_PATH / "knowledge" / "scenes" / (self.config_name + ".json"), "r", encoding="utf-8") as file:
            scenario_json = json.load(file)

        self.all_actions = scenario_json.get('all_actions', [])
        self.all_places = scenario_json.get('all_places', [])
        self.all_moods = scenario_json.get('all_moods', [])
        self.all_people = scenario_json.get('all_people', [])



class PublicKnowledge:
    """
    PublicKnowledge类，用于加载和存储所有场景配置。
    它会在引擎刚启动的时候
    """

    def __init__(self, debug_mode=False):
        """
        初始化PublicKnowledge类。
        """
        self.scene_config_kv: Dict[str, SceneConfig] = {}
        self.debug_mode = debug_mode
        self._load_configs()
        # ["雁栖村","雁栖村丛林","雁栖村矿场","王大妈家","李大爷家","警察局"] 等等
        self.scene_names_knowledge: List[str] = self.get_config_names()
        logger.info("Public knowledge loaded.")

    def get_config_names(self) -> List[str]:
        """
        返回所有场景配置的名称。

        返回:
        List[str]: 所有场景配置的名称
        """
        return list(self.scene_config_kv.keys())


    def _load_configs(self):
        """
        加载所有的配置文件到字典中。
        """
        with concurrent.futures.ThreadPoolExecutor() as executor:
            config_files = [file for file in os.listdir(CONFIG_PATH / "knowledge" / "scenes") if file.endswith('.json')]
            futures = {executor.submit(self._load_config, file): file for file in config_files}

            for future in concurrent.futures.as_completed(futures):
                file = futures[future]
                try:
                    config_name, scene_config = future.result()
                    self.scene_config_kv[config_name] = scene_config
                except Exception as exc:
                    print(f'{file} generated an exception: {exc}')
            logger.debug(f"Loaded scenario knowledge: {config_files}")

    def _load_config(self, file: str) -> tuple:
        """
        加载单个配置文件并返回配置名和SceneConfig对象。

        参数:
        file (str): 配置文件名

        返回:
        tuple: 配置名和SceneConfig对象
        """
        config_name = file[:-5]  # 去掉.json后缀名
        scene_config = SceneConfig(config_name)
        return config_name, scene_config

    def get_scene(self, scene_name: str) -> SceneConfig:
        """
        返回指定名称的SceneConfig对象。

        参数:
        scene_name (str): 场景名称

        返回:
        SceneConfig: 对应的SceneConfig对象
        """
        return self.scene_config_kv.get(scene_name)

    def update_scene(self, scene_name: str, scene_config: SceneConfig):
        """
        更新指定名称的SceneConfig对象。

        参数:
        scene_name (str): 场景名称
        scene_config (SceneConfig): 对应的SceneConfig对象
        """
        self.scene_config_kv[scene_name] = scene_config

    def update_actions(self, scenario_name: str, content: List[str]):
        if scenario_name in self.scene_config_kv:
            self.scene_config_kv[scenario_name].all_actions = content

    def update_moods(self, scenario_name: str, content: List[str]):
        if scenario_name in self.scene_config_kv:
            self.scene_config_kv[scenario_name].all_moods = content

    def update_people(self, scenario_name: str, content: List[str]):
        if scenario_name in self.scene_config_kv:
            self.scene_config_kv[scenario_name].all_people = content

    def update_places(self, scenario_name: str, content: List[str]):
        if scenario_name in self.scene_config_kv:
            self.scene_config_kv[scenario_name].all_places = content

    def get_actions(self, scenario_name: str) -> List[str]:
        if scenario_name in self.scene_config_kv:
            return self.scene_config_kv[scenario_name].all_actions
        return []

    def get_moods(self, scenario_name: str) -> List[str]:
        if scenario_name in self.scene_config_kv:
            return self.scene_config_kv[scenario_name].all_moods
        return []

    def get_people(self, scenario_name: str) -> List[str]:
        if scenario_name in self.scene_config_kv:
            return self.scene_config_kv[scenario_name].all_people
        return []

    def get_places(self, scenario_name: str) -> List[str]:
        if scenario_name in self.scene_config_kv:
            return self.scene_config_kv[scenario_name].all_places
        return []

    def shutdown(self):
        """
        场景配置文件更新，如果是debug_mode就不更新到本地
        :return:
        """
        if not self.debug_mode:
            for scenario_name, scene_config in self.scene_config_kv.items():
                with open(CONFIG_PATH / "knowledge" / "scenes" / (scenario_name + ".json"), "w",
                          encoding="utf-8") as file:
                    json.dump({
                        'all_actions': scene_config.all_actions,
                        'all_places': scene_config.all_places,
                        'all_moods': scene_config.all_moods,
                        'all_people': scene_config.all_people
                    }, file)
        logger.info("Public knowledge shutdown.")


if __name__ == "__main__":
    # 创建PublicKnowledge对象
    public_knowledge = PublicKnowledge()

    # 尝试获取一个场景配置
    scene_name = '雁栖村'  # 请替换为你的实际场景名
    scene_config = public_knowledge.get_scene(scene_name)

    # 打印场景配置的信息
    if scene_config is not None:
        print(f"Config Name: {scene_config.config_name}")
        print(f"All Actions: {scene_config.all_actions}")
        print(f"All Places: {scene_config.all_places}")
        print(f"All Moods: {scene_config.all_moods}")
        print(f"All People: {scene_config.all_people}")
    else:
        print(f"No scene config found for {scene_name}")

