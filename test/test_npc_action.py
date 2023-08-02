"""
NPC自主行为的测试用例
本脚本只发包，测试结果需要手动查看logs文件夹下对应时间戳的日志。
例如：
    npc_engine/logs/engine_2023-07-29-23:58:57.log
"""

import json
import socket
import time
import uuid
import logging
import multiprocessing
import time,os


from npc_engine.src.engine import NPCEngine
from npc_engine.src.config.config import FILE_HANDLER, CONSOLE_HANDLER, PROJECT_ROOT_PATH

logger = logging.getLogger("TEST")
logger.addHandler(CONSOLE_HANDLER)
logger.addHandler(FILE_HANDLER)
logger.setLevel(logging.DEBUG)

# 启动服务器进程
path = PROJECT_ROOT_PATH / "src" / "engine.py"
os.popen("python " + str(path))

def send_data(data, max_packet_size=6000):
        engine_url = "::1"
        engine_port = 8199
        game_url = "::1"
        game_port = 8084
        sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        sock.bind(("::1", game_port))

        # UUID作为消息ID
        msg_id = uuid.uuid4().hex
        # 将json字符串转换为bytes
        data = json.dumps(data).encode('utf-8')
        # 计算数据包总数
        packets = [data[i: i + max_packet_size] for i in range(0, len(data), max_packet_size)]
        total_packets = len(packets)
        for i, packet in enumerate(packets):
            # 构造UDP数据包头部
            header = f"{msg_id}@{i + 1}@{total_packets}".encode('utf-8')
            # 发送UDP数据包
            sock.sendto(header + b"@" + packet, (engine_url, engine_port))
        sock.close()


def test_engine_init():

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
                    "location":"李大爷家",
                    "memory":[ ]},

                    {"name":"王大妈",
                    "desc":"是个好人",
                    "mood":"焦急",
                    "location":"王大妈家",
                    "memory":[ ]}
                      ], # 可以留空，默认按照game_world.json+scene初始化场景NPC。非空则在之前基础上添加。

        }
    :return:
    """

    # 初始化包
    pack1 = {"func":"init",
                # 必填字段，代表在什么场景初始化
                "scene": "default_village",
                "language": "C",
                # 下面是🉑️选
                "npc": [
                    {"name":"超级史莱姆",
                    "desc":"喜欢吃人",
                    "mood":"愤怒",
                    "location": "村口",
                    "memory":[]},

                    {"name":"警长",
                    "desc":"是个好人,但是不喜欢超级史莱姆，非常会使用武器，很勇敢",
                    "mood":"焦急",
                    "location":"村口",
                    "memory":[]}
                      ]
        }
    pack2 = {"func": "init",
             # 必填字段，代表在什么场景初始化
             "scene": "default_village",
             "language": "C",
             # 下面是🉑️选
             "npc": []
             }
    # 发送初始化包到引擎
    print("sending first")
    send_data(pack1)
    time.sleep(5)
    print("sending second")
    send_data(pack2)
    print("all done")

def test_get_purpose():
    """
    测试NPC的目的生成
    :return:
    """
    pass

def test_get_action():
    """
    测试NPC的动作生成
    :return:
    """
    pass

def test_action_done():
    """
    发送动作完成包到引擎
    GAME发送
    的包：

    {
        "func":"action_done",
        "npc_name":"王大妈",
        "status": "success",
        "time": "2021-01-01 12:00:00", # 游戏世界的时间戳

        "observation": ["李大爷", "村长", "椅子#1","椅子#2","椅子#3[李大爷占用]",床], # 本次动作的观察结果
        "position": "李大爷家", # NPC的位置
        "action":"mov",
        "object":"李大爷家",
        "parameters":[],
        "reason": "", # "王大妈在去往‘警察局’的路上被李大爷打断"
    }

    引擎返回的包：
    {
        "func":"action_done",
        "npc_name":"王大妈",
        "action":"chat",
        "object":"李大爷",
        "parameters":["你吃饭了没？"],
    }

    :return:
    """

    action_done_pack =  {
        "func":"action_done",
        "npc_name":"王大妈",
        "status": "success",
        "time": "2021-01-01 13:00:00", # 游戏世界的时间戳

        "observation": ["李大爷", "村长", "椅子#1","椅子#2","椅子#3[李大爷占用]","床"], # 本次动作的观察结果
        "position": "李大爷家", # NPC的位置

        "action":"chat",
        "object":"李大爷",
        "parameters":['李大爷', '你吃了吗？'],
        "reason": "", # "王大妈在去往‘警察局’的路上被李大爷打断"
    }
    send_data(action_done_pack)
    print("all done")
    time.sleep(10)


def test_wake_up():

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
            "func":"wake_up",
            "npc_name": "王大妈",
            "position": "李大爷家",
            "observation": ["李大爷", "椅子#1","椅子#2","椅子#3[李大爷占用]","床"],
            "time": "2021-01-01 12:00:00", # 游戏世界的时间戳
        }
    # 发送初始化包到引擎
    print("sending first")
    send_data(pack1)
    print("all done")
    time.sleep(10)
