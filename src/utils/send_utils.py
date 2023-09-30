"""
Filename: send_utils.py
Author: Mengshi, Yangzejun
Contact: ..., yzj_cs_ilstar@163.com
"""
import json
import uuid

def send_data(sock, target_url, target_port, data, max_packet_size=6000):
    """
    把DICT数据发送给游戏端口
    :param sock:
    :param target_url:
    :param target_port:
    :param data:
    :param max_packet_size:
    :return:
    """
    # UUID作为消息ID
    msg_id = uuid.uuid4().hex
    # 将json字符串转换为bytes
    data = json.dumps(data).encode("utf-8")
    # 计算数据包总数
    packets = [
            data[i : i + max_packet_size] for i in range(0, len(data), max_packet_size)]
    total_packets = len(packets)
    print(total_packets)

    for i, packet in enumerate(packets):
        # 构造UDP数据包头部
        print(
            "sending packet {} of {}, size: {} KB".format(
                i + 1, total_packets, calculate_str_size_in_kb(packet)))
        header = f"{msg_id}@{i + 1}@{total_packets}".encode("utf-8")
        # 发送UDP数据包
        sock.sendto(header + b"@" + packet, (target_url, target_port))

def calculate_str_size_in_kb(string: bytes):
    # 获取字符串的字节数
    byte_size = len(string)
    # 将字节数转换成KB大小
    kb_size = byte_size / 1024
    return kb_size