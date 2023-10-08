## 📜 快速开始
你可点击发行版本中的.bat文件来快速启动引擎，相关响应会在控制台中显示。
## 1.1 下载引擎
访问我们的[github仓库](https://github.com/casia22/npc-engine)下载最新的引擎代码，或者直接点击[这里](https://github.com/casia22/npc-engine/releases).

## 1.2 启动引擎
每个发行版本中都会有对应平台的快速调试脚本(start_engine.bat), 双击即可启动引擎。执行过程的日志和收发包都会记录在logs文件夹下。
## 1.3 脚本交互(python)
引擎监听8084端口，游戏端监听8199端口，引擎端和游戏端通过UDP数据包进行交互。

可以参照下面的python脚本👇来快速测试引擎的功能。

(由于UDP的包机制，我们通过一些trick来实现了大数据包的传输，具体的实现细节可以参考[这里](#udp数据包))
```python
import socket
import json
import uuid
import time
import threading

"""
    该脚本用于测试引擎的功能，包括：
    1. 发送数据包到引擎8199端口(Game -> Engine)
    2. 在8084监听回传给游戏的数据包(Game <- Engine)
"""


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


```

## 📜 UDP数据包收发
Engine目前发送的响应UDP包是会动态扩增的，如果响应超过了最大包限制，那么Engine就会拆分发送。

收发包的统一结构为:
```python
  # {msg_id}@{i + 1}@{total_packets}@{json_data}
  # 例(引擎响应包)： 4bfe6122618b41fa85c8a8eb3ab37993@1@1@{"name": "action", "action": "chat", "object": "李大爷", "parameters": "李大爷,您知道匈房在哪里吗？", "npc_name": "王大姐"}
```
## 2.1 收发包(python)
```python
import uuid, json, socket

def send_data(data, max_packet_size=6000):
        engine_url = "::1"
        engine_port = 8199
        game_url = "::1"
        game_port = 8084
        sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        sock.bind((game_url, game_port))

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

# 准备数据包
init_packet = {
    "func": "init",
    # 必填字段，代表在什么场景初始化
    "scene_name": "雁栖村",
    "language": "C",
    # 下面是🉑️选
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
    "time": "2021-01-01 12:00:00",  # 游戏世界的时间戳
}
# 发送数据包(发送后观察日志或终端)
send_data(init_packet)
send_data(wakeup_packet)
```
## 2.2 收发包(C#)
在Unity中也是需要对数据包进行处理才可以进行发送的，下面是一个简单的Unity脚本，可以参考一下。

```c#
// 发送UDP包的逻辑
private void SendData(object data)
{
    string json = JsonUtility.ToJson(data);  // 提取数据data中的字符串信息
    json = $"@1@1@{json}";  // 左添加头信息
    byte[] bytes = Encoding.UTF8.GetBytes(json);  // 对字符串数据编码
    this.sock.Send(bytes, bytes.Length, this.targetUrl, this.targetPort);  // 通过socket向目标端口发送数据包
}

this.listenThread = new Thread(Listen);
this.listenThread.Start();
this.thread_stop = false;

//接收UDP包的逻辑(UDP包拼接为完整包)
public void Listen()
{
    IPEndPoint localEndPoint = new IPEndPoint(IPAddress.IPv6Loopback, this.listenPort);
    this.sock.Client.Bind(localEndPoint);

    string receivedData = "";  # 初始化receivedData用于整合接收到的字符串
    while (!this.thread_stop)   // 持续监听引擎端发送的数据包
    {
        byte[] data = this.sock.Receive(ref localEndPoint);   // 接收到数据包
        string packet = Encoding.UTF8.GetString(data); // 将接收到的数据包转化为字符串
        string[] parts = packet.Split('@');  // 将字符串按照@字符进行分段并得到片段序列
        string lastPart = parts[parts.Length - 1];  // 片段序列中的最后一段对应引擎端要传送的具体内容
        receivedData+=lastPart;  // 将内容拼接到ReceivedData后面
        if (receivedData.EndsWith("}")) //多包机制下，此为收到最后一个包
        {
            //接下来对整合好的ReceivedData做下列分支判断和后处理
            if (receivedData.Contains("\"inited")) // 如果有inited字段
            {
                num_initialized += 1;
                UnityEngine.Debug.Log($"Successful initialization. {num_initialized}");

            }else if (receivedData.Contains("\"conversation")) // 如果有conversation字段
            {
                ReceiveConvFormat json_data = JsonUtility.FromJson<ReceiveConvFormat>(receivedData);
                UnityEngine.Debug.Log($"Get Conversation.{JsonUtility.ToJson(json_data)}");
                receivedConvs.Add(json_data); flag_ConvReceived = true;

            }else if (receivedData.Contains("\"action"))  // 如果有action字段
            {
                FullActionFormat json_data = JsonUtility.FromJson<FullActionFormat>(receivedData);
                UnityEngine.Debug.Log($"Get Action. {JsonUtility.ToJson(json_data)}");
                receivedActions.Add(json_data); flag_ActReceived = true;
            }
            receivedData = ""; //收到最后一个包，重置收到的内容
        }
    }
}
```
