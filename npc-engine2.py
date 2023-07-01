import socket
import json
import threading
from uuid import uuid4
import datetime
import openai
import zhipuai
import re, os, datetime

zhipuai.api_key = '3fe121b978f1f456cfac1d2a1a9d8c06.iQsBvb1F54iFYfZq'
openai.api_key = "sk-8p38chfjXbbL1RT943B051229a224a8cBdE1B53b5e2c04E2"
openai.api_base = "https://api.ai-yyds.com/v1"


class NPC:
    def __init__(self, name, desc, knowledge, location, mood="正常",ob=[],memory=[],model="gpt-3.5-turbo"):
        # model
        self.model = model
        # NPC固定参数
        self.name = name
        self.desc = desc
        # NPC的常识
        self.actions = knowledge["actions"]
        self.place = knowledge["place"]
        self.moods = knowledge["moods"]
        self.people = knowledge["people"]
        # NPC的状态
        self.knowledge = knowledge
        self.observation = ob
        self.action = ''
        self.params = ''
        self.mood = mood
        self.location = location
        # NPC的记忆
        self.memory = memory
        self.memory.extend([
            {"role": "system", "content": rf"""
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
            """},
        ])
        if self.model.startswith("chatglm"):
            self.memory[0]["role"] = "user"
            self.memory.append({"role": "assistant", "content": "好的，下面我会按照您的要求扮演。"})
            

    def process_response(self, response):
        # 例:名字|语言内容|情绪|情绪状态|动作|动作名｜动作参数
        response = re.sub(r'(\\)+("|\'|\\)', '', response)
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
        except:
            print("回复未能按照模版", name, content, mood, action, params)
            print("")
            pass
        return name, content, mood, action, params

    def to_json(self, name, content, mood, action, params):
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
            "action": {"name": action, "params": params}
        }
        return json

    def call_openai(self):
        response = openai.ChatCompletion.create(model=self.model,
                                                messages=self.memory)
        words = response["choices"][0]["message"]["content"].strip()
        words = re.sub(r'(\\)+("|\'|\\)', '', words)
        return words

    def call_zhipuai(self):
        response = zhipuai.model_api.invoke(
            model=self.model,
            prompt=self.memory,
            temperature=self.temperature,
            top_p=self.top_p,
        )
        words = response['data']['choices'][0]['content'].strip()
        words = re.sub(r'(\\)+("|\'|\\)', '', words)
        return words

    def append_memory(self, memory):
        self.memory.append(memory)

    def listen(self, content, npc):
        content = re.sub(r'(\\)+("|\'|\\)', '', content)
        name, content, mood, action, params = self.process_response(content)
        response_template = rf"{npc.name}|{content}|情绪|{npc.mood}|动作|{npc.action}|{npc.params}"
        self.memory.append({"role": "user", "content": response_template})

    def say(self):
        assert self.memory[-1]["role"] == "user", rf"{self.name}:请先让对方NPC说话"
        try:
            if self.model.startswith("gpt"):
                words = self.call_openai()
            elif self.model.startswith("chatglm"):
                words = self.call_zhipuai()
            name, content, mood, action, params = self.process_response(words)
            print(self.to_json(self.name, content, mood, action, params))
            self.memory.append(
                {"role": "assistant", "content": f"{self.name}|{content}|情绪|{mood}|动作|{action}|{params}"})
            return words
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error occurred: {e}")
            print(self.to_json(self.name, content, mood, action, params))
            return f"{self.name}|{content}|情绪|{mood}|动作|{action}|{params}"


class Conversation:
    def __init__(self, npc, location, topic, iterrupt_speech):
        self.npc = npc
        self.location = location
        self.topic = topic
        self.iterrupt_speech = iterrupt_speech
        self.id = str(uuid4())

    def add_memory(self, conversation_id, index):
        # Add memory logic here
        print("add_memory:",conversation_id, index, datetime.datetime.now())
        pass

    def generate_script(self):
        # Generate script logic here
        script = {
            "name": "conversation",
            "id": self.id,
            "length": 24,
            "lines": [
                # Add conversation lines here
            ]
        }
        return script


class NPCEngine:
    def __init__(self, listen_port=8199, target_url="::1", target_port=8084):
        self.port = listen_port
        self.target_url = target_url
        self.target_port = target_port
        self.conversation_dict = {}
        self.npc_dict = {}
        self.sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)  # 使用IPv6地址
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 添加这一行
        print(('::', self.port))
        self.sock.bind(('::', self.port))  # 修改为IPv6地址绑定方式
        self.listen_thread = threading.Thread(target=self.listen)
        self.listen_thread.start()

    def listen(self):
        print(f"listening on [::]:{self.port}")
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
                pass

    def conversation(self, json_data):
        # 获取参数
        npc = json_data["npc"]
        location = json_data["location"]
        topic = json_data["topic"]
        iterrupt_speech = json_data["iterrupt_speech"]
        # 实例化Conversation
        convo = Conversation(npc, location, topic, iterrupt_speech)
        self.conversation_dict[convo.id] = convo
        script = convo.generate_script()
        self.send_script(script)

    def init(self, json_data):
        # 按照json来初始化NPC和NPC的常识
        npc_list = json_data["npc"]
        knowledge = json_data["knowledge"]
        for npc_data in npc_list:
            npc = NPC(name = npc_data["name"], desc=npc_data["desc"], mood = npc_data["mood"],location= npc_data["location"], knowledge=knowledge, memory = npc_data["memory"]) # todo:👀NPC观察也就是ob没有做
            self.npc_dict[npc.name] = npc
            print("inited npc:", npc.name, npc.desc,npc.location, npc.mood, npc.memory)

    def confirm_conversation_line(self, json_data):
        conversation_id = json_data["conversation_id"]
        index = json_data["index"]
        if conversation_id in self.conversation_dict:
            convo = self.conversation_dict[conversation_id]
            convo.add_memory(conversation_id, index)
    
            
    def send_script(self, script):
        print("sending:",json.dumps(script).encode(), "to", (self.target_url, self.target_port))
        self.sock.sendto(json.dumps(script).encode(), (self.target_url, self.target_port))


if __name__ == "__main__":
    npc_engine = NPCEngine()
