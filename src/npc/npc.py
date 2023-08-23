import json
import logging
import socket
from typing import List, Dict, Any, Tuple
import pickle
import openai
#import zhipuai
import re, os, datetime

#from npc_engine.src.npc.memory import NPCMemory
#from npc_engine.src.npc.action import ActionItem
#from npc_engine.src.config.config import CONSOLE_HANDLER, FILE_HANDLER, PROJECT_ROOT_PATH, MEMORY_DB_PATH, CONFIG_PATH
#from npc_engine.src.config.template import *

from npc.memory import NPCMemory
from npc.action import ActionItem
from config.config import CONSOLE_HANDLER, FILE_HANDLER, PROJECT_ROOT_PATH, MEMORY_DB_PATH, CONFIG_PATH
from config.template import *

#zhipuai.api_key = "3fe121b978f1f456cfac1d2a1a9d8c06.iQsBvb1F54iFYfZq"
openai.api_key = "sk-8p38chfjXbbL1RT943B051229a224a8cBdE1B53b5e2c04E2"
openai.api_base = "https://api.ai-yyds.com/v1"

# LOGGER配置
logger = logging.getLogger("NPC")
logger.setLevel(logging.DEBUG)
class NPC:
    def __init__(
        self,
        name: str,
        desc: str,
        knowledge: Dict[str, Any],
        location: str,
        mood: str = "正常",
        ob: List[str] = [],
        memory: List[str] = [],
        memory_k: int = 3,
        model: str = "gpt-3.5-turbo-16k",
    ) -> None:
        # model
        self.model: str = model
        # NPC固定参数
        self.name: str = name
        self.desc: str = desc
        # NPC的常识
        self.knowledge: Dict[str, Any] = knowledge
        self.actions: List[str] = knowledge["actions"]
        self.place: List[str] = knowledge["places"]
        self.moods: List[str] = knowledge["moods"]
        self.people: List[str] = knowledge["people"]
        # NPC的状态
        self.observation: List[str] = ob
        self.action_dict = {}
        self.mood: str = mood
        self.location: str = location
        self.purpose: str = ""
        # NPC的记忆
        self.memory: NPCMemory = NPCMemory(npc_name=self.name, k=memory_k)
        self.memory.touch_memory()
        
        ####################### 先清空现有VB #######################
        self.memory.clear_memory()
        ################# 等到记忆添加实现闭环时删除 #################
        
        # 将初始化的记忆内容加入到memory中
        if len(memory) > 0:
            for piece in memory:
                self.memory.add_memory_text(piece, game_time = "XXXXXXXXXXXXXXXX")
                logger.debug(f"add memory {piece} into npc {self.name} done.")

    def set_observation(self, observation: List[str]) -> None:
        self.observation = observation

    def set_all_actions(self, actions: List[str]) -> None:
        self.actions = actions

    def set_location(self, location: str) -> None:
        self.location = location

    def set_mood(self, mood: str) -> None:
        self.mood = mood

    def get_purpose(self, time:str, k:int=3) -> str:
        """
        根据位置和时间+NPC记忆获取NPC的目的
        如果没有目的，那就参照最近记忆生成一个目的
        如果有了目的，那就以当前记忆检索重新生成一个目的
        :param time: str
        :return: str
        """
        if not self.purpose:
            # 如果没有目的，那就参照最近记忆
            role_play_instruct = f"""
            请你扮演{self.name}，特性是：{self.desc}，
            可有的心情是{self.moods}，
            当前心情是{self.mood}，正在{self.location}，现在时间是{time},
            最近记忆:{self.memory.latest_k.queue},
            {self.name}现在看到:{self.observation}
            """
            prompt = f"""
            请你为{self.name}生成一个目的，以下是例子：
            例1：[{self.moods[0]}]<{self.name}想去XXX，因为{self.name}想和XX聊聊天，关于{self.name}XXX>
            例2：[{self.moods[1]}]<{self.name}想买一条趁手的扳手，这样就可以修理{self.name}家中损坏的椅子。>
            例3：[{self.moods[1]}]<{self.name}想去XXX的家，因为{self.name}想跟XXX搞好关系。>
            要求：
            1.按照[情绪]<目的>的方式来返回内容
            2.尽量使用第三人称来描述
            3.如果目的达成了一部分，那就去除完成的部分并继续规划
            4.目的要在20字以内。
            """
        else:
            # 如果有目的，那就使用目的来检索最近记忆和相关记忆
            memory_dict:Dict[str, Any] = self.memory.search_memory(query_text=self.purpose,query_game_time=time, k=k)
            memory_latest_text = "\n".join([each.text for each in memory_dict["latest_memories"]])
            memory_related_text = "\n".join([each.text for each in memory_dict["related_memories"]])

            # 结合最近记忆和相关记忆来生成目的
            role_play_instruct = f"""
            请你扮演{self.name}，特性是：{self.desc}，
            可有的心情是{self.moods}，
            心情是{self.mood}，正在{self.location}，现在时间是{time},
            {self.name}的最近记忆:{memory_latest_text}，
            {self.name}脑海中相关记忆:{memory_related_text}，
            {self.name}现在看到:{self.observation}，
            {self.name}之前的目的是:{self.purpose}
            """
            prompt = f"""
            请你为{self.name}生成一个目的，以下是例子：
            例1：[{self.moods[0]}]<{self.name}想去XXX，因为{self.name}想和XX聊聊天，关于{self.name}XXXXXXX。>
            例2：[{self.moods[1]}]<{self.name}想买一条趁手的扳手，这样就可以修理{self.name}家中损坏的椅子。>
            例3：[{self.moods[1]}]<{self.name}想去XXX的家，因为{self.name}想跟XXX搞好关系。>
            要求：
            1.按照[情绪]<目的>的方式来返回内容
            2.尽量使用第三人称来描述
            3.如果目的达成了一部分，那就去除完成的部分并继续规划
            4.如果目的不改变，可以返回: [情绪]<S>
            5.目的要在20字以内。
            """
        #role_play_instruct, prompt=prompt = get_agent_purpose()
        # 发起请求
        purpose_response: str = self.call_llm(instruct=role_play_instruct, prompt=prompt)
        # 解析返回
        purpose: str = purpose_response.split("]<")[1].replace(">", "")
        mood: str = purpose_response.split("]<")[0].replace("[", "")

        logger.debug(f"""
            <发起PURPOSE请求>
            <请求内容>:{role_play_instruct}
            <请求提示>:{prompt}
            <返回目的>:{purpose}
            <返回情绪>:{mood}
            """)
        # 更新情绪
        self.mood = mood
        # 如果目的不改变，那就直接返回
        if purpose == "<S>":
            return self.purpose
        # 如果目的改变，那就更新目的
        self.purpose = purpose
        return purpose

    def get_action(self, time:str, k:int=3) -> Dict[str, Any]:
        # TODO: 将返回的action做成类似conversation一样的list，然后返回游戏执行错误/成功，作为一个memoryitem
        """
        结合NPC的记忆、目的、情绪、位置、时间等信息来生成动作和参数
        大模型返回例:
            <chat|李大爷|李大爷你吃了吗>
            <mov|李大爷|>
            todo：返回一个action列表
            [<mov|箱子>,<take|箱子|西瓜汁>]
        函数返回例：
            {'action': 'take', 'object': '箱子', 'parameters': ['西瓜汁', '桃子', '枕头']}
        :param time:
        :param k:
        :return: Dict[str, Any]
        """
        # 按照NPC目的和NPC观察检索记忆
        query_text:str = self.purpose + ",".join(self.observation) # 这里暴力相加，感觉这不会影响提取的记忆相关性[或检索两次？]
        memory_dict:Dict[str, Any] = self.memory.search_memory(query_text=query_text,query_game_time=time,k=k)
        memory_related_text = "\n".join([each.text for each in memory_dict["related_memories"]])
        memory_latest_text = "\n".join([each.text for each in memory_dict["latest_memories"]])
        # 构造prompt请求
        instruct = f"""
            请你扮演{self.name}，特性是：{self.desc}，
            心情是{self.mood}，正在{self.location}，现在时间是{time},
            {self.name}的最近记忆:{memory_latest_text}，
            {self.name}脑海中相关记忆:{memory_related_text}，
            {self.name}现在看到:{self.observation}，
            {self.name}当前的目的是:{self.purpose}
        """
        # TODO: 完善use功能，为每个物品声明动作和动作参数范围
        prompt = f"""
            请你为{self.name}生成一个动作，以下是例子：
                <chat|李大爷|李大爷你吃了吗>
                <mov|李大爷家|>
                <put|箱子|苹果派>
                <take|箱子|西瓜汁,桃子,枕头>
                <take|箱子|枕头>
                <use|刀|西瓜>
                <use|门|开>
                <give|李大爷|茶叶>
            要求:
                1.按照<动作|对象|参数>的方式来返回内容
                2.按照情况仅返回下面允许动作中的一个
                3.use动作的对象和参数要存在于看到的物品中。
                4.如果动作有多个参数那么使用“,”分隔
                5.使用|而不是｜来分割
                6.动作和参数要在20字以内。
            允许动作：
                {self.actions}
            """
        # 发起请求
        response: str = self.call_llm(instruct=instruct, prompt=prompt)
        # 抽取动作和参数
        action_dict:Dict[str, Any] = ActionItem.str2json(response)
        self.action_dict = action_dict
        logger.debug(f"""
                    <发起ACTION请求>
                    <请求内容>:{instruct}
                    <请求提示>:{prompt}
                    <返回目的>:{action_dict}
                    """)
        return action_dict

    def call_llm(self, instruct:str, prompt:str) -> str:
        llm_prompt_list = [{
            "role": "system",
            "content": instruct},
            {
                "role": "user",
                "content": prompt}
        ]
        response = openai.ChatCompletion.create(model=self.model, messages=llm_prompt_list)
        words = response["choices"][0]["message"]["content"].strip()
        return words

    def save_memory(self):
        """
        以npc_name.json的形式保存npc的状态
        """
        NPC_CONFIG_PATH = CONFIG_PATH / "npc" / f"{self.name}.json"
        data = {
            # 初始化的必填参数
            "name": self.name,
            "desc": self.desc,
            "location": self.location,
            "mood": self.mood,
            "memory": self.memory.latest_k.queue,

            # 无任何意义只是记录的参数
            "purpose": self.purpose,
            "observation": self.observation,
            "action": self.action_dict,
        }
        # 以json字符串的形式保存
        with open(NPC_CONFIG_PATH, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        logger.debug(f"保存NPC:{self.name}的状态到{NPC_CONFIG_PATH}")