"""
Filename : conversation.py
Author : Yangzejun
Contact : yzj_cs_ilstar@163.com
"""

from typing import List, Dict, Any
from uuid import uuid4
import datetime
import os
import openai
#import zhipuai

openai.api_key = "sk-8p38chfjXbbL1RT943B051229a224a8cBdE1B53b5e2c04E2"
openai.api_base = "https://api.ai-yyds.com/v1"
os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890"

class Conversation:
    """
    Conversation类，内有剧本初生成函数、剧本再生成函数、LLM调用函数、剧本解析函数、记忆添加函数
    """
    def __init__(
        self,
        names: List[str],
        location: str,
        system_prompt: Dict[str, str],
        query_prompt: Dict[str, str],
        language: str = "C",
        model: str = "gpt-3.5-turbo",
    ) -> None:
        # 系统时间戳
        self.start_time = datetime.datetime.now()
        self.end_time = None
        # 对话创建关键信息：角色名称、地点、系统提示词、查询提示词、中/英、大模型类型
        self.names: List[str] = names
        self.location: str = location
        self.system_prompt: Dict[str, str] = system_prompt
        self.query_prompt: Dict[str, str] = query_prompt
        self.language: str = language
        self.model: str = model
        # Conversation实例的ID
        self.convo_id: str = str(uuid4())
        # 将展示结束的剧本行作为记忆存起来
        self.temp_memory: List[str] = []
        # 剧本行索引，用于剧本演示的确认
        self.index: int = -1
        # 存储剧本按行拆分结果的中间变量
        self.sentences = []
        # 调用剧本生成函数生成剧本
        self.script = self.generate_script()

    def call_llm(
        self,
        messages: Dict[str, str],
    ) -> str:
        """
        统一的LLM调用函数，用于剧本初生成、再生成
        提示词输入的格式如下：
        [
            {
            "role": "system",
            "content": string1,
            },
            {
            "role": "assistant",
            "content": string2,
            },
            {
            "role": "user",
            "content": string3,
            },
        ]

        :params messages:
        :return content:
        """
        # 调用官方API获取字典形式的返回值
        response = openai.ChatCompletion.create(model=self.model, messages=messages)
        # 按照固定形式从LLM返回的字典中提取出回复文本并做空格符清理
        content = response["choices"][0]["message"]["content"].strip()

        return content

    def parser(
        self,
        conv: str,
    ) -> List[Dict[str, Any]]:
        """
        将剧本按行解析，每行归为四个剧本内容类型中的一类，并打包成字典格式
        剧本内容类型1————会话状态，配置案例如下：
        {
        "type": "State",
        "state": "<Nobody Exists. Remaining Characters: Jack, Tom, Lily>",
        "name": "",
        "mood": "",
        "words": "",
        "action": None,
        }
        剧本内容类型2————结束状态，配置案例如下：
        {
        "type": "State",
        "state": "<EOC>",
        "name": "",
        "mood": "",
        "words": "",
        "action": None,
        }
        剧本内容类型3————角色交互，配置案例如下：
        {
        "type": "Interaction",
        "state": "",
        "name": "Jack",
        "mood": "Sad",
        "words": "I feel not well right now.",
        "action": {
            "type": "Chat",
            "args": "Lily",
            }
        }
        剧本内容类型4————错误内容，配置案例如下：
        {
        "type": "Error",
        "state": "<Nobody exist, remained characters: Lily)",
        "name": "",
        "mood": "",
        "words": "",
        "action": None,
        }

        :param conv:
        :return:
        """
        # 首先将剧本按行拆分
        lines = []
        self.sentences.clear()
        self.sentences = conv.split("\n")

        # 逐行分析并依据四个剧本内容类型分类
        for sent in self.sentences:
            # 归为结束状态和会话状态两类
            if "<" in sent:
                line = {
                    "type": "State",
                    "state": sent,
                    "name": "",
                    "mood": "",
                    "words": "",
                    "action": None}
            elif "(" in sent or "（" in sent:
                # 归为英文的角色交互一类
                if self.language == "E":
                    line = {
                        "type": "Interaction",
                        "state": "",
                        "name": sent.split("(")[0].strip(),
                        "mood": (sent.split("(")[1]).split("|")[0].strip(),
                        "words": sent.split(":")[1].strip(),
                        "action": {"type": ((sent.split(")")[0]).split("|")[1]).strip(), "args": ((sent.split(")")[0]).split("|")[2]).strip()}}
                # 归为中文的角色交互一类
                elif self.language == "C":
                    line = {
                        "type": "Interaction",
                        "state": "",
                        "name": sent.split("（")[0].strip(),
                        "mood": (sent.split("（")[1]).split("|")[0].strip(),
                        "words": sent.split("：")[1].strip(),
                        "action": {"type": ((sent.split("）")[0]).split("|")[1]).strip(), "args": ((sent.split("）")[0]).split("|")[2]).strip()}}
            # 归为错误内容一类
            else:
                line = {
                    "type": "Error",
                    "state": sent,
                    "name": "",
                    "mood": "",
                    "words": "",
                    "action": None}
            lines.append(line)

        return lines

    def generate_script(
        self,
    ) -> Dict[str, Any]:
        """
        函数根据实例中与对话创建相关的关键信息生成剧本并以标准格式解析成json发送到游戏端
        函数中涉及到字典格式的剧本信息，该格式配置案例如下：
        {
        "name": "conversation",
        "id": "123456789",
        "length": "S",
        "location": "Park",
        "lines": [
            {
            "type": "State",
            "state": "<Nobody Exists. Remaining Characters: Jack, Tom, Lily>"
            "name": "",
            "mood": "",
            "words": "",
            "action": None,
            },
            {
            "type": "Interaction",
            "name": "Jack",
            "mood": "Sad",
            "words": "I feel not well right now.",
            "action": {
                "type": "Chat",
                "args": "Lily"
                }
            },
            ...
            {
            "type": "State",
            "state": "<EOC>",
            "name": "",
            "mood": "",
            "words": "",
            "action": None,
            },
        ]
        }

        :params:
        :return script:
        """
        # 首先将系统提示词和查询提示词打包
        messages = [self.system_prompt, self.query_prompt]
        # 接着将打包好的提示词输入到LLM中生成文本剧本
        conv = self.call_llm(messages = messages)
        # 使用解析器将文本剧本映射成字典格式
        lines = self.parser(conv)
        # 将剧本信息按照配置标准整理并返回
        script = {
            "name": "conversation",
            "id": self.convo_id,
            "length": len(lines),
            "location": self.location,
            "lines": lines,
        }

        return script

    def re_create_conversation(
        self,
        assistant_prompt: Dict[str, str],
        query_prompt: Dict[str, str],
    ) -> Dict[str, Any]:
        """
        函数根据实例中与对话创建相关的关键信息以及玩家新插入的回复信息，继续生成剧本并以标准格式解析成json发送到游戏端
        函数中涉及到字典格式的剧本信息，具体格式详见generate_script()函数

        :params interruption:
        :return script:
        """
        # 首先将系统提示词、输入的助理提示词和输入的查询提示词打包
        messages = [self.system_prompt, assistant_prompt, query_prompt]
        # 接着将打包好的提示词输入到LLM中继续生成文本剧本
        conv = self.call_llm(messages = messages)
        # 使用解析器将文本剧本映射成字典格式
        lines = self.parser(conv)
        # 将剧本信息按照配置标准整理并返回
        script = {
            "name": "conversation",
            "id": self.convo_id,
            "length": len(lines),
            "location": self.location,
            "lines": lines,
        }

        return script

    def add_temp_memory(
        self,
        index: int,
    ) -> bool:
        """
        根据回收的确认包，将所有不大于确认索引的所有剧本内容添加到conversation记忆中

        :params index:
        :return bool:
        """
        # 将接收的索引号与已经处理的索引号作比较，并决定是否添加新的记忆
        if index >= self.index + 1:
            self.temp_memory.extend(self.sentences[self.index + 1 : index + 1])
            self.index = index
        else:
            pass

        # 显示新添加的记忆内容的详细信息
        print("add_memory:", self.convo_id, index, datetime.datetime.now())

        # 判断所有剧本内容是否都添加到记忆中，如果是则返回True，否则返回False
        if self.index + 1 == len(self.sentences):
            self.end_time = datetime.datetime.now()
            print("add_memory complete !", self.end_time)
            return True
        return False

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
    conv = """<无人退出。剩下的角色：小明，小李，小张>""" + '\n' + \
                                """小明（稳定，对话 小李&小张）：“你好呀，你们最近过得如何？”""" + '\n' + \
                                """小李（稳定，对话 小明）：“我很好，我们现在正在讨论数学。”""" + '\n' + \
                                """小张（稳定，对话 小明）：“是的，我们忙于做数学作业。”""" + '\n' + \
                                """小明（稳定，对话 小李&小张）：“好吧，下次再见。”""" + '\n' + \
                                """小李（稳定，对话 小明）：“好的，再见。”""" + '\n' + \
                                """小张（稳定，对话 小明）：“再见小明。”""" + '\n' + \
                                """小张（稳定，前往 家）：空""" + '\n' + \
                                """<小明退出。剩下的角色：小李，小张>""" + '\n' + \
                                """小李（着急，对话 小张）：“哦！我妈妈让我回家，我得走了。”""" + '\n' + \
                                """小张（稳定，对话 小李）：“好的，再见，我想去公园看看。”""" + '\n' + \
                                """小李（着急，前往 家）：空""" + '\n' + \
                                """<小李退出。剩下的角色：小张>""" + '\n' + \
                                """小张（稳定，前往 公园）：空""" + '\n' + \
                                """<小张退出。剩下的角色：无人>""" + '\n' + \
                                """<结束>"""
    con.parser(conv)
    '''
