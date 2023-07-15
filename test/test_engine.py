import asyncio
import json
import random
import socket
import threading, sys
import time
import uuid
from pathlib import Path

# 获取当前脚本所在目录的父目录
parent_dir = Path(__file__).parent

# 将父目录添加到模块搜索路径中
sys.path.append(str(parent_dir))

from npc_engine import (
    NPC_CONFIG,
    INIT_PACK,
    ALL_ACTIONS,
    ALL_PLACES,
    ALL_MOODS,
    CONV_CONFIG,
)
from npc_engine import *

from npc_engine.src.config.config import (
    ZHIPU_KEY,
    OPENAI_KEY,
    OPENAI_BASE,
    INIT_PACK,
    NPC_CONFIG,
    CONV_CONFIG,
    ALL_ACTIONS,
    ALL_PLACES,
    ALL_MOODS,
)
import pytest
import faker


class TestGame():
    def setup_class(
        self, game_url="::1", engine_url="::1", engine_port=8199, game_port=8084
    ):
        print("setup_class")
        self.engine = NPCEngine(
            engine_port=engine_port,
            game_url=game_url,
            game_port=game_port,
            model="gpt-3.5-turbo",
        )
        self.engine_url = engine_url
        self.engine_port = engine_port
        self.game_url = game_url
        self.game_port = game_port
        self.sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 添加这一行
        self.sock.bind((self.game_url, self.game_port))
        # faker
        # 生成包括200个NPC的初始包数据
        self.npc_num = 200
        self.fake = faker.Faker(locale="zh_CN")
        self.names = [self.fake.unique.name() for _ in range(self.npc_num)]

    def teardown_class(self):
        print("teardown_class")
        self.engine.close()
        self.sock.close()

    def listen(self, buffer_size=6000):
        print("LISTENING")
        buffer = {}
        while True:
            data, addr = self.sock.recvfrom(buffer_size)
            # 解析UDP数据包头部
            msg_id, packet_no, total_packets, pack = data.split(b'@', 3)
            print("GAME LISTEN RECIEVED:", msg_id, packet_no, total_packets)
            packet_no = int(packet_no)
            total_packets = int(total_packets)
            # 缓存数据包
            if msg_id not in buffer:
                buffer[msg_id] = [b''] * total_packets
            buffer[msg_id][packet_no - 1] = pack
            # 检查是否所有数据包都已接收
            if not any(part == b'' for part in buffer[msg_id]):
                # 重组消息
                msg_str = b''.join(buffer[msg_id]).decode('utf-8')
                msg = json.loads(json.loads(msg_str))
                try:
                    # 根据func键值调用相应的函数
                    if msg["name"] == "inited":
                        print("init_confirm")
                    if msg["name"] == "conversation":
                        print("收到 CONVERSATION包")
                        msg_id = msg["id"]
                        length = msg["length"]
                        lines = msg["lines"]
                        assert len(lines) == length
                        for idx, line in enumerate(lines):
                            print(line)
                            # 回传确认包
                            self.confirm_conversation(msg_id, idx)
                        return
                except json.JSONDecodeError:
                    print("json.JSONDecodeError, msg:", msg)
                except:
                    import traceback
                    traceback.print_exc()

    @pytest.mark.run(order=1)
    def test_init_engine(self):
        """
        生成若干NPC的初始包，发送给Engine
        :return:
        """
        self.listen_thread = threading.Thread(target=self.listen)
        self.listen_thread.start()
        sock, engine = self.sock, self.engine
        print("running test test_engine.py::TestGame::test_init_engine")

        descriptions = [self.fake.text() for _ in range(self.npc_num)]
        moods = [
            self.fake.random_element(elements=("正常", "焦急", "严肃", "开心", "伤心"))
            for _ in range(self.npc_num)
        ]
        addresses = [self.fake.address() for _ in range(self.npc_num)]
        # 生成每个NPC的记忆,每个NPC的记忆随机多条
        event_descriptions = [[self.fake.sentence() for _ in range(self.fake.random_int(min=1, max=5))] for i in range(self.npc_num)]
        npc_jsons = []
        for i in range(self.npc_num):
            NPC_CONFIG.update(
                {
                    "name": self.names[i],
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
                    "actions": ALL_ACTIONS,
                    "places": ALL_PLACES,
                    "moods": ALL_MOODS,
                    "people": self.names
                            },
                "language":"C"
            }
        )
        init_pack = INIT_PACK
        # 使用UDP发送初始包到引擎
        self.send_data(
            init_pack
        )
        time.sleep(10)
        print("test_init_engine done")
        # print(self.engine.npc_dict.keys())
        assert len(self.engine.npc_dict.keys())==self.npc_num

    @pytest.mark.run(order=2)
    def test_conversation(self):
        """
        生成10个创建对话包，发送给Engine

        :return:
        """

        print("\n running test test_engine.py::TestGame::test_conversation")
        # 生成10个假对话包数据
        fake = faker.Faker(locale="zh_CN")
        num = 3
        npcs = []
        locations = []
        topics = []
        observations = []
        startings = []
        player_descs = []
        for i in range(num):
            # 从self.names随机选择2-5个NPC
            npc_num = fake.random_int(min=2, max=5)
            npc = fake.random_elements(elements=self.names, length=npc_num)
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
            print("sending conversation_pack")
            self.send_data(
                conversation_pack
            )
        time.sleep(60)
        assert len(self.engine.conversation_dict.keys())==num

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
