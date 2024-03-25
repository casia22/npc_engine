import json
import socket
import time
import uuid
import pathlib
import sys
sys.path.append(str(pathlib.Path(__file__).parent.parent.parent))

PROJECT_ROOT_PATH = pathlib.Path(__file__).parent.parent.parent / "example_project"
import threading

engine_url = "::1"
engine_port = 8199
game_url = "::1"
game_port = 8084
sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
sock.bind(("::1", game_port))

def send_data(data, max_packet_size=6000):
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
            sock.sendto(header + b"@" + packet, (engine_url, engine_port))
        #sock.close()

def test_engine_init_memory():

    """
    测试引擎初始化
    向引擎发送初始化包，检查引擎是否正确初始化
    """

    # 初始化包
    pack1 = {"func":"init",
                # 必填字段，代表在什么场景初始化
                "scene_name": "荒野小镇",
                "language": "C",
                # 下面是🉑️选
                "npc": []}
    # 发送初始化包到引擎
    print("sending for init")
    send_data(pack1)
    #time.sleep(180)

test_engine_init_memory()
time.sleep(5)

def test_conversation():

    """
    测试引擎wake_up函数
    向引擎发送初始化包，检查引擎是否正确初始化
    wakeup包例：
        {
            "func":"wake_up",
            "npc_name": "王大妈",
            "position": "李大爷家",
            "observation": ["李大爷", "椅子#1","椅子#2","椅子#3[李大爷占用]",床]
            "time": "2021-01-01 12:00:00", # 游戏世界的时间戳
        }
    预期返回包:
    {
            "name":"action",
            "npc_name":"王大妈",
            "action":"chat",
            "object":"李大爷",
            "parameters":["你吃饭了没？"],
        }
    :return:
    """

    # 初始化包
    pack1 = {
            "func":"create_conversation",
            "npc":["土匪Red","土匪Slim","牛仔John"],   # 参与对话的NPC
            "scenario_name": "荒野小镇",
            "location":"荒野小镇",                # 对话地点
            "topic":"土匪Red的经历",           # 对话主题,可以留空,gpt会自发选择一个主题。
            "npc_states": [
                {
                  "position": "荒野小镇",
                  "observation": {
                          "people": ["警长Woody", "土匪Slim"],
                          "items": ["椅子1","椅子2","椅子3","床"],
                          "locations": []
                                },
                  "backpack":["黄瓜", "1000元", "老报纸"]
                },
                {
                  "position": "李大爷家",
                  "observation": {
                          "people": ["警长Woody", "土匪Red"],
                          "items": ["椅子1","椅子2","椅子3","床"],
                          "locations": []
                                },
                  "backpack":["优质西瓜", "大砍刀", "黄金首饰"]
                }],
            # 下面是为了解决玩家/npc插入对话的问题
            "starting": "嘿你们在干什么呢",  # 玩家插入发言,可以留空
            "player_desc": "是一位来自未来世界的枪手，有非常精湛的射击技术。",
            "memory_k": 3,
            "length": "S",
            "stream": True
        }

    # 发送初始化包到引擎
    print("sending for conversation")
    send_data(pack1)

test_conversation()
time.sleep(9)

def send_pack_create():
    pack1 = {        
            "func":"confirm_conversation_line",
            "conversation_id":"76ee76f0-7d13-499b-a8ad-c4744cf44aea",
            "index":18
            }
    print("sending pack1")
    send_data(pack1)

#send_pack_create()
#time.sleep(5)

def test_conversation_re_creation():
    pack1 = {
        "func":"re_create_conversation",
        "id":"1234567890",
        "character":"警长",
        "interruption": "", # 玩家插入发言,可以留空
        "player_desc": "", # 玩家的个性描述
        "memory_k": 3,
        "length": "M",
        "stream": True}
    
    print("sending for conversation re-creation")
    send_data(pack1)

#test_conversation_re_creation()
#time.sleep(10)

def close_engine():
    pack1 = {
        "func":"close"
    }
    
    print("send package to close engine")
    send_data(pack1)

#close_engine()
#time.sleep(5)