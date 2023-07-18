import socket
from typing import List, Dict, Any, Tuple
import json
import threading
from uuid import uuid4
import datetime
import openai
#import zhipuai
import re, os, datetime, sys

from template import *
from config.config import *

openai.api_key = "sk-8p38chfjXbbL1RT943B051229a224a8cBdE1B53b5e2c04E2"
openai.api_base = "https://api.ai-yyds.com/v1"
os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890"

class Conversation:
    def __init__(
        self, names, location, system_prompt, query_prompt, language="C", model="gpt-3.5-turbo"):
        self.start_time = datetime.datetime.now()
        self.language = language
        self.names = names
        self.location = location
        self.system_prompt = system_prompt
        self.query_prompt = query_prompt
        self.model = model
        self.id = str(uuid4())
        self.temp_memory = []
        self.index = -1
        self.script = self.generate_script()

    def add_temp_memory(self, conversation_id, index):
        """
        根据回收的确认包，将所有不大于确认索引的所有剧本内容添加到conversation记忆中
        在需要的时候将记忆内容提取出来并存在每个参与对话的npc的记忆中
        :params conversation_id, index:
        :return bool:
        """
        if index >= self.index + 1:
            self.temp_memory.extend(self.sentences[self.index + 1 : index + 1])
            self.index = index
        else:
            pass
        print(self.temp_memory)
        print("add_memory:", conversation_id, index, datetime.datetime.now())
        if self.index + 1 == len(self.sentences):
            self.end_time = datetime.datetime.now()
            return True
        else:
            return False

    def parser(self, conv):
        """
        将剧本按照换行符分割成句子，再按照|分割成不同的字段
        :param conv:
        :return:
        """
        lines = []
        self.sentences = conv.split("\n")
        for sent in self.sentences:
            if "<" in sent:
                line = {
                    "type": "State",
                    "state": sent,
                    "name": "",
                    "mood": "",
                    "words": "",
                    "action": None}
            elif "(" in sent or "（" in sent:
                if self.language == "E":
                    line = {
                        "type": "Interaction",
                        "state": "",
                        "name": sent.split("(")[0].strip(),
                        "mood": (sent.split("(")[1]).split("|")[0].strip(),
                        "words": sent.split(":")[1].strip(),
                        "action": {"type": ((sent.split(")")[0]).split("|")[1]).strip(), "args": ((sent.split(")")[0]).split("|")[2]).strip()}}
                elif self.language == "C":
                    line = {
                        "type": "Interaction",
                        "state": "",
                        "name": sent.split("（")[0].strip(),
                        "mood": (sent.split("（")[1]).split("|")[0].strip(),
                        "words": sent.split("：")[1].strip(),
                        "action": {"type": ((sent.split("）")[0]).split("|")[1]).strip(), "args": ((sent.split("）")[0]).split("|")[2]).strip()}}
            else:
                line = {
                    "type": "Error",
                    "state": sent,
                    "name": "",
                    "mood": "",
                    "words": "",
                    "action": None}
            lines.append(line)
            print(line)
        return lines

    def call_llm(self, messages):
        """
        统一的LLM调用函数，用于剧本生成和部分润色
        :params messages:
        :return content:
        """
        #print(self.system_prompt)
        #print(self.query_prompt)
        response = openai.ChatCompletion.create(
            model=self.model, messages=messages
        )
        content = response["choices"][0]["message"]["content"].strip()
        return content

    def generate_script(self):
        """
        在类初始化的时候被自动调用，会请求LLM生成对话，返回剧本包
        :params:
        :return script:
        """
        messages = [self.system_prompt, self.query_prompt]
        conv = self.call_llm(messages = messages)
        lines = self.parser(conv)
        script = {
            "name": "conversation",
            "id": self.id,
            "length": len(lines),
            "location": self.location,
            "lines": lines,
        }
        return script

    def re_create_conversation(self, interruption):
        """
        接着玩家新插入的语句，继续生成剧本
        :params interruption:
        :return script:
        """
        assistant_prompt, query_prompt = Engine_Prompt.prompt_for_re_creation(
            self.language, interruption, self.temp_memory)
        self.query_prompt = query_prompt
        messages = [self.system_prompt, assistant_prompt, self.query_prompt]
        conv = self.call_llm(messages = messages)
        lines = self.parser(conv)
        script = {
            "name": "conversation",
            "id": self.id,
            "length": len(lines),
            "location": self.location,
            "lines": lines,
        }
        return script

if __name__ == '__main__':
    #prompt = Engine_Prompt()
    con = Conversation(1,2,3,4)
    '''
    a, b = prompt.prompt_for_conversation_E(
        names = ["Tony", "Austin"],
        location = "park",
        topic = "how to write math homework faster",
        descs = ["He is a teacher.", "He is a docter."],
        moods = ["calm", "calm"],
        memories = [["He finished homework just now.","He was a singer 10 years ago."], ["He had courses just now.", "He was a dancer."]],
        observations = "tree, grass, flower.",
        all_actions = ["chat","move"],
        all_places = ["Austin's home", "Tony's home", "park"],
        all_people = ["Tony", "Austin", "Cherry"],
        all_moods = ["calm", "happy", "sad", "anxious"],
        starting = "Hi, bro",
    )
    #print(openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "system", "content": "You are a singer and you know my name is Austin"},{"role": "user", "content": "You are a singer and you know my name is Austin.who are you and do you know who I am"}]))
    convo = Conversation(names = ["Tony", "Austin"],location = "park",system_prompt = a,query_prompt = b)
    print(convo.add_temp_memory("123",0))
    print(convo.add_temp_memory("123",1))
    #print(convo.add_temp_memory("123",2))
    convo.re_create_conversation("yeah it takes much time. What do you think of physics.")
    #print(convo.script)
    '''
    conv = rf"""<无人退出。剩下的角色：小明，小李，小张>""" + '\n' + \
                                rf"""小明（稳定，对话 小李&小张）：“你好呀，你们最近过得如何？”""" + '\n' + \
                                rf"""小李（稳定，对话 小明）：“我很好，我们现在正在讨论数学。”""" + '\n' + \
                                rf"""小张（稳定，对话 小明）：“是的，我们忙于做数学作业。”""" + '\n' + \
                                rf"""小明（稳定，对话 小李&小张）：“好吧，下次再见。”""" + '\n' + \
                                rf"""小李（稳定，对话 小明）：“好的，再见。”""" + '\n' + \
                                rf"""小张（稳定，对话 小明）：“再见小明。”""" + '\n' + \
                                rf"""小张（稳定，前往 家）：空""" + '\n' + \
                                rf"""<小明退出。剩下的角色：小李，小张>""" + '\n' + \
                                rf"""小李（着急，对话 小张）：“哦！我妈妈让我回家，我得走了。”""" + '\n' + \
                                rf"""小张（稳定，对话 小李）：“好的，再见，我想去公园看看。”""" + '\n' + \
                                rf"""小李（着急，前往 家）：空""" + '\n' + \
                                rf"""<小李退出。剩下的角色：小张>""" + '\n' + \
                                rf"""小张（稳定，前往 公园）：空""" + '\n' + \
                                rf"""<小张退出。剩下的角色：无人>""" + '\n' + \
                                rf"""<结束>"""
    con.parser(conv)