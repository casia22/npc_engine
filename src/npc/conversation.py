import datetime
import json
import os
import re
import socket
import threading
from typing import Any, Dict, List, Tuple
from uuid import uuid4

import openai
import zhipuai

from npc_engine.src.config import *
from npc_engine.src.template import *


class Conversation:
    def __init__(
        self, names, system_prompt, query_prompt, language="E", model="gpt-3.5-turbo"
    ):
        self.start_time = datetime.datetime.now()
        self.language = language
        self.names = names
        self.system_prompt = system_prompt
        self.query_prompt = query_prompt
        self.model = model
        self.id = str(uuid4())
        self.temp_memory = []
        self.index = -1
        self.script = self.generate_script()

    def add_temp_memory(self, conversation_id, index):
        if index >= self.index + 1:
            self.temp_memory.extend(self.sentences[self.index + 1, index + 1])
            self.index = index
        else:
            pass
        print("add_memory:", conversation_id, index, datetime.datetime.now())
        if self.index == len(self.sentences):
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
            if "(" in sent or "（" in sent:
                line = {
                    "type": "State",
                    "name": "",
                    "mood": "",
                    "words": sent.split("|")[1],
                    "action": None,
                }
            line = {
                "type": "content",
                "name": sent.split("|")[0],
                "mood": sent.split("|")[3],
                "talk": sent.split("|")[1],
                "action": {"name": sent.split("|")[5], "args": sent.split("|")[6]},
            }
            lines.append(line)
        return lines

    def call_llm(self):
        """
        调用LLM生成对话的功能函数(需要parser再处理)
        :return:
        """
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
            "lines": lines,
        }
        return script

    def re_create_conversation(self, interruption):
        assistant_prompt, query_prompt = Engine_Prompt.prompt_for_re_creation(
            self.language, interruption, self.temp_memory
        )
        self.query = query_prompt
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
        print("script:", script)
        return script


if __name__ == "__main__":
    print(OPENAI_BASE)
