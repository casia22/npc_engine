"""
NPC自主行为的测试用例
本脚本只发包，测试结果需要手动查看logs文件夹下对应时间戳的日志。
例如：
    nuwa/logs/engine_2023-07-29-23:58:57.log
"""

import json
import socket
import time
import uuid
import logging
import multiprocessing
import time,os

from nuwa.src.engine import NPCEngine
from nuwa.src.config.config import FILE_HANDLER, CONSOLE_HANDLER, PROJECT_ROOT_PATH
from nuwa.test.test_config.test_packets import init_packet, wakeup_packet_1, wakeup_packet_2, wakeup_packet_3, \
                                     action_done_packet_1,action_done_packet_2


logger = logging.getLogger("TEST")
logger.addHandler(CONSOLE_HANDLER)
logger.addHandler(FILE_HANDLER)
logger.setLevel(logging.DEBUG)

# # 启动服务器进程
# path = PROJECT_ROOT_PATH / "src" / "engine.py"
# os.popen("python " + str(path))

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
         请参考test_config.test_packets
    :return:
    """
    print(init_packet)
    # 发送初始化包到引擎
    print("sending first")
    send_data(init_packet)
    print("sent first")

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
    GAME发送的包：
    参考test_config.test_packets
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

    print("sending")
    send_data(action_done_packet_1)
    print(action_done_packet_1)
    send_data(action_done_packet_2)
    print(action_done_packet_2)
    print("all done")

def test_wake_up():
    """
    测试引擎wake_up函数
    向引擎发送初始化包，检查引擎是否正确初始化
    wakeup包例：
        请参考test_config.test_packets
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
    # 发送初始化包到引擎
    print("sending first")
    send_data(wakeup_packet_1)
    print(wakeup_packet_1)
    send_data(wakeup_packet_2)
    print(wakeup_packet_2)
    send_data(wakeup_packet_3)
    print(wakeup_packet_1)
    print("all done")
