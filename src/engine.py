import socket
from typing import List, Dict, Any, Tuple
import json
import threading
from uuid import uuid4
import datetime
import openai
import zhipuai
import re, os, datetime

from npc_engine import *

import colorama
colorama.init()
from colorama import Fore, Style
from npc_engine.src.config.config import ZHIPU_KEY, OPENAI_KEY, OPENAI_BASE, INIT_PACK, NPC_CONFIG, CONV_CONFIG, ALL_ACTIONS, ALL_PLACES, ALL_MOODS

from langchain import text_splitter
zhipuai.api_key = ZHIPU_KEY
openai.api_key = OPENAI_KEY
openai.api_base = OPENAI_BASE


class NPCEngine:
    def __init__(self, engine_port=8199, game_url="::1", game_port=8084, model="gpt-3.5-turbo"):
        print(Fore.BLUE + """
         _   _ ______  _____  _____  _   _  _____  _____  _   _  _____    
        | \ | || ___ \/  __ \|  ___|| \ | ||  __ \|_   _|| \ | ||  ___|   
        |  \| || |_/ /| /  \/| |__  |  \| || |  \/  | |  |  \| || |__     
        | . ` ||  __/ | |    |  __| | . ` || | __   | |  | . ` ||  __|    
        | |\  || |    | \__/\| |___ | |\  || |_\ \ _| |_ | |\  || |___    
        \_| \_/\_|     \____/\____/ \_| \_/ \____/ \___/ \_| \_/\____/ 
        """ + Style.RESET_ALL)
        print("""
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
         \____/ \___/  \__, ||_| |_||_|\_|  |_/ \__,_| \__||_|   |_|/_/\_\
                        __/ |                                             
                       |___/                                              
        """)
        self.engine_port = engine_port
        self.game_url = game_url
        self.game_port = game_port
        self.conversation_dict = {}
        self.npc_dict = {}
        self.sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)  # 使用IPv6地址
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 添加这一行
        # color print
        print(Fore.GREEN + f"listening on [::]:{self.engine_port}, sending data to {self.game_url}:{self.game_port}, using model {model}" + Style.RESET_ALL)
        self.sock.bind(('::', self.engine_port))  # 修改为IPv6地址绑定方式
        self.listen_thread = threading.Thread(target=self.listen)
        self.listen_thread.start()
        self.model = model

    def listen(self):
        """
        监听端口，接收游戏发送的数据,并根据数据调用相应的函数
        :return:
        """
        print(f"listening on [::]:{self.engine_port}")
        while True:
            data, addr = self.sock.recvfrom(1024)
            try:
                json_data = json.loads(data.decode())
                if "func" in json_data:
                    func_name = json_data["func"]
                    if hasattr(self, func_name):
                        func = getattr(self, func_name)
                        func(json_data)
            except json.JSONDecodeError:
                # print the raw data and the address of the sender and the time and the traceback
                print(f"json decode error: {data} from {addr} at {datetime.datetime.now()}")
                # print error getting key
                print(f"error getting key: {json_data['func']}")
            except Exception as e:
                print(f"error: {e}")
                pass

    def create_conversation(self, json_data):
        """
        根据游戏发送的Conversation信息，创建Conversation剧本并返回；
        直到对话都被确认，Conversation才会被销毁，
        否则，存在的Conversation会被保存在self.conversation_dict中。

        {
            "func":"create_conversation",
            "npc":["李大爷","王大妈","村长"],   # 参与对话的NPC
            "location":"酒吧",                # 对话地点
            "topic":"村长的紫色内裤",           # 对话主题,可以留空,gpt会自发选择一个主题。
            "observations":"旁边有两颗大树"，    # 描述的是角色个体或者角色团体观测到的场景信息

            # 下面是为了解决玩家/npc插入对话的问题
            "starting": "你好我是玩家，你们在干什么？"，  # 玩家插入发言,可以留空
            "player_desc": "是一个律师，是小村村长的儿子。"
        }
        :param json_data:
        :return:
        """
        # get language setup and obtain corresponding system_prompt for Conversation
        names: List[str] = json_data['npc']
        npc_refs = [self.npc_dict[name] for name in names]
        location: str = json_data['location']
        topic: str = json_data['topic']

        # 初始化群体描述、心情和记忆
        descs: List[str] = [json_data['player_desc']] + [npc.desc for npc in npc_refs]
        moods:List[str] = [npc.mood for npc in npc_refs]
        memories:List[str] = [npc.memory for npc in npc_refs]

        # 初始化群体观察和常识
        observations:str = json_data['observations']
        all_actions:List[str] = self.knowledge["actions"]
        all_places:List[str] = self.knowledge["places"]
        all_people:List[str] = self.knowledge["people"]
        all_moods:List[str] = self.knowledge["moods"]
        starting:str = json_data['starting']

        # 如果没有指定topic，就GPT生成一个
        if topic == "":
            topic = self.get_random_topic(names, location, observations, self.language)

        # 根据语言选择对应的系统提示函数
        system_prompt_func = getattr(Engine_Prompt, "prompt_for_conversation_" + self.language)
        system_prompt, query_prompt = system_prompt_func(names, location, topic, descs, moods,
                                                         memories, observations, all_actions, all_places, all_people,
                                                         all_moods, starting)

        # 创建Conversation，存入对象字典，生成剧本
        convo = Conversation(names=names, system_prompt=system_prompt, query_prompt=query_prompt,
                             language=self.language, model=self.model)

        self.conversation_dict[convo.id] = convo
        script = convo.generate_script()
        # 发送整个剧本
        self.send_script(script)

    def re_create_conversation(self, json_data):
        """
        根据游戏发送的Conversation打断包中id，找到原来的Conversation对象，重新生成剧本并返回；
        打断包例:
        {
        "func":"re_create_conversation",
        "id":"1234567890"
        "interruption": "我认为这边" # 玩家插入发言,可以留空
        }
        :param json_data:
        :return:
        """
        conversation_id = json_data["conversation_id"]
        interruption = json_data['interruption']
        if conversation_id in self.conversation_dict:
            convo = self.conversation_dict[conversation_id]
            script = convo.re_create_conversation(interruption)
            self.send_script(script)

    def get_random_topic(self, names: List[str], location: str, observations: str, language: str) -> str:
        """
        使用GPT为对话生成一个随机的topic
        :param names: 参与对话的NPC名称列表
        :param location: 对话地点
        :param observations: 观测到的场景信息
        :param language: 语言
        :return: 随机生成的话题
        """
        system_topic, query_prompt = Engine_Prompt.prompt_for_topic(names=names, location=location,
                                                                    observations=observations, language=language)
        response = openai.ChatCompletion.create(model=self.model, messages=[system_topic, query_prompt])
        topic: str = response["choices"][0]["message"]["content"].strip()
        return topic

    def init(self, json_data):
        """
        按照json来初始化NPC和NPC的常识
        例子：
        {"func":"init",
                 "npc":[
                    {"name":"李大爷",
                    "desc":"是个好人",
                    "mood":"正常",
                    "location":"李大爷家",
                    "memory":[ ]},

                    {"name":"王大妈",
                    "desc":"是个好人",
                    "mood":"焦急",
                    "location":"王大妈家",
                    "memory":[ ]}
                      ],
                 "knowledge":{
                    "all_actions" = ["stay", "move", "chat"],
                     "all_places" = ["李大爷家", "王大妈家", "广场", "瓜田", "酒吧", "警局"],
                     "all_moods" = ["正常", "焦急", "严肃", "开心", "伤心"],
                     "all_people" = ["李大爷","王大妈","村长","警长"],
                             }，
                "language":"E" or "C"
        }
        :param json_data:
        :return:
        """
        npc_list = json_data["npc"]
        self.knowledge = json_data["knowledge"]
        self.language = json_data["language"]
        for npc_data in npc_list:
            npc = NPC(name=npc_data["name"], desc=npc_data["desc"], mood=npc_data["mood"],
                      location=npc_data["location"],
                      knowledge=self.knowledge, memory=npc_data["memory"], model=self.model)  # todo:👀NPC观察也就是ob没有做
            self.npc_dict[npc.name] = npc
            print("inited npc:", npc.name, npc.desc, npc.location, npc.mood)


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

        conversation_id = json_data["conversation_id"]
        index = json_data["index"]
        if conversation_id in self.conversation_dict:
            convo = self.conversation_dict[conversation_id]
            judge = convo.add_memory(conversation_id, index)
            if judge:
                self.npc_add_memory(convo)

    def npc_add_memory(self, convo):
        """
        将对话的内容添加到对应NPC的记忆list中，以第三人称的方式
        例如：
            李大爷 talked with 王大妈,村长 from 2021-01-01 12:00:00 to 2021-01-01 12:00:00.
            (被放入李大爷的记忆中)
        :param convo:
        :return:
        """
        # 得到对话类中的人名列表
        names = convo.names
        # 对每个人名，生成一条记忆，放入对应的NPC的记忆list中
        for i in range(len(names)):
            person_name = names[i]
            the_other_names = names[:i] + names[i + 1:]
            pre_inform = rf"{person_name} talked with {','.join(the_other_names)} from {convo.start_time} to {convo.end_time}. \n"
            new_memory = pre_inform + '\n'.join(convo.temp_memory) + '\n'
            npc = self.npc_dict[person_name]
            npc.memory.append(new_memory)

    def send_script(self, script):
        """
        将script发送给游戏
        :param script:
        :return:
        """
        # print item with appropriate color
        print("sending script:", Fore.GREEN, json.dumps(script).encode(), Style.RESET_ALL,
              "to", (self.game_url, self.game_port))
        self.sock.sendto(json.dumps(script).encode(), (self.game_url, self.game_port))

    def close(self):
        """
        关闭socket,结束Engine
        保存所有NPC的记忆到本地
        :return:
        """
        self.sock.close()
        print("socket closed")
        for npc in self.npc_dict.values():
            npc.save_memory()
        print("all memory saved")
        print("Engine closed")