import asyncio
import json
import random
import socket
import threading, sys
from pathlib import Path
# 获取当前脚本所在目录的父目录
parent_dir = Path(__file__).parent

# 将父目录添加到模块搜索路径中
sys.path.append(str(parent_dir))


from src.config.config import (
    NPC_CONFIG,
    INIT_PACK,
    ALL_ACTIONS,
    ALL_PLACES,
    ALL_MOODS,
    CONV_CONFIG,
)
from src.engine import *

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

import pytest
import faker

class TestGame():
    def setup_method(
        self, game_url="::1", engine_url="::", engine_port=8199, game_port=8084
    ):
        self.engine = NPCEngine(
            engine_port=engine_port,
            game_url=game_url,
            game_port=game_port,
            model="gpt-3.5-turbo-16k",
        )
        self.engine_url = engine_url
        self.engine_port = engine_port
        self.game_port = game_port
        self.sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.listen_thread = threading.Thread(target=self.listen)
        self.listen_thread.start()

    def teardown_method(self):
        self.engine.close()
        self.sock.close()

    def listen(self):
        self.sock.bind(("::1", self.game_port))
        while True:
            data, addr = self.sock.recvfrom(1024)
            try:
                json_data = json.loads(data.decode())
                # 处理对话包
                if json_data["name"] == "conversation":
                    id = json_data["id"]
                    length = json_data["length"]
                    lines = json_data["lines"]
                    assert len(lines) == length
                    for idx, line in enumerate(lines):
                        print(line)
                        # 回传确认包
                        self.confirm_conversation(id, idx)

                # 处理其他包
                pass
                print(json_data)
            except json.JSONDecodeError:
                pass

    @pytest.mark.run(order=1)
    def test_init_engine(self):
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

    @pytest.mark.run(order=2)
    def test_conversation(self):
        """
        生成10个创建对话包，发送给Engine

        :return:
        """
        sock, engine = self.sock, self.engine
        # 生成10个假对话包数据
        fake = faker.Faker(locale="zh_CN")
        num = 10
        npcs = []
        locations = []
        topics = []
        observations = []
        startings = []
        player_descs = []
        for i in range(num):
            # 随机生成1-5个npc
            npc_num = fake.random_int(min=1, max=5)
            npc = [fake.name() for _ in range(npc_num)]
            # 随机生成地点，话题，打断语，观察语，开始语
            location = fake.address()
            topic = fake.sentence()
            observation = fake.sentence()
            ## 开头starting可能是""或随机生成的句子
            starting = fake.sentence() if fake.random_int(min=0, max=1) else ""
            # 玩家描述
            player_desc = fake.sentence()

            npcs.append(npc), locations.append(location), topics.append(
                topic
            ), observations.append(observation), startings.append(
                starting
            ), player_descs.append(
                player_desc
            )
            CONV_CONFIG.update(
                {
                    "npc": npc,
                    "location": location,
                    "topic": topic,
                    "observation": observation,
                    "starting": starting,
                    "player_desc": player_desc,
                }
            )
            conversation_pack = CONV_CONFIG
            # 使用UDP发送对话包到引擎
            sock.sendto(
                json.dumps(conversation_pack).encode(),
                (engine.game_url, engine.engine_port),
            )

        assert True

    def generate_conversation(self, npc, location, topic, iterrupt_speech):
        conversation_data = {
            "func": "conversation",
            "npc": npc,
            "location": location,
            "topic": topic,
            "iterrupt_speech": iterrupt_speech,
        }
        self.send_data(conversation_data)
        return conversation_data

    async def confirm_conversation(self, conversation_id, index):
        # 随机延迟0-100ms
        await asyncio.sleep(random.random() / 10)
        confirm_data = {
            "func": "confirm_conversation_line",
            "conversation_id": conversation_id,
            "index": index,
        }
        print("confirm_conversation_line", confirm_data)
        self.send_data(confirm_data)

    def calculate_str_size_in_kb(self, string: bytes):
        # 获取字符串的字节数
        byte_size = len(string)
        # 将字节数转换成KB大小
        kb_size = byte_size / 1024
        return kb_size

    def send_data(self, data, max_packet_size=6000):
        # UUID作为消息ID
        msg_id = uuid.uuid4().hex
        # 将json字符串转换为bytes
        data = json.dumps(data).encode('utf-8')
        # 计算数据包总数
        packets = [data[i: i + max_packet_size] for i in range(0, len(data), max_packet_size)]
        total_packets = len(packets)

        for i, packet in enumerate(packets):
            # 构造UDP数据包头部
            #print("sending packet {} of {}, size: {} KB".format(i + 1, total_packets, self.calculate_str_size_in_kb(packet)))
            header = f"{msg_id}@{i + 1}@{total_packets}".encode('utf-8')
            # 发送UDP数据包
            #print()
            self.sock.sendto(header + b"@" + packet, (self.engine_url, self.engine_port))