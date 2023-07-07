import socket
from typing import List, Dict, Any, Tuple
import json
import threading
from uuid import uuid4
import datetime
import openai
#import zhipuai
import re, os, datetime, sys

from src.template import *
from src.config.config import *

openai.api_key = "sk-8p38chfjXbbL1RT943B051229a224a8cBdE1B53b5e2c04E2"
openai.api_base = "https://api.ai-yyds.com/v1"
os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890"

class Conversation:
    def __init__(
        self, names, location, system_prompt, query_prompt, language="E", model="gpt-3.5-turbo"
    ):
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
        print(self.sentences)
        for sent in self.sentences:
            if "(" in sent or "（" in sent or sent == "<EOC>":
                line = {
                    "type": "State",
                    "name": "",
                    "mood": "",
                    "words": sent,
                    "action": None}
                continue
            line = {
                "type": "Content",
                "name": sent.split("|")[0],
                "mood": sent.split("|")[3],
                "words": sent.split("|")[1],
                "action": {"type": sent.split("|")[5], "args": sent.split("|")[6]},
            }
            lines.append(line)
        return lines

    def call_llm(self):
        """
        调用LLM生成对话的功能函数(需要parser再处理)
        :return:
        """
        #print(self.system_prompt)
        #print(self.query_prompt)
        response = openai.ChatCompletion.create(
            model=self.model, messages=[self.system_prompt, self.query_prompt]
        )
        conv = response["choices"][0]["message"]["content"].strip()
        return conv

    def generate_script(self):
        """
        在类初始化的时候被自动调用，会请求LLM生成对话，返回剧本包
        :return:
        """
        conv = self.call_llm()
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
        assistant_prompt, query_prompt = Engine_Prompt.prompt_for_re_creation(
            self.language, interruption, self.temp_memory)
        self.query_prompt = query_prompt
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[self.system_prompt, assistant_prompt, self.query_prompt],
        )
        conv = response["choices"][0]["message"]["content"].strip()
        lines = self.parser(conv)
        script = {
            "name": "conversation",
            "id": self.id,
            "length": len(lines),
            "lines": lines,
        }
        return script

if __name__ == '__main__':
    prompt = Engine_Prompt()
    
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