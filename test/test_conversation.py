import json
import socket
import time
import uuid
import pathlib
import sys
sys.path.append(str(pathlib.Path(__file__).parent.parent.parent))

from npc_engine.src.config.config import PROJECT_ROOT_PATH
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
    初始化包例：
         {"func":"init",
                # 必填字段，代表在什么场景初始化
                "scene":"default_village",
                "language":"E" or "C"
                # 下面是🉑️选
                "npc":[
                    {"name":"李大爷",
                    "desc":"是个好人",
                    "mood":"正常",
                    "position":"李大爷家",
                    "memory":[ ]},

                    {"name":"王大妈",
                    "desc":"是个好人",
                    "mood":"焦急",
                    "position":"王大妈家",
                    "memory":[ ]}
                      ], # 可以留空，默认按照game_world.json+scene初始化场景NPC。非空则在之前基础上添加。
        }
    :return:
    """

    # 初始化包
    pack1 = {"func":"init",
                # 必填字段，代表在什么场景初始化
                "scene_name": "李大爷家",
                "language": "C",
                # 下面是🉑️选
                "npc": []
                    #{"name":"超级史莱姆",
                    #"desc":"喜欢吃人",
                    #"mood":"愤怒",
                    #"location": "村口",
                    #"memory":["20年前吃了两只小狗","15年前吃了三只小猫","9年前吃了三个小孩","6年前吃了两个老人","1年前吃了一家五口人"]}
                    #  ]
        }
    # 发送初始化包到引擎
    print("sending for init")
    send_data(pack1)
    #time.sleep(180)

test_engine_init_memory()

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
            "npc":["李大爷","王大妈"],   # 参与对话的NPC
            "scenario_name": "李大爷家",
            "location":"花园",                # 对话地点
            "topic":"李大爷的人生经历",           # 对话主题,可以留空,gpt会自发选择一个主题。
            "npc_states": [
                {
                  "position": "李大爷家",
                  "observation": {
                          "people": ["王大妈", "村长", "隐形李飞飞"],
                          "items": ["椅子#1","椅子#2","椅子#3[李大爷占用]","床"],
                          "locations": ["李大爷家大门","李大爷家后门","李大爷家院子"]
                                },
                  "backpack":["黄瓜", "1000元", "老报纸"]
                },
                {
                  "position": "李大爷家",
                  "observation": {
                          "people": ["李大爷", "村长", "隐形李飞飞"],
                          "items": ["椅子#1","椅子#2","椅子#3[李大爷占用]","床"],
                          "locations": ["李大爷家大门","李大爷家后门","李大爷家院子"]
                                },
                  "backpack":["优质西瓜", "大砍刀", "黄金首饰"]
                }],
            # 下面是为了解决玩家/npc插入对话的问题
            "starting": "",  # 玩家插入发言,可以留空
            "player_desc": "",
            "memory_k": 3,
            "length": "S",
            "stream": True
        }

    # 发送初始化包到引擎
    print("sending for conversation")
    send_data(pack1)
    #print("all done")

#test_conversation()

def send_pack_create():
    pack1 = {        
            "func":"confirm_conversation_line",
            "conversation_id":"1234567890",
            "index":24
            }
    print("sending pack1")
    send_data(pack1)

def test_conversation_re_creation():
    pack1 = {
        "func":"re_create_conversation",
        "id":"1234567890",
        "character":"警长",
        "interruption": "", # 玩家插入发言,可以留空
        "player_desc": "", # 玩家的个性描述
        "memory_k": 3,
        "length": "M"}
    
    print("sending for conversation re-creation")
    send_data(pack1)

def sent_pack_re_create():
    pack = {        
            "func":"confirm_conversation_line",
            "conversation_id":"1234567890",
            "index":24
            }

    print("sending pack")
    send_data(pack)