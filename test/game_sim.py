import socket
import json
import uuid
import time
import threading

# 监听的地址和端口
UDP_IP = "::1"
UDP_PORT = 8084

# 发送数据的地址和端口
engine_url = "::1"
engine_port = 8199

# 创建socket
sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

# 准备数据包
init_packet = {
    "func": "init",
    "scene_name": "雁栖村",
    "language": "C",
    "npc": []
}
wakeup_packet = {
    "func": "wake_up",
    "npc_name": "王大妈",
    "scenario_name": "李大爷家",
    "npc_state": {
        "position": "李大爷家卧室",
        "observation": {
            "people": ["李大爷", "村长", "隐形李飞飞"],
            "items": ["椅子#1", "椅子#2", "椅子#3[李大爷占用]", "床[包括:被子、枕头、床单、床垫、私房钱]"],
            "locations": ["李大爷家大门", "李大爷家后门", "李大爷家院子"]
        },
        "backpack": ["优质西瓜", "大砍刀", "黄金首饰"]
    },
    "time": "2021-01-01 12:00:00",
}

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
        header = f"{msg_id}@{i + 1}@{total_packets}".encode('utf-8')
        # 发送UDP数据包
        sock.sendto(header + b"@" + packet, (engine_url, engine_port))
        print(f"Sent UDP packet: {header.decode('utf-8')}@{packet.decode('utf-8')}")

def listen():
    print("Listening on [{}]:{}".format(UDP_IP, UDP_PORT))
    while True:
        data, addr = sock.recvfrom(4000)
        # get json packet from udp
        data = data.decode('utf-8')
        json_str = data.split('@')[-1]
        json_data = json.loads(json_str)
        print("Received UDP packet from {}: {}".format(addr, json_data))

def send_packets():
    while True:
        send_data(init_packet)
        send_data(wakeup_packet)
        time.sleep(10)

# 分别启动监听和发送数据包的线程
threading.Thread(target=listen).start()
threading.Thread(target=send_packets).start()
