"""
Filename : conversation.py
Author : Yangzejun
Contact : yzj_cs_ilstar@163.com
"""
from pathlib import Path
from typing import List, Dict, Any
from uuid import uuid4
import copy
import json
import datetime
import os
import logging
import hashlib
import openai
#import zhipuai
from colorama import Fore, Style
from nuwa.src.utils.model_api import get_model_answer
from nuwa.src.utils.send_utils import send_data

os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890"


class Conversation:
    """
    Conversation 是动态维护多Agent对话的数据结构

    Conversation 对象创建：
    [1] 对象初创建所需要的游戏端信息包括：初始对话Agent实体，初始对话主题、初始对话地点
    [2] 对象创建后会自动调用generate_script()方法生成初始剧本
    
    Conversation 对象运行：
    [1] Conversation 对象在运行的时候占用所有对话Agent的信息更改权，但是该权限可以被阻塞
    [2] Conversation 对象自行决定Agent的退出，但无法决定Agent的加入
    [3] Conversation 决定某个Agent退出对话后，会在退出Agent中更新数据并自动释放占用权限
    [4] Conversation 对象默认执行所有角色的move动作和chat动作，除非在Agent相关属性中特殊声明角色的动作列表

    Conversation 对象关闭：
    [1] 当剧本展演完后对象会自动检测Agent实体列表，当没有任何Agent实体剩余的时候，会向Engine端返回关闭信号。
        收到关闭信号后Engine会调用close()方法清空该对象的所有数据并删除该对象。

    Conversation 对象维护的主要游戏端信息如下：
    (1) 所有对话Agent实体
    (2) 对话发生的当前地点
    (3) 对话的主要主题
    (4) 剧本内容
    Conversation可对外开放的接口及其对应功能如下：
    (1) generate_script() 在Conversation对象刚开始创建的时候会调用的生成初始剧本的方法，
    (2) re_generate_script() 在有新Agent加入或者玩家插话的时候调用的方法，续写剧本
    (3) set_topic() 重新设定新的主题，根据新主题续写剧本
    (4) set_requirements() 重新设定剧本生成的约束或者要求
    (5) set_location() 重新设定新的地点，对剧本内容改动不是很大
    (6) release() 强制让Conversation释放对某角色的占用权限
    (7) close() 清空对象的所有数据
    """
    def __init__(
        self,
        names: List[str],
        location: str,
        scenario_name: str,
        topic: str,
        model: str,
        share_observations: Dict[str, List[str]],
        system_prompt: Dict[str, str],
        query_prompt: Dict[str, str],
        project_root=Path(os.getcwd()),
        language: str = "C",
        stream: bool = True,
        sock = None,
        game_url: str = "",
        game_port: str = "",
    ) -> None:
        # Conversation模块logger设置
        self.logger = logging.getLogger("CONVERSATION")
        self.logger.setLevel(logging.INFO)

        # 系统时间戳
        self.start_time = datetime.datetime.now()
        self.end_time = None
        # 对话创建关键信息：角色名称、地点、系统提示词、查询提示词、中/英、大模型类型
        self.names: List[str] = names
        self.location: str = location
        self.scenario_name: str = scenario_name
        self.topic: str = topic
        self.share_observations = share_observations
        self.language: str = language
        self.model: str = model
        self.stream = stream
        # 端口相关信息
        self.engine_sock = sock
        self.game_url = game_url
        self.game_port = game_port
        # 用于阻塞控制stream对话生成
        self.active_session = ""
        # 存储每一个角色参与对话的记忆起始索引值
        self.start_memory: Dict[str, int] = {}
        for name in self.names:
            self.start_memory[name] = 0
        # 由self.names派生出的变量，用于添加到角色的记忆中，会动态更新
        #self.memory_head_names: Dict[str, List[str]] = {}
        ##for name in self.names:
        #    self.memory_head_names[name] = copy.deepcopy(self.names)
        # Conversation实例的ID
        self.convo_id: str = str(uuid4())
        #self.convo_id = "1234567890"
        # 将展示结束的剧本行作为记忆存起来
        self.temp_memory: List[str] = []
        self.script_perform: List[str] = []
        # 剧本行索引，用于剧本演示的确认
        self.index: int = -1
        # 存储剧本按行拆分结果的中间变量
        self.sentences: List[str] = []
        self.lines: List[Dict[str, Any]] = []

    def reset_session(
        self, 
        new_session: str):
        """
        将new_session赋值给全局session

        :params new_session:
        """
        self.active_session = new_session

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
        :params stream:
        :return content:
        """
        # 如果是流式的则返回一个迭代器，如果是非流式则返回字典
        response = openai.ChatCompletion.create(model=self.model, messages=messages, stream=self.stream)
        # TODO: 使用标准model_api模块而不是自己实现 这样仅仅能使用openai是不可以的
        return response

    def parser(
        self,
        conv: str,
    ) -> None:
        """
        将剧本按行解析，每行归为四个剧本内容类型中的一类，并打包成字典格式
        剧本内容类型1————会话状态，配置案例如下：
        {
        "type": "State",
        "state": "Nobody Exits. Remaining Characters: Jack, Tom, Lily",
        "name": "",
        "mood": "",
        "words": "",
        "action": None,
        }
        剧本内容类型2————结束状态，配置案例如下：
        {
        "type": "State",
        "state": "EOC",
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
        "state": "<Nobody Exit, remained characters: Lily)",
        "name": "",
        "mood": "",
        "words": "",
        "action": None,
        }

        :param conv:
        :return:
        """
        # 更新与实例属性以适应新剧本
        self.index = -1
        self.lines.clear()
        self.sentences.clear()
        self.sentences = conv.split("\n")

        # 逐行分析并依据四个剧本内容类型分类
        for sent in self.sentences:
            self.logger.debug(f"get a new sentence of script : {sent}")
            line = self.parse_one_sent(sent=sent)
            if line is not None:
                self.lines.append(line)

    def parse_one_sent(self, sent):
        if len(sent) == 0:
            return None
        # 归为结束状态和会话状态两类
        if sent[0] == "<" and sent[-1] == ">":
            line = {
                "type": "State",
                "state": sent[1:-1],
                "name": "",
                "mood": "",
                "words": "",
                "action": None}
        elif ("(" in sent or "（" in sent) and (":" in sent or "：" in sent):
            # 根据左括号是全角还是半角来解析name和mood信息
            if "(" in sent:
                name = sent.split("(")[0].strip()
                mood = (sent.split("(")[1]).split("|")[0].strip()
            elif "（" in sent:
                name = sent.split("（")[0].strip()
                mood = (sent.split("（")[1]).split("|")[0].strip()
                
            # 根据冒号是全角还是半角来解析words信息
            if ":" in sent:
                words = sent.split(":")[1].strip()
            elif "：" in sent:
                words = sent.split("：")[1].strip()
                    
            # 根据右括号是全角还是半角来解析action信息
            if ")" in sent:
                action_type = ((sent.split(")")[0]).split("|")[1]).strip()
                action_args = ((sent.split(")")[0]).split("|")[2]).strip()
            elif "）" in sent:
                action_type = ((sent.split("）")[0]).split("|")[1]).strip()
                action_args = ((sent.split("）")[0]).split("|")[2]).strip()

            # 将信息整合成最终的一行格式化剧本
            line = {
                "type": "Interaction",
                "state": "",
                "name": name,
                "mood": mood,
                "words": words,
                "action": {"type": action_type, "args": action_args}}
                    
        # 归为错误内容一类
        else:
            line = {
                "type": "Error",
                "state": sent,
                "name": "",
                "mood": "",
                "words": "",
                "action": None}
        self.logger.debug(f"parser out a new line of script : {line}")
        return line
        
    def generate_script(
        self,
        system_prompt: Dict[str, str],
        query_prompt: Dict[str, str],
    ) -> Dict[str, Any]:
        """
        函数根据实例中与对话创建相关的关键信息生成剧本并以标准格式解析成json发送到游戏端
        函数中涉及到字典格式的剧本信息，该格式配置案例如下：
        {
        "name": "conversation",
        "mood": "script"
        "id": "123456789",
        "location": "Park",
        "lines": [
            {
            "type": "State",
            "state": "<Nobody Exits. Remaining Characters: Jack, Tom, Lily>"
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

        :params system_prompt:
        :params query_prompt:
        :return script:
        """
        # 创建一个新的局部session并覆盖式的重置全局session
        local_session = hashlib.md5(str(datetime.datetime.now()).encode()).hexdigest()
        self.reset_session(local_session)
        # 首先将系统提示词和查询提示词打包
        messages = [system_prompt, query_prompt]
        # 接着将打包好的提示词输入到LLM中生成文本剧本
        response = self.call_llm(messages = messages)

        if self.stream:
            self.logger.debug(f"First script of conversation {self.convo_id} in stream form is generated as follows:")
            one_sent = ""
            for chunk in response:
                chunk_message = chunk['choices'][0]['delta']
                # 如果content键在chunk_message里面，则表示这条流信息中有内容可以提取
                if 'content' in chunk_message:
                    chunk_content = chunk_message['content']
                # 如果不在则表示没有内容可以提取了
                else:
                    self.logger.debug(f"Generate new line in conversation {self.convo_id}: {one_sent}")
                    self.sentences.append(one_sent)
                    one_line = self.parse_one_sent(one_sent)
                    self.lines.append(one_line)
                    one_sent = ""
                    line_pack = {
                        "name": "conversation",
                        "mode": "line",
                        "id": self.convo_id,
                        "location": self.location,
                        "index": len(self.lines),
                        "one_line": one_line}
                    self.send_line(line_pack)
                    break
                # 如果内容中有回车符，则按照回车做截取
                if "\n" in chunk_content:
                    one_sent += chunk_content.split('\n')[0]
                    self.logger.debug(f"Generate new line in conversation {self.convo_id}: {one_sent}")
                    self.sentences.append(one_sent)
                    one_line = self.parse_one_sent(one_sent)
                    self.lines.append(one_line)
                    one_sent = chunk_content.split('\n')[1]
                    line_pack = {
                        "name": "conversation",
                        "mode": "line",
                        "id": self.convo_id,
                        "location": self.location,
                        "index": len(self.lines),
                        "one_line": one_line}
                    self.send_line(line_pack)
                # 如果没有回车符，则直接将内容右添加到one_sent中
                else:
                    one_sent += chunk_content
                if self.active_session != local_session:
                    break
            self.logger.debug(f"All script lines of conversation {self.convo_id} in stream form is generated.")
            sentence_str = '\n'.join(self.sentences)
            self.logger.info(f"First script of conversation {self.convo_id} in stream form is generated as follows:\n{sentence_str}")
        else:
            conv = response["choices"][0]["message"]["content"].strip()
            self.logger.debug(f"First script of conversation {self.convo_id} in non-stream form is generated as follows:\n{conv}")
            # 使用解析器将文本剧本映射成字典格式
            self.parser(conv)
            # 将剧本信息按照配置标准整理并返回
            script = {
                "name": "conversation",
                "mode": "script",
                "id": self.convo_id,
                "location": self.location,
                "lines": self.lines,
            }
            self.logger.debug(f"First script of conversation {self.convo_id} in non-stream form is generated.")
            self.logger.info(f"First script of conversation {self.convo_id} in non-stream form is generated as follows:\n{conv}")
            # 发送整个剧本
            self.send_script(script)
    
    def re_generate_script(
        self,
        new_name: str,
        system_prompt: Dict[str, str],
        query_prompt: Dict[str, str],
    ) -> Dict[str, Any]:
        """
        函数根据实例中与对话创建相关的关键信息以及新加入的角色或新插入的玩家回复，继续生成剧本并以标准格式解析成json发送到游戏端
        函数中涉及到字典格式的剧本信息，具体格式详见generate_script()函数

        :params new_name:
        :params system_prompt:
        :params query_prompt:
        :return script:
        """
        # 创建一个新的局部session并覆盖式的重置全局session
        local_session = hashlib.md5(str(datetime.datetime.now()).encode()).hexdigest()
        self.reset_session(local_session)
        # 如果添加的新角色已经在角色列表中，则报错并返回空
        if new_name in self.names:
            self.logger.info(f"{new_name} is already in conversation {self.convo_id}. Re-creation fails.")
            return None
        # 如果新角色信息不为空，则加入更新对话对象的角色列表、temp_memory序列以及对话记忆起始索引值字典
        if new_name != "":
            self.names.append(new_name)
            self.temp_memory.append(rf"""{new_name}加入了对话。""")
            self.start_memory[new_name] = len(self.temp_memory)
        # 首先将系统提示词、输入的助理提示词和输入的查询提示词打包
        messages = [system_prompt, query_prompt]
        # 接着将打包好的提示词输入到LLM中继续生成文本剧本
        response = self.call_llm(messages = messages)

        if self.stream:
            self.logger.debug(f"New script of conversation {self.convo_id} in stream form is re-generated as follows:")
            # 将动态维护剧本的变量进行清空
            self.index = -1
            self.lines.clear()
            self.sentences.clear()

            one_sent = ""
            for chunk in response:
                chunk_message = chunk['choices'][0]['delta']
                # 如果content键在chunk_message里面，则表示这条流信息中有内容可以提取
                if 'content' in chunk_message:
                    chunk_content = chunk_message['content']
                # 如果不在则表示没有内容可以提取了
                else:
                    self.logger.debug(f"Generate new line in conversation {self.convo_id}: {one_sent}")
                    self.sentences.append(one_sent)
                    one_line = self.parse_one_sent(one_sent)
                    self.lines.append(one_line)
                    one_sent = ""
                    line_pack = {
                        "name": "conversation",
                        "mode": "line",
                        "id": self.convo_id,
                        "location": self.location,
                        "index": len(self.lines),
                        "one_line": one_line}
                    self.send_line(line_pack)
                    break
                # 如果内容中有回车符，则按照回车做截取
                if "\n" in chunk_content:
                    one_sent += chunk_content.split('\n')[0]
                    self.logger.debug(f"Generate new line in conversation {self.convo_id}: {one_sent}")
                    self.sentences.append(one_sent)
                    one_line = self.parse_one_sent(one_sent)
                    self.lines.append(one_line)
                    one_sent = chunk_content.split('\n')[1]
                    line_pack = {
                        "name": "conversation",
                        "mode": "line",
                        "id": self.convo_id,
                        "location": self.location,
                        "index": len(self.lines),
                        "one_line": one_line}
                    self.send_line(line_pack)
                # 如果没有回车符，则直接将内容右添加到one_sent中
                else:
                    one_sent += chunk_content
                if self.active_session != local_session:
                    break
            self.logger.debug(f"All script lines of conversation {self.convo_id} in stream form is re-generated.")
            sentence_str = '\n'.join(self.sentences)
            self.logger.info(f"New script of conversation {self.convo_id} in stream form is re-generated as follows:\n{sentence_str}")
        else:
            conv = response["choices"][0]["message"]["content"].strip()
            self.logger.debug(f"New script of conversation {self.convo_id} in non-stream form is re-generated as follows:\n{conv}")
            # 使用解析器将文本剧本映射成字典格式
            self.parser(conv)
            # 将剧本信息按照配置标准整理并返回
            script = {
                "name": "conversation",
                "mode": "script",
                "id": self.convo_id,
                "location": self.location,
                "lines": self.lines,
            }
            self.logger.debug(f"New script of conversation {self.convo_id} in non-stream form is re-generated.")
            self.logger.info(f"New script of conversation {self.convo_id} in non-stream form is re-generated as follows:\n{conv}")
            # 发送整个剧本
            self.send_script(script)

    def add_temp_memory(
        self,
        index: int,
    ) -> Dict[str, List[str]]:
        """
        根据回收的确认包，将所有不大于确认索引的所有剧本内容整理并添加到temp_memory中，对退出的角色返回记忆添加内容和退出时的心情
        memory_add返回值的英文格式事例：
        {
            "Tom": [
            "Tom had a conversation with Lily about "help with the math homework" at the location: Park.",
            "Lily(Sad|Chat|Tom): "Hi, how is it going?" ",
            "Tom(Calm|Chat|Lily): "Hi, I'm fine, but you look unhappy." ",
            "Lily(Sad|Chat|Tom): "Yes, I cannot finish my homework." ",
            "Tom(Calm|Chat|Lily): "Math? Maybe I can help you." ",
            "Lily(Happy|Chat|Tom): "Oh, really? Are you available now?" ",
            "Tom(Calm|Chat|Lily): "Sorry I'm busy now, tonight at 7 I will call you. Bye." ",
            "Lily(Happy|Chat|Tom): "OK, see you tonight!" ",
            "Tom(Calm|Move|Home): None",
            ],
            ...
        }
        mood_change返回值的英文格式事例：
        {
            "Tom": "Calm",
            ...        
        }

        :params index:
        :return memory_add, mood_change:
        """
        # 声明一个返回的记忆添加变量和心情改变变量
        memory_add = {}
        mood_change = {}
        # 如果确认包的索引值符合要求，则处理索引范围内的剧本
        if index > self.index :
            # 遍历temp_lines的每一行剧本，判断其所属类型并更新self.temp_memory和self.names的数值
            for i in range(self.index + 1, index + 1):
                line = self.lines[i]
                # 如果是角色交互类型的剧本行
                if line["type"] == "Interaction":
                    self.temp_memory.append(self.sentences[i])
                    self.script_perform.append(self.sentences[i])
                    self.logger.debug(f"No.{i} Interaction line, added into temp_conversation done")
                # 如果是非结束符的会话状态类型的剧本行
                elif line["type"] == "State" and line["state"] != "结束":
                    # 提取出退出的角色
                    exit_character = line["state"].split("退出")[0].strip()
                    # 如果退出的角色是无人的话，处理下一个剧本行
                    if exit_character == "无人":
                        continue
                    #memory_head = rf"""{"，".join(self.memory_head_names[exit_character])}这{len(self.memory_head_names[exit_character])}个角色在地点{self.location}中共同交流有关{self.topic}的内容。"""
                    memory_head = rf"""{"，".join(self.names)}这{len(self.names)}个角色在地点{self.location}中共同交流有关{self.topic}的内容。"""
                    # 将temp_memory加入到退出角色的记忆中
                    memory_add[exit_character] = [memory_head] + self.temp_memory[self.start_memory[exit_character]:]
                    # 提取退出角色在退出时的心情作为最新的心情
                    mood_change[exit_character] = self.lines[i-1]["mood"]
                    #显示退出角色添加记忆的信息
                    memory_add_str = '\n'.join(memory_add[exit_character])
                    self.logger.info(f"Conversation {self.convo_id} successfully adds memory into NPC {exit_character} with contents:\n{memory_add_str}")
                    # 将角色退出作为客观事实写入temp_memory中
                    self.temp_memory.append(rf"""{exit_character}退出了对话。""")
                    self.script_perform.append(self.sentences[i])
                    # 从会话的角色姓名列表中删除退出的角色并删除相应的对话记忆起始索引值
                    self.names.remove(exit_character)
                    del self.start_memory[exit_character]
                    ## 更新其他角色的会话对象
                    #del self.memory_head_names[exit_character]
                    #for chat_name in self.memory_head_names.keys():
                    #    self.memory_head_names[chat_name] = copy.deepcopy(self.names)
                # Error及结束符这两种类型的剧本行不做处理
                else:
                    continue
            self.index = index
        return memory_add, mood_change

    def send_script(self, script):
        """
        将script发送给游戏
        :param script:
        :return:
        """
        # print item with appropriate color
        # print(f"[Conversation] sending script:\n{script}")
        # print(
        #     "[Conversation] sending script:",
        #     Fore.GREEN,
        #     json.dumps(script).encode(),
        #     Style.RESET_ALL,
        #     "to",
        #     (self.game_url, self.game_port),
        # )
        send_data(sock = self.engine_sock, target_url = self.game_url, 
                  target_port = self.game_port, data = script)

    def send_line(self, line):
        """
        将script发送给游戏
        :param script:
        :return:
        """
        # print item with appropriate color
        # print(f"[Conversation] sending one line of script:{line}")
        # print(
        #     "[Conversation] sending one line of script:",
        #     Fore.GREEN,
        #     json.dumps(line).encode(),
        #     Style.RESET_ALL,
        #     "to",
        #     (self.game_url, self.game_port),
        # )
        send_data(sock = self.engine_sock, target_url = self.game_url, 
                  target_port = self.game_port, data = line)
    
    # 重新设置对话的剧本生成模式，流式还是非流式
    def set_stream(self, stream):
        self.stream = stream

if __name__ == '__main__':
    con = Conversation(1,2,3,{},{},"","")
    '''
    prompt = EnginePrompt()
    con = Conversation(1,2,3,{},{},"","")
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
