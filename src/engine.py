"""
Filename: engine.py
Author: Mengshi, Yangzejun
Contact: ..., yzj_cs_ilstar@163.com
"""

import asyncio
import nest_asyncio
import datetime
import json
import logging
import socket
import threading
import traceback
import uuid
from typing import List, Dict, Any, Tuple
nest_asyncio.apply()

import colorama
import openai
import zhipuai

# 这部分代码保证项目能被python解释器搜索到
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from npc_engine.src.npc.action import ActionItem
from npc_engine.src.npc.npc import NPC
from npc_engine.src.config.template import EnginePrompt
from npc_engine.src.npc.conversation import Conversation

colorama.init()
from colorama import Fore, Style
from npc_engine.src.config.config import (OPENAI_BASE, OPENAI_KEY, ZHIPU_KEY,CONFIG_PATH,
                                          CONSOLE_HANDLER,FILE_HANDLER,PROJECT_ROOT_PATH)

# key配置
zhipuai.api_key = ZHIPU_KEY
openai.api_key = OPENAI_KEY
openai.api_base = OPENAI_BASE

# LOGGER配置
logger = logging.getLogger("ENGINE")
CONSOLE_HANDLER.setLevel(logging.DEBUG)
logger.addHandler(CONSOLE_HANDLER)
logger.addHandler(FILE_HANDLER)
logger.setLevel(logging.DEBUG)

class NPCEngine:
    def __init__(
        self,
        engine_url="::1",
        engine_port=8199,
        game_url="::1",
        game_port=8084,
        model="gpt-3.5-turbo-16k",
        logo=True,
    ):
        logger.info("initializing NPC-ENGINE")
        self.knowledge = {}
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
        self.engine_port = engine_port
        self.engine_url = engine_url
        self.game_url = game_url
        self.game_port = game_port
        self.conversation_dict = {}
        self.npc_dict = {}
        self.action_dict = {}
        self.sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)  # 使用IPv6地址
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 添加这一行
        # color print
        print(
            Fore.GREEN
            + f"listening on [::]:{self.engine_port}, sending data to {self.game_url}:{self.game_port}, using model {model}"
            + Style.RESET_ALL
        )
        self.sock.bind((engine_url, self.engine_port))  # 修改为IPv6地址绑定方式 todo:这里可能要改为::1
        self.model = model
        self.listen_thread = threading.Thread(target=self.listen)
        self.listen_thread.start()
        logger.info("initialized NPC-ENGINE")

    def listen(self, buffer_size=40000):
        """
        监听端口，接收游戏发送的数据,并根据数据调用相应的函数
        :return:
        """
        print(f"listening on [::]:{self.engine_port}")
        logger.info(f"listening on [::]:{self.engine_port}")
        buffer = {}
        while True:
            data, addr = self.sock.recvfrom(buffer_size)
            # 解析UDP数据包头部
            # print(data)
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
                logger.debug(f"received packet {json_data}")
                FILE_HANDLER.flush()
                try:
                    # 按照完整数据包的func字段调用相应的函数
                    if "func" in json_data.keys():
                        func_name = json_data["func"]
                        if hasattr(self, func_name):
                            func = getattr(self, func_name)
                            asyncio.run(func(json_data))
                        # test
                        if "init" in json_data["func"]:
                            logger.info(f"[NPC-ENGINE]<UDP INIT>: {json_data}")
                        if "create_conversation" in json_data["func"]:
                            logger.info(f"[NPC-ENGINE]<create_conversation>: {json_data}")
                        if "confirm_conversation" in json_data["func"]:
                            logger.info(f"[NPC-ENGINE]<confirm_conversation>: {json_data}")

                except json.JSONDecodeError:
                    # print the raw data and the address of the sender and the time and the traceback
                    print(
                        f"json decode error: {data} from {addr} at {datetime.datetime.now()}"
                    )
                    # print error getting key
                    print(f"error getting key: {json_data['func']}")
                    logger.error(traceback.format_exc())
                except Exception as e:
                    print(f"error: {e}")
                    logger.error(traceback.format_exc())
                    pass

    def batch_search_memory(self, 
            npcs: List[str],
            query: str,
            memory_k: int):
        tasks = {}
        memories_items = {}
        loop = asyncio.get_event_loop()
        for npc in npcs:
            new_task = loop.create_task(npc.memory.search_memory(query_text = query, 
                                        query_game_time = "Time", 
                                        k = memory_k))
            tasks[npc.name] = new_task

        for _, task in tasks.items():
                loop.run_until_complete(task)

        for name, task in tasks.items():
            memories_items[name] = task.result()

        return memories_items

    async def create_conversation(self, json_data):
        """
        根据游戏发送的Conversation信息，创建Conversation剧本并返回；
        直到对话都被确认，Conversation才会被销毁.
        create_conversation游戏端发给引擎的包
        {
            "func": "create_conversation",
            "npc": ["王大妈","李大爷"],     # 参与对话的NPC
            "location": "李大爷家",      # 对话地点
            "topic": "王大妈想要切了自己的西瓜给李大爷吃，并收钱", # 对话主题，可以留空，会自动生成topic
            "npc_states": {
                    "王大妈": {
                        "position": "李大爷家",
                        "observation": {
                                "people": ["李大爷", "村长", "隐形李飞飞"],
                                "items": ["椅子#1","椅子#2","椅子#3[李大爷占用]","床"],
                                "locations": ["李大爷家大门","李大爷家后门","李大爷家院子"]
                                        },
                        "backpack":["优质西瓜", "大砍刀", "黄金首饰"]
                            },
                    "李大爷": {
                        "position": "李大爷家",
                        "observation": {
                                "people": ["王大妈", "村长", "隐形李飞飞"],
                                "items": ["椅子#1","椅子#2","椅子#3[李大爷占用]","床"],
                                "locations": ["李大爷家大门","李大爷家后门","李大爷家院子"]
                                        },
                        "backpack":["黄瓜", "1000元", "老报纸"]
                            },
                        },
            "starting": "你好，嫩们在干啥腻？",  # 玩家说的话，可选留空
            "player_desc": "玩家是一个疯狂的冒险者，喜欢吃圆圆的东西",  # 玩家的描述，可选留空
            "memory_k": 3,  # npc的记忆检索条数，必须填写
            "length": "M"  # 可以选择的剧本长度，S M L X 可选。 
        }

        :param json_data:
        :return:
        """
        # get language setup and obtain corresponding system_prompt for Conversation
        names: List[str] = json_data["npc"]
        states: Dict[str, Dict[str, Any]] = json_data["npc_states"]
        npc_refs = [self.npc_dict[name] for name in names]
        location: str = json_data["location"]
        topic: str = json_data["topic"]
        length: str = json_data["length"]
        memory_k = json_data["memory_k"]

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
        all_actions: List[str] = self.knowledge["actions"]
        all_places: List[str] = self.knowledge["places"]
        all_people: List[str] = self.knowledge["people"]
        all_moods: List[str] = self.knowledge["moods"]
        starting: str = json_data["starting"]

        # 如果没有指定topic，就GPT生成一个
        if topic == "":
            #logger.error("There is no topic for creating a conversation.")
            topic = self.get_random_topic(names, location, states, self.language)

        # 根据语言选择对应的系统提示函数
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
            states = states,
            starting=starting,
            length=length
        )

        # 创建Conversation，存入对象字典，生成剧本
        convo = Conversation(
            names=names,
            location=location,
            topic=topic,
            system_prompt=system_prompt,
            query_prompt=query_prompt,
            language=self.language,
            model=self.model,
        )  # todo: 这里engine会等待OPENAI并无法处理新的接收

        self.conversation_dict[convo.convo_id] = convo
        # script = convo.generate_script()

        # 发送整个剧本
        self.send_script(convo.script)

    async def re_create_conversation(self, json_data):
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

        if conversation_id in self.conversation_dict:
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

            system_prompt, query_prompt = self.engine_prompt.prompt_for_re_creation(names = names,
                                                                                    location = location,
                                                                                    topic = topic,
                                                                                    character = character,
                                                                                    mood = mood,
                                                                                    descs = descs,
                                                                                    memories = memories,
                                                                                    interruption = interruption,
                                                                                    length = length,
                                                                                    history = history)
            script = convo.re_generate_script(character, system_prompt, query_prompt)
            self.send_script(script)

    async def get_random_topic(
        self, names: List[str], location: str, states: Dict[str, Dict[str, Any]], language: str
    ) -> str:
        """
        使用GPT为对话生成一个随机的topic
        :param names: 参与对话的NPC名称列表
        :param location: 对话地点
        :param states: 角色状态信息
        :param language: 语言
        :return: 随机生成的话题
        """
        system_topic, query_prompt = self.engine_prompt.prompt_for_topic(
            names=names, location=location, states=states, language=language
        )
        response = openai.ChatCompletion.create(
            model=self.model, messages=[system_topic, query_prompt]
        )
        topic: str = response["choices"][0]["message"]["content"].strip()
        return topic

    async def init(self, json_data):
        """
        初始化NPC对象，ACTION对象。
        1.读取game_world.json文件，初始化NPC和ACTION.
        2.如果init包npc字段不为空，那就在内存中覆盖掉对应的NPC对象。
                                如果不存在这个NPC，就新建一个NPC对象。
        例子：
        {"func":"init",
                # 必填字段，代表在什么场景初始化
                "scene":"default_village",
                "language":"E" or "C"
                # 下面是🉑️选
                "npc":[
                    {"name":"李大爷",
                    "desc":"是个好人",
                    "mood":"正常",
                    "position":"李大爷家",
                    "memory":[ ]},

                    {"name":"王大妈",
                    "desc":"是个好人",
                    "mood":"焦急",
                    "position":"王大妈家",
                    "memory":[ ]}
                      ], # 可以留空，默认按照game_world.json+scene初始化场景NPC。非空则在之前基础上添加。

        }
        :param json_data:
        :return:
        """
        # 先读取game_world.json
        game_world_path = CONFIG_PATH / "knowledge" / "game_world.json"
        with open(game_world_path, "r", encoding="utf-8") as file:
            game_world_json = json.load(file)
        all_places_config:List[str] = game_world_json["all_places"]  # ["default_village","forest","mine"] 读取对应场景json
        scenes_permitted:List[str] = all_places_config  # ["default_village","forest","mine"] 顶层场景总览

        # 按照scene字段，加载指定场景json
        assert json_data["scene"] in scenes_permitted, f"场景{json_data['scene']}不在允许的场景列表中{scenes_permitted}"
        assert len(all_places_config) > 0, "场景列表为空"
        # 初始化列表
        npc_list = []
        action_list = []
        moods_permitted = []
        scene_subplaces_permitted = []

        scene_name = json_data["scene"]
        with open(CONFIG_PATH / "knowledge" / "scenes" / (scene_name + ".json"), "r", encoding="utf-8") as file:
            scenario_json = json.load(file)
        npc_list.extend(scenario_json["all_people"])  # ["李大爷", "王大妈","村长","警长"]
        action_list.extend(scenario_json["all_actions"])  # ["mov", "get", "put"],
        moods_permitted.extend(scenario_json["all_moods"])  # ["正常", "焦急", "严肃", "开心", "伤心"]
        scene_subplaces_permitted.extend(scenario_json["all_places"])  # ["村口","李大爷家", "王大妈家", "广场", "村长家", "瓜田", "酒吧", "警局","矿井入口","丛林入口"],

        # 准备self.knowledge
        self.knowledge["places"] = scene_subplaces_permitted + scenes_permitted
        self.knowledge["actions"] = action_list
        self.knowledge["moods"] = moods_permitted
        self.knowledge["people"] = npc_list

        # 根据知识创建引擎提示词的实例
        self.engine_prompt = EnginePrompt(knowledge=self.knowledge)
        logger.debug(f"generate engine prompt done")

        # 按照npc字段，添加新的NPC
        for npc_name in npc_list:
            with open(CONFIG_PATH / "npc" / (npc_name + ".json"), "r", encoding="utf-8") as file:
                npc_json = json.load(file)
            npc = NPC(
                name=npc_json["name"],
                desc=npc_json["desc"],
                knowledge=self.knowledge,
                # 初始化NPC的状态，目前背包和观察都初始化为空
                state={
                    'position': npc_json["position"],
                    'backpack': [],
                    'ob_people': [],
                    'ob_items': [],
                    'ob_locations': []
                },
                mood=npc_json["mood"],
                memory=npc_json["memory"],
                model=self.model,
            )
            self.npc_dict[npc.name] = npc
            logger.debug(f"<DISK NPC INIT>npc:{npc.name}")
        if "npc" in json_data:
            for npc_data in json_data["npc"]:
                npc = NPC(
                    name=npc_data["name"],
                    desc=npc_data["desc"],
                    knowledge=self.knowledge,
                    # 初始化NPC的状态，目前背包和观察都初始化为空
                    state={
                        'position': npc_json["position"],
                        'backpack': [],
                        'ob_people': [],
                        'ob_items': [],
                        'ob_locations': []
                    },
                    mood=npc_data["mood"],
                    memory=npc_data["memory"],
                    model=self.model,
                )
                self.npc_dict[npc.name] = npc
                logger.debug(f"<UDP NPC INIT> npc:{npc.name}")
        # 按照action字段，添加新的ACTION
        for action_name in action_list:
            with open(CONFIG_PATH / "action" / (action_name + ".json"), "r", encoding="utf-8") as file:
                action_json = json.load(file)
            action_item = ActionItem(
                name=action_json["name"],
                log_template=action_json["log_template"],
            )
            self.action_dict[action_item.name] = action_item
            logger.debug(f"<DISK ACT INIT> action:{action_item.name}")

        # language
        self.language = json_data["language"]

        self.send_data({"name": "inited", "status": "success"})

    async def confirm_conversation_line(self, json_data):
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
        conversation_id = json_data["conversation_id"]
        index = json_data["index"]
        if conversation_id in self.conversation_dict:
            convo = self.conversation_dict[conversation_id]
            memory_add, mood_change = convo.add_temp_memory(index)
            if len(memory_add.keys()) != 0:
                self.npc_information_update(memory_add, mood_change)

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
            npc.memory.add_memory_text(text = "\n".join(memory_add[name]), game_time = "Time")
            logger.debug(f"npc {name} add conversation pieces into memory done")
            npc.mood = mood_change[name]
            logger.debug(f"npc {name} update mood done")

    async def action_done(self, json_data:Dict[str, Any]):
        """
        如果游戏成功执行了动作，那么就将动作和参数存入记忆中 更新purpose 生成新的action然后传给GAME
        如果执行失败，那就结合失败原因存入记忆
        GAME传回数据例子:
        {
            "func":"action_done",
            "npc_name": "王大妈",
            "status": "success/fail",
            "npc_state": {
              "position": "李大爷家",
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
        status:str = json_data["status"]
        action_item:ActionItem = self.action_dict[json_data["action"]]
        npc_name:str = json_data["npc_name"]
        npc:NPC = self.npc_dict[npc_name]
        if status == "success":
            action_log:str = action_item.get_log(npc_name, json_data["object"], json_data["parameters"], reason=json_data["reason"])
        else:
            action_log:str = action_item.get_log(npc_name, json_data["object"], json_data["parameters"], reason=json_data["reason"])
        # 更新NPC允许的动作
        npc.set_all_actions(list(self.action_dict.keys()))
        # 更新NPC的状态
        npc.set_state(json_data['npc_state'])
        # 添加NPC记忆
        npc.memory.add_memory_text(action_log, game_time=json_data["time"])
        # 更新purpose
        npc.purpose = await npc.get_purpose(time=json_data["time"], k=3)
        # 生成新的action
        new_action:Dict[str, Any] = await npc.get_action(time=json_data["time"], k=3)
        action_packet = new_action
        action_packet["name"] = "action"
        # 发送新的action到环境
        self.send_script(action_packet)
        logger.debug(f"""[NPC-ENGINE]<action_done> 
                        npc_name:{npc.name}, 
                        purpose: {npc.purpose},
                        action:{action_packet}
                        to game""")

    async def wake_up(self, json_data):
        """
        NPC激活，
            游戏端检测到有NPC长时间无action/游戏初始化init时 被调用
            根据observation，location等字段，生成一个action，然后将action发送给游戏端

        GAME发送过来的数据例子:
        {
            "func":"wake_up",
            "npc_name": "王大妈",
            "npc_state": {
              "position": "李大爷家",
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
        # 获得NPC的引用
        npc_name = json_data["npc_name"]
        npc = self.npc_dict[npc_name]
        # 更新NPC允许的动作
        npc.set_all_actions(list(self.action_dict.keys()))
        # 更新NPC的状态
        npc.set_state(json_data['npc_state'])
        # 更新NPC的purpose
        npc.purpose = await npc.get_purpose(time=json_data["time"], k=3)
        # 生成新的action
        new_action = await npc.get_action(time=json_data["time"], k=3)
        action_packet = new_action
        action_packet["name"] = "action"
        # 发送新的action到环境
        self.send_script(action_packet)
        logger.debug(f"""[NPC-ENGINE]<wake_up> 
                        npc_name: {npc.name}, 
                        purpose: {npc.purpose} 
                        action: {action_packet} 
                        to game""")

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
            data[i : i + max_packet_size] for i in range(0, len(data), max_packet_size)
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

    def close(self):
        """
        关闭socket,结束Engine
        保存所有NPC的记忆到本地
        :return:
        """
        self.sock.close()
        print("socket closed")
        logger.debug("socket closed")
        logger.debug("saving memory")
        for npc in self.npc_dict.values():
            npc.save_memory()
        print("all memory saved")
        print("Engine closed")
        logger.debug("Engine closed")

if __name__ == "__main__":
    engine = NPCEngine()
