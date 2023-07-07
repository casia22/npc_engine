import socket
import json
import threading
import faker

target_port = 8199
listen_port = 8084

from src.config.config import (
    ZHIPU_KEY,
    OPENAI_KEY,
    OPENAI_BASE,
    INIT_PACK,
    NPC_CONFIG,
    CONV_CONFIG,
    ALL_ACTIONS,
    ALL_PLACES,
    ALL_MOODS)

from src.engine import *


class Game:
    def __init__(self, target_url="::1", target_port=target_port, listen_port=listen_port):
        self.target_url = target_url
        self.target_port = target_port
        self.listen_port = listen_port
        self.sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.listen_thread = threading.Thread(target=self.listen)
        self.listen_thread.start()

        self.engine = NPCEngine(
            engine_port=target_port,
            game_url=target_url,
            game_port=listen_port,
            model="gpt-3.5-turbo",
        )
    def listen(self):
        self.sock.bind(('::1', self.listen_port))
        while True:
            data, addr = self.sock.recvfrom(1024)
            try:
                json_data = json.loads(data.decode())
                print(json_data)
            except json.JSONDecodeError:
                pass

    def init_engine(self):
        """
        生成若干NPC的初始包，发送给Engine
        :return:
        """
        sock, engine = self.sock, self.engine
        npc_num = 200
        # 生成包括200个NPC的初始包数据
        fake = faker.Faker(locale="zh_CN")
        names = [fake.name() for _ in range(npc_num)]
        descriptions = [fake.text() for _ in range(npc_num)]
        moods = [
            fake.random_element(elements=("正常", "焦急", "严肃", "开心", "伤心"))
            for _ in range(npc_num)
        ]
        addresses = [fake.address() for _ in range(npc_num)]
        # 生成每个NPC的记忆,每个NPC的记忆随机多条
        event_descriptions = [[fake.sentence() for _ in range(fake.random_int(min=1, max=5))] for i in range(npc_num)]
        npc_jsons = []
        for i in range(npc_num):
            NPC_CONFIG.update(
                {
                    "name": names[i],
                    "desc": descriptions[i],
                    "mood": moods[i],
                    "location": addresses[i],
                    "memory": event_descriptions[i],
                }
            )
            npc_jsons.append(NPC_CONFIG.copy())
        INIT_PACK.update(
            {
                "npc": npc_jsons,
                "knowledge": {
                    "all_actions": ALL_ACTIONS,
                    "all_places": ALL_PLACES,
                    "all_moods": ALL_MOODS,
                    "all_people": names
                            },
                "language":"C"
            }
        )
        init_pack = INIT_PACK
        # 使用UDP发送初始包到引擎
        sock.sendto(
            json.dumps(init_pack).encode(), (engine.game_url, engine.engine_port)
        )
        assert True

    def generate_conversation(self, npc, location, topic, observation, starting, player_desc):
        conversation_data = {
            "func": "create_conversation",
            "npc": npc,
            "location": location,
            "topic": topic,
            "observation": observation,
            "starting": starting,
            "player_desc": player_desc
        }
        self.send_data(conversation_data)
        return conversation_data

    def confirm_conversation(self, conversation_id, index):
        confirm_data = {
            "func": "confirm_conversation_line",
            "conversation_id": conversation_id,
            "index": index
        }
        self.send_data(confirm_data)

    def send_data(self, data):
        self.sock.sendto(json.dumps(data).encode(), (self.target_url, self.target_port))
   
game = Game()
game.init_engine()
res = game.generate_conversation(["李大爷", "王大妈", "村长"], "酒吧", "村长的紫色内裤", "旁边有两颗大树", "你好我是玩家，你们在干什么？", "是一个律师，是小村村长的儿子。")
#game.confirm_conversation("8bd7a1bd-3c20-4102-be4f-0426e149d19f", 24)