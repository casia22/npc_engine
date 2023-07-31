"""
Filename: npc.py
Author: Mengshi*, Yangzejun
Contact: ..., yzj_cs_ilstar@163.com
"""

import socket
from typing import List, Dict, Any, Tuple
import pickle
import openai
#import zhipuai
import re, os, datetime
from npc.memory import *

#zhipuai.api_key = "3fe121b978f1f456cfac1d2a1a9d8c06.iQsBvb1F54iFYfZq"
openai.api_key = "sk-8p38chfjXbbL1RT943B051229a224a8cBdE1B53b5e2c04E2"
openai.api_base = "https://api.ai-yyds.com/v1"

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
        model: str = "gpt-3.5-turbo",
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
        self.action: str = ""
        self.params: str = ""
        self.mood: str = mood
        self.location: str = location
        # NPC的记忆
        self.memory = NPCMemory(npc_name = self.name, k = memory_k)
        self.prompt: List[Dict[str, str]] = []
        self.prompt.extend(
            [
                {
                    "role": "system",
                    "content": rf"""
            下面你是角色'{self.name}',特点描述'{self.desc}',心情是'{self.mood}',正在'{self.location}'，
            附近环境是'{self.place}',看到了'{self.observation}',现在时间:{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
            下面扮演{self.name}进行符合口语交流习惯的对话，
            仅生成单轮对话，不要添加多轮对话。
            仅生成{self.name}嘴说出的话，不输出环境描述；
            当对话应当结束时比如角色move或者自然聊天结束，输出<EOC>，并且不要再输出任何内容。
            可选动作:{self.actions}
            可选地点:{self.place}
            可选人物:{self.people}
            可选心情:{self.moods}
            回复模版：
            名字|语言内容|情绪|情绪状态|动作|动作名｜动作参数
            例：
            武大郎|哎呀，我好像摔倒了|情绪|伤心|动作|stay｜None
            潘金莲|我想喝一杯茶|情绪|正常|动作|stay｜None
            潘金莲|我想我得去招武松聊聊|情绪|正常|动作|chat｜武松
            刘备|我可不是一般人，我要回家了|情绪|严肃|动作|move｜home
            <EOC>
            """,
                },
            ]
        )
        if self.model.startswith("chatglm"):
            self.prompt[0]["role"] = "user"
            self.prompt.append({"role": "assistant", "content": "好的，下面我会按照您的要求扮演。"})

    def process_response(self, response: str) -> Tuple[str, str, str, str, str]:
        # 例:名字|语言内容|情绪|情绪状态|动作|动作名｜动作参数
        response = re.sub(r'(\\)+("|\'|\\)', "", response)
        response = response.replace("｜", "|")
        response = response.split("|")
        # 解析response 得到 name, content, mood, action, params
        name, content, mood, action, params = "", "", "", "", ""
        try:
            # 王大妈:[中午好啊!我的黄金西瓜不见了，你见过吗] 情绪:<焦急> 动作:<chat|李大爷>"
            name = response[0]
            content = response[1]
            mood = response[3]
            action = response[5]
            params = response[6]
            # 更新NPC的状态
            self.mood = mood
            self.action = action
            self.params = params
            # 解析response 得到 name, content, mood, action, params
        except:
            # 更新NPC的状态
            self.mood = mood
            self.action = action
            self.params = params
            print("回复未能按照模版", name, content, mood, action, params)
            print("")
        return name, content, mood, action, params

    def to_json(
        self, name: str, content: str, mood: str, action: str, params: str
    ) -> Dict[str, Any]:
        # 匹配可用的mood
        if mood not in self.moods:
            mood = "正常"
        # 匹配可用的action
        if action not in self.actions:
            action = "stay"
        # 匹配可用的params
        if action == "move":
            if params not in self.place:
                params = ""
        elif action == "chat":
            if params not in self.people:
                params = ""
        json = {
            "name": name,
            "words": content,
            "emotion": mood,
            "action": {"name": action, "params": params},
        }
        return json

    def call_llm(self) -> str:
        response = openai.ChatCompletion.create(model=self.model, messages=self.prompt)
        words = response["choices"][0]["message"]["content"].strip()
        words = re.sub(r'(\\)+("|\'|\\)', "", words)
        return words

    def call_zhipuai(self) -> str:
        response = zhipuai.model_api.invoke(
            model=self.model,
            prompt=self.prompt,
            temperature=self.temperature,
            top_p=self.top_p,
        )
        words = response["data"]["choices"][0]["content"].strip()
        words = re.sub(r'(\\)+("|\'|\\)', "", words)
        return words

    def append_memory(self, memory: str) -> None:
        self.prompt.append(memory)

    def listen(self, content: str, npc: "npc") -> None:
        content = re.sub(r'(\\)+("|\'|\\)', "", content)
        name, content, mood, action, params = self.process_response(content)
        response_template = (
            rf"{npc.name}|{content}|情绪|{npc.mood}|动作|{npc.action}|{npc.params}"
        )
        self.prompt.append({"role": "user", "content": response_template})

    def say(self) -> str:
        assert self.prompt[-1]["role"] == "user", rf"{self.name}:请先让对方NPC说话"
        try:
            if self.model.startswith("gpt"):
                words = self.call_llm()
            elif self.model.startswith("chatglm"):
                words = self.call_zhipuai()
            name, content, mood, action, params = self.process_response(words)
            print(self.to_json(self.name, content, mood, action, params))
            self.prompt.append(
                {
                    "role": "assistant",
                    "content": f"{self.name}|{content}|情绪|{mood}|动作|{action}|{params}",
                }
            )
            return words
        except Exception as e:
            import traceback

            traceback.print_exc()
            print(f"Error occurred: {e}")
            print(self.to_json(self.name, content, mood, action, params))
            return f"{self.name}|{content}|情绪|{mood}|动作|{action}|{params}"

    def save_memory(self):
        """
        保存自己到本地./npc_memory/npc_name.pkl
        """
        data = {
            "model": self.model,
            "name": self.name,
            "desc": self.desc,
            "knowledge": self.knowledge,
            "actions": self.actions,
            "place": self.place,
            "moods": self.moods,
            "people": self.people,
            "observation": self.observation,
            "action": self.action,
            "params": self.params,
            "mood": self.mood,
            "location": self.location,
            "memory": self.memory,
            "prompt": self.prompt,
        }
        # 检查是否存在npc_memory文件夹，如果不存在则创建
        if not os.path.exists("./npc_memory"):
            os.makedirs("./npc_memory")
        file_path = os.path.join("./npc_memory", f"{self.name}.pkl")
        with open(file_path, "wb") as f:
            pickle.dump(data, f)