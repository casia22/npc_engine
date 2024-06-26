"""
Filename: engine.py
Author: Mengshi, Yangzejun
Contact: ..., yzj_cs_ilstar@163.com
"""

import asyncio
import nest_asyncio
from concurrent.futures import ThreadPoolExecutor
import datetime
import json
import socket
import traceback
import uuid
from typing import List, Dict, Any, Tuple
from functools import partial

from nuwa.src.utils.fail_safe import FailSafe

nest_asyncio.apply()
import colorama
import openai
#import zhipuai
from pathlib import Path
import sys

from nuwa.src.npc.action import ActionItem
from nuwa.src.npc.npc import NPC
from nuwa.src.npc.knowledge import PublicKnowledge, SceneConfig
from nuwa.src.config.template import EnginePrompt
from nuwa.src.npc.conversation import Conversation

colorama.init()
from colorama import Fore, Style
from nuwa.src.config.config import NPC_MEMORY_CONFIG
from nuwa.src.utils.engine_logger import EngineLogger
from nuwa.src.utils.embedding import LocalEmbedding, HuggingFaceEmbedding, BaseEmbeddingModel

class NPCEngine:
    """
    项目的核心入口类，扮演着一个Router的角色，负责接受相应的包并出发对应函数返回结果给游戏。
    engine的实现是基于socket UDP的，并发处理主要靠coroutine实现。
    """
    def __init__(
        self,
        project_root_path: Path,
        engine_url="::1",
        engine_port=8199,
        game_url="::1",
        game_port=8084,
        logo=True,
    ):
        # 初始化项目日志
        # LOGGER配置
        engine_logger = EngineLogger(project_root_path=project_root_path)
        engine_logger.set_up()
        self.logger = engine_logger.get_logger("ENGINE")
        self.logger.info("initializing NPC-ENGINE")
        # 设置用户定义路径
        self.PROJECT_ROOT_PATH = project_root_path  # 用户输入的项目根目录
        self.CONFIG_PATH = self.PROJECT_ROOT_PATH / "config"
        # 读取LLM_CONFIG
        OPENAI_CONFIG_PATH = self.PROJECT_ROOT_PATH / "config" / "llm_config.json"
        openai_config_data = json.load(open(OPENAI_CONFIG_PATH, "r"))
        OPENAI_KEY = openai_config_data["OPENAI_CONFIG"]["OPENAI_KEYS_BASES"][0]["OPENAI_KEY"]
        OPENAI_BASE = openai_config_data["OPENAI_CONFIG"]["OPENAI_KEYS_BASES"][0]["OPENAI_BASE"]
        GENERAL_MODEL = openai_config_data["LLM_MODEL_SELECTION"]["GENERAL_MODEL"]  # general model实际上只能选择openai的model 应为目前conversation的model是自己实现的openai请求 没有走model_api
        ACTION_MODEL = openai_config_data["LLM_MODEL_SELECTION"]["ACTION_MODEL"]
        # model 设置
        self.model = GENERAL_MODEL
        self.action_model = ACTION_MODEL
        # key配置
        # zhipuai.api_key = ZHIPU_KEY
        openai.api_key = OPENAI_KEY
        openai.api_base = OPENAI_BASE

        if logo:
            print(
                Fore.BLUE
                + """
             _   _ ______  _____  _____  _   _  _____  _____  _   _  _____
            | \ | || ___ \/  __ \|  ___|| \ | ||  __ \|_   _|| \ | ||  ___|
            |  \| || |_/ /| /  \/| |__  |  \| || |  \/  | |  |  \| || |__
            | . ` ||  __/ | |    |  __| | . ` || | __   | |  | . ` ||  __|
            | |\  || |    | \__/\| |___ | |\  || |_\ \ _| |_ | |\  || |___
            \_| \_/\_|     \____/\____/ \_| \_/ \____/ \___/ \_| \_/\____/
            """
                + Style.RESET_ALL
            )
            print(
                """
                _
               | |
               | |__   _   _
               | '_ \ | | | |
               | |_) || |_| |
               |_.__/  \__, |
             _____      __/ |            _ ___  ___        _          _
            /  __ \    |___/            (_)|  \/  |       | |        (_)
            | /  \/  ___    __ _  _ __   _ | .  . |  __ _ | |_  _ __  _ __  __
            | |     / _ \  / _` || '_ \ | || |\/| | / _` || __|| '__|| |\ \/ /
            | \__/\| (_) || (_| || | | || || |  | || (_| || |_ | |   | | >  <
             \____/ \___/  \__, ||_| |_||_|\_|  |_/ \__,_| \__||_|   |_|/_/\_\\
                            __/ |
                           |___/
            """)
        # 加载引擎网络组件
        self.engine_port = engine_port
        self.engine_url = engine_url
        self.game_url = game_url
        self.game_port = game_port
        self.conversation_dict = {}
        self.npc_dict = {}
        self.npc_index_dict = {}
        self.action_dict = {}
        self.sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)  # 使用IPv6地址
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 添加这一行
        print(
            Fore.GREEN
            + f"listening on [::]:{self.engine_port}, sending data to {self.game_url}:{self.game_port}, using general llm model {self.model}, action llm model  {self.action_model}"
            + Style.RESET_ALL
        )
        self.sock.bind((engine_url, self.engine_port))  # 修改为IPv6地址绑定方式 todo:这里可能要改为::1

        # 加载模型embedding模型
        if NPC_MEMORY_CONFIG["hf_embedding_online"]:
            self.logger.info("using online embedding model")
            self.embedding_model = HuggingFaceEmbedding(model_name=NPC_MEMORY_CONFIG["hf_model_id"], vector_width=NPC_MEMORY_CONFIG["hf_dim"])
        else:
            self.logger.info("using local embedding model")
            self.embedding_model = LocalEmbedding(model_name=NPC_MEMORY_CONFIG["hf_model_id"], vector_width=NPC_MEMORY_CONFIG["hf_dim"])
        self.public_knowledge = PublicKnowledge(project_root_path=self.PROJECT_ROOT_PATH)
        self.fail_safe = FailSafe(self.embedding_model)

        self.logger.info("using local embedding model")
        self.logger.info("initialized NPC-ENGINE")
        try:
            self.loop = asyncio.get_event_loop()
            self.loop.run_until_complete(self.listen())
        except KeyboardInterrupt:
            self.logger.info("Detected Ctrl+C, exiting...")
            self.logger.info("Exiting...")
            self.sock.close()

    async def listen(self, buffer_size=400000):
        """
        监听端口，接收游戏发送的数据,并根据数据调用相应的函数
        :return:
        """
        print(f"listening on [::]:{self.engine_port}")
        self.logger.info(f"listening on [::]:{self.engine_port}")
        buffer = {}
        with ThreadPoolExecutor() as pool:
            while True:
                data, addr = self.sock.recvfrom(buffer_size)
                # 解析UDP数据包头部
                msg_id, packet_no, total_packets, pack = data.split(b"@", 3)
                packet_no = int(packet_no)
                total_packets = int(total_packets)
                # 缓存数据包
                if msg_id not in buffer:
                    buffer[msg_id] = [b""] * total_packets
                buffer[msg_id][packet_no - 1] = pack
                # 检查是否所有数据包都已接收
                if not any(part == b"" for part in buffer[msg_id]):
                    # 重组消息
                    msg_str = b"".join(buffer[msg_id]).decode("utf-8")
                    json_data = json.loads(msg_str)
                    self.logger.debug(f"received packet {json_data}")

                    try:
                        # 按照完整数据包的func字段调用相应的函数
                        if "func" in json_data.keys():
                            func_name = json_data["func"]
                            if hasattr(self, func_name):
                                func = getattr(self, func_name)
                                func_partial = partial(func, json_data)
                                self.loop.run_in_executor(pool, func_partial)
                            if "init" in json_data["func"]:
                                self.logger.info(f"[NPC-ENGINE]<UDP INIT>: {json_data}")
                            if "create_conversation" in json_data["func"]:
                                self.logger.info(f"[NPC-ENGINE]<create_conversation>: {json_data}")
                            if "confirm_conversation" in json_data["func"]:
                                self.logger.info(f"[NPC-ENGINE]<confirm_conversation>: {json_data}")
                            if "close" in json_data["func"]:
                                self.logger.info(f"[NPC-ENGINE]<close>: {json_data}")
                    except json.JSONDecodeError:
                        # print the raw data and the address of the sender and the time and the traceback
                        print(
                            f"json decode error: {data} from {addr} at {datetime.datetime.now()}"
                        )
                        # print error getting key
                        print(f"error getting key: {json_data['func']}")
                        self.logger.error(traceback.format_exc())
                    except KeyboardInterrupt:
                        self.logger.info("Detected Ctrl+C, exiting...")
                        self.sock.close()

                    except Exception as e:
                        print(f"error: {e}")
                        self.logger.error(traceback.format_exc())
                        pass

    def batch_search_memory(self, npcs: List[str], query: str, memory_k: int):
        """
        同步批量搜索NPC的记忆(可能存在性能问题)
        :param npcs:
        :param query:
        :param memory_k:
        :return:
        """
        # TODO：如果有性能问题，考虑是否需要异步
        memories_items = {}
        for npc in npcs:
            memories_items[npc.name] = npc.memory.search_memory(query_text=query,
                                         query_game_time="Time",
                                         k=memory_k)
        return memories_items

    def create_conversation(self, json_data):
        # TODO 考虑数据包是否需要传送state参数，不需要则可以直接删除
        """
        根据游戏发送的Conversation信息，创建Conversation剧本并返回；
        直到对话都被确认，Conversation才会被销毁.
        create_conversation游戏端发给引擎的包
        {
            "func": "create_conversation",
            "npc": ["王大妈","李大爷"],     # 参与对话的NPC
            "location": "李大爷家卧室",      # 对话地点
            "scenario_name": "李大爷家",
            "topic": "王大妈想要切了自己的西瓜给李大爷吃，并收钱", # 对话主题，可以留空，会自动生成topic
            "npc_states": [
                    {
                        "position": "李大爷家",
                        "observation": {
                                "people": ["李大爷", "村长", "隐形李飞飞"],
                                "items": ["椅子#1","椅子#2","椅子#3[李大爷占用]","床"],
                                "locations": ["李大爷家大门","李大爷家后门","李大爷家院子"]
                                        },
                        "backpack":["优质西瓜", "大砍刀", "黄金首饰"]
                    },
                    {
                        "position": "李大爷家",
                        "observation": {
                                "people": ["王大妈", "村长", "隐形李飞飞"],
                                "items": ["椅子#1","椅子#2","椅子#3[李大爷占用]","床"],
                                "locations": ["李大爷家大门","李大爷家后门","李大爷家院子"]
                                        },
                        "backpack":["黄瓜", "1000元", "老报纸"]
                    },
                    ],
            "starting": "你好，嫩们在干啥腻？",  # 玩家说的话，可选留空
            "player_desc": "玩家是一个疯狂的冒险者，喜欢吃圆圆的东西",  # 玩家的描述，可选留空
            "memory_k": 3,  # npc的记忆检索条数，必须填写
            "length": "M"  # 可以选择的剧本长度，S M L X 可选。
            "stream": True  # 是否需要采用流式数据包格式
        }

        :param json_data:
        :return:
        """
        # get language setup and obtain corresponding system_prompt for Conversation
        names: List[str] = json_data["npc"]
        states: List[Dict[str, Any]] = json_data["npc_states"]
        npc_refs = [self.npc_dict[name] for name in names]
        location: str = json_data["location"]
        scenario_name: str = json_data["scenario_name"]
        topic: str = json_data["topic"]
        length: str = json_data["length"]
        try:
            stream: bool = json_data["stream"]
        except:
            stream: bool = False
        memory_k = json_data["memory_k"]

        # 提取并整合所有人的观测信息
        share_obs_people_set = []
        share_obs_items_set = []
        share_obs_locations_set = []
        for npc_state in states:
            share_obs_people_set += npc_state["observation"]["people"]
            share_obs_items_set += npc_state["observation"]["items"]
            share_obs_locations_set += npc_state["observation"]["locations"]
        share_obs_people_set = list(set(share_obs_people_set))
        share_obs_items_set = list(set(share_obs_items_set))
        share_obs_locations_set = list(set(share_obs_locations_set))
        for name in names:
            if name in share_obs_people_set:
                share_obs_people_set.remove(name)
        share_observations = {
            "people" : share_obs_people_set,
            "items" : share_obs_items_set,
            "locations" : share_obs_locations_set
        }

        # 初始化群体描述、心情和记忆
        descs: List[str] = [npc.desc for npc in npc_refs] + [json_data["player_desc"]]
        moods: List[str] = [npc.mood for npc in npc_refs]
        memories: List[str] = []  # 记忆来自于init初始化中的记忆参数
        memories_items = self.batch_search_memory(npcs=npc_refs, query=topic, memory_k=memory_k)

        for name in names:
            items_list = memories_items[name]["related_memories"] + list(memories_items[name]["latest_memories"])
            memory_content = [m_item.text for m_item in items_list]
            memories.append(memory_content)

        # 初始化群体观察和常识
        starting: str = json_data["starting"]

        # 如果没有指定topic，就GPT生成一个
        if topic == "":
            #self.logger.error("There is no topic for creating a conversation.")
            topic = self.get_random_topic(names, location, scenario_name, states, self.language)

        # 根据语言选择对应的系统提示函数
        self.engine_prompt.reset_knowledge(knowledge=self.public_knowledge, scenario_name=scenario_name)
        system_prompt_func = getattr(
            self.engine_prompt, "prompt_for_conversation_" + self.language.lower()
        )
        system_prompt, query_prompt = system_prompt_func(
            names=names,
            location=location,
            topic=topic,
            descs=descs,
            moods=moods,
            memories=memories,  # init参数中的记忆、addmemory的记忆被添加到创建对话prompt里面
            share_observations=share_observations,
            starting=starting,
            length=length
        )
        convo = Conversation(
            names=names,
            location=location,
            scenario_name=scenario_name,
            topic=topic,
            share_observations=share_observations,
            system_prompt=system_prompt,
            query_prompt=query_prompt,
            language=self.language,
            model=self.model,
            stream = stream,
            sock = self.sock,
            game_url = self.game_url,
            game_port = self.game_port,
            project_root = self.PROJECT_ROOT_PATH
        )  # todo: 这里engine会等待OPENAI并无法处理新的接收

        self.conversation_dict[convo.convo_id] = convo
        # script = convo.generate_script()

        # 调用剧本生成函数生成剧本
        convo.generate_script(system_prompt, query_prompt)

    def re_create_conversation(self, json_data):
        # TODO 对话的再创建的提示词中缺乏对原对话房间角色的信息描述，且没有任何观测描述，需要和create统一一下
        """
        根据游戏发送的Conversation打断包中id，找到原来的Conversation对象，重新生成剧本并返回；
        打断包例:
        {
        "func":"re_create_conversation",
        "id":"1234567890",
        "character":"小明",
        "interruption": "我认为这儿需要在交流", # 玩家插入发言,可以留空
        "player_desc": "是一名老师", # 玩家的个性描述
        "memory_k": 3,
        "length": "X",
        "stream": True,
        }

        location: str = "",
        topic: str = "",
        mood: str = "",
        descs: List[str] = None,
        memories: List[List[str]] = None,
        history: List[str] = None,

        :param json_data:
        :return:
        """
        conversation_id = json_data["id"]
        character = json_data["character"]
        interruption = json_data["interruption"]
        player_desc = json_data["player_desc"]
        memory_k = json_data["memory_k"]
        length = json_data["length"]
        stream = json_data["stream"]

        if conversation_id in self.conversation_dict.keys():
            convo = self.conversation_dict[conversation_id]
            names = convo.names
            location = convo.location
            topic = convo.topic
            mood = self.npc_dict[character].mood
            npc_refs = [self.npc_dict[name] for name in names]
            descs = [npc.desc for npc in npc_refs]

            if character != "":
                npc_refs.append(self.npc_dict[character])
                descs += [self.npc_dict[character].desc]
            else:
                descs += [player_desc]

            memories: List[str] = []  # 记忆来自于init初始化中的记忆参数
            memories_items = self.batch_search_memory(npcs=npc_refs, query=topic, memory_k=memory_k)

            for name in names:
                items_list = memories_items[name]["related_memories"] + list(memories_items[name]["latest_memories"])
                memory_content = [m_item.text for m_item in items_list]
                memories.append(memory_content)

            history = convo.script_perform
            share_observations = convo.share_observations

            self.engine_prompt.reset_knowledge(knowledge=self.public_knowledge, scenario_name=convo.scenario_name)
            system_prompt, query_prompt = self.engine_prompt.prompt_for_re_creation(names = names,
                                                                                    location = location,
                                                                                    topic = topic,
                                                                                    character = character,
                                                                                    mood = mood,
                                                                                    descs = descs,
                                                                                    memories = memories,
                                                                                    share_observations = share_observations,
                                                                                    interruption = interruption,
                                                                                    length = length,
                                                                                    history = history)
            convo.set_stream(stream)
            convo.re_generate_script(character, system_prompt, query_prompt)

    def get_random_topic(
        self, names: List[str], location: str, scenario_name:str, states: Dict[str, Dict[str, Any]], language: str
    ) -> str:
        """
        使用GPT为对话生成一个随机的topic
        :param names: 参与对话的NPC名称列表
        :param location: 对话地点
        :param scenario_name: 对话场景
        :param states: 角色状态信息
        :param language: 语言
        :return: 随机生成的话题
        """
        self.engine_prompt.reset_knowledge(knowledge=self.public_knowledge, scenario_name=scenario_name)
        system_topic, query_prompt = self.engine_prompt.prompt_for_topic(
            names=names, location=location, states=states, language=language
        )
        response = openai.ChatCompletion.create(
            model=self.model, messages=[system_topic, query_prompt]
        )
        topic: str = response["choices"][0]["message"]["content"].strip()
        return topic

    def init(self, json_data):
        """
        初始化NPC对象，ACTION对象。
        1.按init包中的scene字段加载指定场景的NPC和ACTION。
            如果scenario文件中的npc已经初始化过了，就略过，不再初始化。
        2.如果init包npc字段不为空，那就在内存中覆盖掉对应的NPC对象。
                                如果不存在这个NPC，就新建一个NPC对象。
        3.如果init包npc字段不为空，会添加UDP参数的NPC到people knowledge里面

        例子：
        {
        "func":"init",
        # 必填字段，代表在什么场景初始化
        "scene_name":"雁栖村"
        "language": "E" or "C",
        # 下面是🉑️选
        "npc": [], # 可以留空，默认按照your_scene_name.json初始化场景NPC。非空则在之前基础上添加。
        }
        :param json_data:
        :return:
        """
        try:
            # 获得场景对象
            scene_name = json_data["scene_name"]
            scene_config: SceneConfig = self.public_knowledge.get_scene(scene_name=scene_name)

            # 根据知识创建引擎提示词的实例
            self.engine_prompt = EnginePrompt(knowledge=self.public_knowledge, scenario_name=scene_name)
            self.logger.debug(f"generate engine prompt done")

            # 按照action字段，添加新的ACTION
            for action_name in self.public_knowledge.get_actions(scenario_name=scene_name):
                with open(self.CONFIG_PATH / "action" / (action_name + ".json"), "r", encoding="utf-8") as file:
                    action_json = json.load(file)
                action_item = ActionItem(
                    name=action_json["name"],
                    definition=action_json['definition'],
                    example=action_json['example'],
                    log_template=action_json["log_template"],
                    multi_param=action_json["multi_param"],
                )
                # 设置语义向量
                action_item.vec = self.embedding_model.embed_text(action_item.name)
                self.action_dict[action_item.name] = action_item
                self.logger.debug(f"<DISK ACT INIT> action:{action_item.name}")

            # 按照npc字段，添加磁盘中JSON对应的NPC
            for npc_name in self.public_knowledge.get_people(scenario_name=scene_name):
                try:
                    with open(self.CONFIG_PATH / "npc" / (npc_name + ".json"), "r", encoding="utf-8") as file:
                        npc_json = json.load(file)
                except FileNotFoundError:
                    self.logger.warning(f"NPC {npc_name} not found in disk, skip")
                    continue
                except json.decoder.JSONDecodeError:
                    self.logger.warning(f"NPC {npc_name} json decode error, check the format of {npc_name}.json, skip")
                    continue
                """
                {
                  "name":"李大爷",
                  "desc": "李大爷是一个普通的种瓜老头，戴着文邹邹的金丝眼镜，喜欢喝茶，平常最爱吃烤烧鸡喝乌龙茶；上午他喜欢呆在家里喝茶，下午他会在村口卖瓜，晚上他会去瓜田护理自己的西瓜",
                  "mood":"开心",
                  "scenario_name": "李大爷家",
                  "npc_state": {
                        "position": "李大爷家卧室",
                        "observation": {
                                "people": ["王大妈", "村长", "隐形李飞飞"],
                                "items": ["椅子#1","椅子#2","椅子#3[李大爷占用]","床"],
                                "locations": ["李大爷家大门","李大爷家后门","李大爷家院子"]
                                      },
                        "backpack":["黄瓜", "1000元", "老报纸"]
                             },
                  "memory":["20年前在工厂表现优异获得表彰。","15年前在工厂收了两个徒弟。","8年前李大爷的两个徒弟在工厂表现优异都获得表彰。","6年前从工厂辞职并过上普通的生活。","4年前孩子看望李大爷并带上大爷最爱喝的乌龙茶。"]
                }
                """
                # 如果已经存在NPC在内存中，则不再config从加载覆盖
                npc_name = npc_json["name"]
                if npc_name in self.npc_dict.keys():
                    self.logger.debug(f"NPC {npc_name} 已经被初始化，跳过")
                    continue
                
                # 根据名字生成姓名序号，以便在后续生成每个NPC的唯一hash值
                if npc_name in self.npc_index_dict:
                    self.npc_index_dict[npc_name] += 1
                elif npc_name not in self.npc_index_dict:
                    self.npc_index_dict[npc_name] = 1

                npc = NPC(
                    name=npc_name,
                    name_index=self.npc_index_dict[npc_name],
                    desc=npc_json["desc"],
                    public_knowledge=self.public_knowledge,
                    scenario_name=scene_name,
                    # 初始化NPC的状态，目前背包和观察都初始化为空
                    state={
                        'position': npc_json["npc_state"]["position"],
                        'backpack': npc_json["npc_state"]["backpack"],
                        'ob_people': npc_json["npc_state"]["observation"]["people"],
                        'ob_items': npc_json["npc_state"]["observation"]["items"],
                        'ob_locations': npc_json["npc_state"]["observation"]["locations"]
                    },
                    action_dict=self.action_dict,
                    mood=npc_json["mood"],
                    memory=npc_json["memory"],
                    action_space=npc_json["action_space"],
                    model=self.action_model,
                    embedding_model=self.embedding_model,
                    project_root_path=self.PROJECT_ROOT_PATH
                )
                npc._init()
                self.npc_dict[npc.name] = npc
                self.logger.debug(f"<DISK NPC INIT>npc:{npc.name}")
            # 按照GAME回传的init包中的npc字段，添加新的NPC
            additional_npc = []  # 由init数据包设置的新NPC
            if "npc" in json_data:
                for npc_data in json_data["npc"]:
                    # 如果已经存在NPC在内存中，则依然从UDP参数覆盖(UDP参数我们认为有更高的优先级)
                    npc = NPC(
                        name=npc_data["name"],
                        desc=npc_data["desc"],
                        public_knowledge=self.public_knowledge,
                        scenario_name=scene_name,
                        # 初始化NPC的状态
                        state={
                            'position': npc_data["npc_state"]["position"],
                            'backpack': npc_data["npc_state"]["backpack"],
                            'ob_people': npc_data["npc_state"]["observation"]["people"],
                            'ob_items': npc_data["npc_state"]["observation"]["items"],
                            'ob_locations': npc_data["npc_state"]["observation"]["locations"]
                        },
                        action_dict=self.action_dict,
                        mood=npc_data["mood"],
                        action_space=npc_data["action_space"],
                        memory=npc_data["memory"],
                        model=self.action_model,
                        embedding_model=self.embedding_model,
                        project_root_path=self.PROJECT_ROOT_PATH
                    )
                    npc._init()
                    self.npc_dict[npc.name] = npc
                    additional_npc.append(npc.name)
                    self.logger.debug(f"<UDP NPC INIT> npc:{npc.name}")
            # UDP发送过来的新NPC，也被视为people常识，knowledge需要更新
            appended_npc = [npc_name for npc_name in additional_npc if npc_name not in self.public_knowledge.get_people(scenario_name=scene_name)]
            self.public_knowledge.update_people(scenario_name=scene_name, content=list(set(scene_config.all_people + additional_npc)))
            self.logger.debug(f"knowledge update done, people:{self.public_knowledge.get_people(scenario_name=scene_name)}, "
                         f"appended npc:{appended_npc}")

            # language
            self.language = json_data["language"]
            self.send_data({"name": "inited", "status": "success"})
        except Exception as e:
            self.logger.error(f"init error:{traceback.format_exc()}")
            self.send_data({"name": "inited", "status": "failed"})

    def confirm_conversation_line(self, json_data):
        """
        接受确认包，将游戏发过来对应的conversation和idx 添加到 npc的memory中。
        例：
        {"func":"confirm_conversation_line",
         "conversation_id":"1234567890",
         "index":12
        } # index是对话的第几句话,从0开始计数,只有确认包发送后才会被添加到记忆里。

        :param json_data:
        :return:
        """
        try:
            conversation_id = json_data["conversation_id"]
            index = json_data["index"]
            if conversation_id in self.conversation_dict:
                convo = self.conversation_dict[conversation_id]
                memory_add, mood_change = convo.add_temp_memory(index)
                if len(memory_add.keys()) != 0:
                    self.npc_information_update(memory_add, mood_change)
        except Exception as e:
            self.logger.error(f"confirm_conversation_line error:{traceback.format_exc()}")

    def npc_information_update(self, memory_add, mood_change):
        """
        将对话的内容添加到对应NPC的记忆list中，以第三人称的方式
        例如：
            李大爷 talked with 王大妈,村长 from 2021-01-01 12:00:00 to 2021-01-01 12:00:00.
            (被放入李大爷的记忆中)
        :params memory_add:
        :return:
        """
        # 得到对话类中的人名列表
        for name in memory_add.keys():
            npc = self.npc_dict[name]
            npc.memory.add_memory_text(text="\n".join(memory_add[name]), game_time="Time")
            self.logger.debug(f"npc {name} add conversation pieces into memory done")
            npc.mood = mood_change[name]
            self.logger.debug(f"npc {name} update mood done")

    def action_done(self, json_data: Dict[str, Any]):
        """
        如果游戏成功执行了动作，那么就将动作和参数存入记忆中 更新purpose 生成新的action然后传给GAME
        如果执行失败，那就结合失败原因存入记忆
        GAME传回数据例子:
        {
            "func":"action_done",
            "npc_name": "王大妈",
            "status": "success/fail",
            "scenario_name": "李大爷家",
            "npc_state": {
              "position": "李大爷家卧室",
              "observation": {
                      "people": ["李大爷", "村长", "李飞飞"],
                      "items": ["椅子#1","椅子#2","椅子#3[李大爷占用]","床"],
                      "locations": ["李大爷家大门","李大爷家后门","李大爷家院子"]
                            },
              "backpack":["优质西瓜", "大砍刀", "黄金首饰"]
            },
            "time": "2021-01-01 12:00:00", # 游戏世界的时间戳

            "action":"mov",
            "object":"李大爷家",
            "parameters":[],
            "reason": "", # "王大妈在去往‘警察局’的路上被李大爷打断"
        }

        本函数返回给GAME的数据例子:
        {
        "name":"action",
        "npc_name":"李大妈",
        "action":"mov",
        "object":"李大爷家",
        "parameters":[],
        }
        """
        try:
            status:str = json_data["status"]
            action_item:ActionItem = self.action_dict[json_data["action"]]
            npc_name:str = json_data["npc_name"]
            scenario_name:str = json_data["scenario_name"]
            npc:NPC = self.npc_dict[npc_name]
            action_log: str = action_item.get_log(status, npc_name, json_data["object"], json_data["parameters"],
                                                      reason=json_data["reason"])
            # 更新NPC的状态
            npc.set_state(json_data['npc_state'])
            # 更新NPC的场景属性(自动更新scenario_knowledge和自动更新scenario属性)
            npc.set_scenario(scenario_name)
            # 添加NPC记忆
            npc.memory.add_memory_text(action_log, game_time=json_data["time"])
            # 更新purpose
            npc.purpose = npc.get_purpose(time=json_data["time"], k=3)
            # 生成新的action
            new_action: Dict[str, Any] = npc.get_action(time=json_data["time"], fail_safe=self.fail_safe, k=3)
            action_packet = new_action
            action_packet["name"] = "action"
            # 发送新的action到环境
            self.send_script(action_packet)
            self.logger.debug(f"""[NPC-ENGINE]<action_done> 
                            npc_name:{npc.name}, 
                            purpose: {npc.purpose},
                            action:{action_packet}
                            to game""")
        except Exception as e:
            self.logger.error(f"[NPC-ENGINE]<action_done> error:{traceback.format_exc()}")

    def wake_up(self, json_data):
        """
        NPC激活，
            游戏端检测到有NPC长时间无action/游戏初始化init时 被调用
            根据observation，location等字段，生成一个action，然后将action发送给游戏端

        GAME发送过来的数据例子:
        {
            "func":"wake_up",
            "npc_name": "王大妈",
            "scenario_name": "李大爷家",
            "npc_state": {
              "position": "李大爷家卧室",
              "observation": {
                      "people": ["李大爷", "村长", "李飞飞"],
                      "items": ["椅子#1","椅子#2","椅子#3[李大爷占用]","床"],
                      "locations": ["李大爷家大门","李大爷家后门","李大爷家院子"]
                            },
              "backpack":["优质西瓜", "大砍刀", "黄金首饰"]
            },
            "time": "2021-01-01 12:00:00", # 游戏世界的时间戳
        }

        本函数返回给GAME的数据例子:
        {
            "name":"action",
            "npc_name":"王大妈",
            "action":"chat",
            "object":"李大爷",
            "parameters":["你吃饭了没？"],
        }
        :param json_data:
        :return:
        """
        try:
            # 获得NPC的引用
            npc_name = json_data["npc_name"]
            npc = self.npc_dict[npc_name]
            # 更新NPC的状态
            npc.set_state(json_data['npc_state'])
            npc.set_scenario(scenario=json_data["scenario_name"])
            # 更新NPC的purpose
            npc.purpose = npc.get_purpose(time=json_data["time"], k=3)
            # 生成新的action
            new_action = npc.get_action(time=json_data["time"], fail_safe=self.fail_safe, k=3)
            action_packet = new_action
            action_packet["name"] = "action"
            # 发送新的action到环境
            self.send_script(action_packet)
            self.logger.debug(f"""[NPC-ENGINE]<wake_up> 
                            npc_name: {npc.name}, 
                            purpose: {npc.purpose} 
                            action: {action_packet} 
                            to game""")
        except Exception as e:
            self.logger.error(f"[NPC-ENGINE]<wake_up> error: {traceback.format_exc()}")

    def talk2npc(self, json_data):
        """
        玩家跟NPC进行交流,
            函数会先根据玩家对话检索相关记忆，产生回答、action和目的。
            玩家的问句和NPC的回答会被组合，放入记忆。
            (记忆条件下，同时产生purpose、action、回答，这样保证了高一致性)
            (action发给game后，自动进入action_done的loop)

        GAME发送过来的数据例子:
        {
            "func":"talk2npc",
            "npc_name":"警员1",
            "time": "2021-01-01 12:00:00", # 游戏世界的时间戳

            # NPC的状态
            "scenario_name": "警察局",
            "npc_state": {
              "position": "雁栖村入口",
              "observation": {
                      "people": ["囚犯阿呆","警员1","警员2"],
                      "items": ["椅子#1","椅子#2","椅子#3[李大爷占用]","床"],
                      "locations": ["李大爷家大门","李大爷家后门","李大爷家院子"]
                            },
              "backpack":["优质西瓜", "大砍刀", "黄金首饰"]
            },
            # player的信息
            "player_name":"旅行者小王",
            "speech_content":"你好，我是旅行者小王, 我要报警, 在林区中好像有人偷砍树",
            "items_visible": ["金丝眼镜", "旅行签证", "望远镜"],
            "state": "旅行者小王正在严肃地站着，衣冠规整，手扶着金丝眼镜",
        }

        本函数返回给GAME的数据例子:
        {
            "name":"talk_result",
            "npc_name":"王大妈",
            "answer":"你吃饭了没？"
            "actions": [{
                "name":"action",
                "npc_name":"王大妈",
                "action":"mov",
                "object":"雁栖村入口",
                "parameters":[],
                        }]
            }
        :param json_data:
        :return:
        """
        try:
            # 获得玩家信息
            player_name = json_data["player_name"]
            speech_content = json_data["speech_content"]
            items_visible = json_data["items_visible"]
            player_state = json_data["state"]

            # 获得NPC的引用
            npc_name = json_data["npc_name"]
            npc = self.npc_dict[npc_name]
            # 更新NPC的状态
            npc.set_state(json_data['npc_state'])
            npc.set_scenario(scenario=json_data["scenario_name"])

            # 对当前情景进行描述，并存入记忆
            memory_desc: str = f"{player_name}对{npc.name}说:{speech_content}"
            npc.memory.add_memory_text(memory_desc, game_time=json_data["time"])
            # 更新NPC的purpose
            # npc.purpose = await npc.get_purpose(time=json_data["time"], k=3) # todo:应该移动到response发送后面，强制依赖response更新新的action
            # 生成新的response
            response = npc.get_npc_response(player_name=player_name, player_speech=speech_content,
                                                    items_visible=items_visible, player_state_desc=player_state,
                                                    time=json_data["time"], fail_safe=self.fail_safe, k=3)

            response["name"] = "talk_result"
            # 发送新的action到环境
            self.send_script(response)
            self.logger.debug(f"""[NPC-ENGINE]<talk2npc> 
                            npc_name: {npc.name}, 
                            purpose: {npc.purpose},
                            answer: {response["answer"]}
                            action: {response["actions"]} 
                            to game""")
        except Exception as e:
            self.logger.error(f"[NPC-ENGINE]<talk2npc> error: {traceback.format_exc()}")

    def send_script(self, script):
        """
        将script发送给游戏
        :param script:
        :return:
        """
        # print item with appropriate color
        print(
            "[NPC-ENGINE]sending script:",
            Fore.GREEN,
            json.dumps(script).encode(),
            Style.RESET_ALL,
            "to",
            (self.game_url, self.game_port),
        )
        self.send_data(script)

    def send_data(self, data, max_packet_size=6000):
        """
        把DICT数据发送给游戏端口
        :param data:dict
        :param max_packet_size:
        :return:
        """
        # UUID作为消息ID
        msg_id = uuid.uuid4().hex
        # 将json字符串转换为bytes
        data = json.dumps(data).encode("utf-8")
        # 计算数据包总数
        packets = [
            data[i: i + max_packet_size] for i in range(0, len(data), max_packet_size)
        ]
        total_packets = len(packets)
        print(total_packets)

        for i, packet in enumerate(packets):
            # 构造UDP数据包头部
            print(
                "sending packet {} of {}, size: {} KB".format(
                    i + 1, total_packets, self.calculate_str_size_in_kb(packet)
                )
            )
            header = f"{msg_id}@{i + 1}@{total_packets}".encode("utf-8")
            # 发送UDP数据包
            self.sock.sendto(header + b"@" + packet, (self.game_url, self.game_port))

    def calculate_str_size_in_kb(self, string: bytes):
        # 获取字符串的字节数
        byte_size = len(string)
        # 将字节数转换成KB大小
        kb_size = byte_size / 1024
        return kb_size

    def save_npc_json(self):
        """
        保存NPC的json数据到本地
        :return:
        """
        self.logger.info(f"saving npc json, names:{self.npc_dict.keys()}")
        for npc in self.npc_dict.values():
            npc.save_memory()
        self.logger.info("npc json saved")

    def close(self, json_data):
        """
        关闭socket,结束Engine
        保存所有NPC的记忆到本地.
        可以被数据包触发：
            {
                "func":"close"
            }
        :return:
        """
        try:
            # 关闭socket
            self.sock.close()
            self.logger.debug("socket closed")
            # 保存所有NPC到本地
            self.save_npc_json()
            self.logger.info("Engine closing")
            # 退出程序
            sys.exit(0)
        except Exception as e:
            self.logger.error(f"[NPC-ENGINE]<close> error: {traceback.format_exc()}")
            sys.exit(0)

if __name__ == "__main__":
    import os
    PROJECT_ROOT_PATH = Path(os.path.abspath(__file__)).parent.parent.parent / "example_project"
    print("path:", PROJECT_ROOT_PATH)
    engine = NPCEngine(project_root_path=PROJECT_ROOT_PATH)