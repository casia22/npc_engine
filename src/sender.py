import socket
import json
import threading
import faker

target_port = 8199
listen_port = 8084

from config.config import (
    ZHIPU_KEY,
    OPENAI_KEY,
    OPENAI_BASE,
    INIT_PACK,
    NPC_CONFIG,
    CONV_CONFIG)

from engine import *


class Game:
    def __init__(self, target_url="::1", target_port=target_port, listen_port=listen_port):
        self.target_url = target_url
        self.target_port = target_port
        self.listen_port = listen_port
        self.sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.listen_thread = threading.Thread(target=self.listen)
        self.listen_thread.start()

        #self.engine = NPCEngine(
        #    engine_port=target_port,
        #    game_url=target_url,
        #    game_port=listen_port,
        #    model="gpt-3.5-turbo",
        #)
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
        #sock, engine = self.sock, self.engine
        ALL_ACTIONS = ["对话", "前往", "挠头"]
        ALL_MOODS = ["稳定", "焦急", "严肃", "开心", "伤心", "生气", "郁闷", "惊讶"]
        ALL_PLACES = ["卫生间","医院","花园","宿舍","教学楼","食堂","超市", "图书馆"]
        names = ["英华","泽君","楠楠","王奎","家龙","兴华"]
        descriptions = ["长得很漂亮，脾气很好，喜欢吃鸡爪，肤白貌美大长腿。",
                        "很胖，喜欢玩游戏，无肉不欢，代码能力强，43码的大脚。",
                        "脾气很好，长得好看，很爱学习，很喜欢吃肉。",
                        "在做计算机行业，喜欢吃虾，又高又瘦。",
                        "很傲娇，喜欢吃虾，无肉不欢，又高又瘦。",
                        "话痨，脾气很好，喜欢吃肉，喜欢玩游戏。"]
        moods = ["稳定", "稳定", "稳定", "稳定", "稳定", "稳定"]
        addresses = ["医院","食堂","教学楼","卫生间","花园","图书馆"]
        event_descriptions = [ ["2009年获得奥林匹克数学比赛小学组铜牌","2013年去新加坡访学","2015年以自主招生考试成绩排名前100进入合肥市168高中，免学费","2018年以高考645分考入电子科技大学","2021年以年级排名第6保送到中国科学院","2022年以第一作者身份发表了学术论文到中国自动化大会"],
                               ["2015年以文科生身份就读平泉市第一高中","2018年以高考588分考入西南民族大学","2019年加入到大学学生会公关部","2021年底与一位大帅哥谈恋爱","2022年考研以年级第4考入本校读研究生","2023年获得8000元奖学金"],
                               ["2014年在中学与一个男生谈恋爱","2018年570分考入河北经贸大学","2019年因为男朋友出轨而分手","2021年谈第二个男朋友","2022年因为性格不合与第二个男朋友又分手","2023年谈了第三个男朋友"],
                               ["2008年小学辍学","2012年自学成才考入平泉市第一初中","2014年初中辍学","2017年开公司卖衣服","2020年年收入2000万","2022年公司破产"],
                               ["2005年幼儿园辍学","2008年参加北京奥运会夺得金牌","2012年回家乡创业做农产品售卖","2016年年收入700万","2018年创业公司上市","2022年从公司辞去董事职务"],
                               ["2008年获得编程竞赛小学组银牌","2013年以中考全市第一的成绩进入最好的高中","2016年以高考703分的成绩获得全省状元并被北京大学光华管理学院录取","2018年加入北京大学学生会","2019年创办Bosie服装公司","2022年Bosie公司上市"]]
        npc_jsons = []
        for i in range(6):
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
                "memory_k": 3,
                "language":"C"
            }
        )
        init_pack = INIT_PACK
        # 使用UDP发送初始包到引擎
        print(init_pack)
        self.send_data(init_pack)

    def send_data(self, data, max_packet_size=6000):

            engine_url = "::1"
            engine_port = 8199
            game_url = "::1"
            game_port = 8084

            sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
            # sock.bind(("::1", game_port))

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
                whole_content = header + b"@" + packet

                sock.sendto(whole_content, (engine_url, engine_port))
            sock.close()

    def generate_conversation(self, npc, location, topic, observation, starting, player_desc, length):
        conversation_data = {
            "func": "create_conversation",
            "npc": npc,
            "location": location,
            "topic": topic,
            "observation": observation,
            "starting": starting,
            "player_desc": player_desc,
            "length" : length
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

    #def send_data(self, data):
    #    self.sock.sendto(json.dumps(data).encode(), (self.target_url, self.target_port))
   
game = Game()
game.init_engine()
res = game.generate_conversation(["英华", "泽君"], "花园", "如何向对方表白", "旁白有几棵大树，一条小道，很多的花和草", "", "", "M")
#game.confirm_conversation("8bd7a1bd-3c20-4102-be4f-0426e149d19f", 24)