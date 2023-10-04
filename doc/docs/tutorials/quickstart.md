## 使用说明

### 引擎的启动、交互、关闭

#### 引擎启动
引擎可以使用对应平台的**运行脚本**(windows下是.bat)或者手动使用**python src/engine.py**运行。

#### 引擎交互

-在引擎端运行前，游戏端可以在默认文件夹中撰写有关“动作”、“角色”以及“场景”的配置文件来为引擎端提供初始化数据（详情请见《配置文档》），配置文件会在引擎端运行期间自主更新。
-在引擎端运行期间，游戏端可以通过UDP数据包传送和接收的方式进行信息交互（）：
 - 引擎端默认在8199端口监听游戏端并发送数据包；游戏端默认在8084端口监听引擎端并发送数据包
 - 引擎启动后，游戏端按照相应功能的数据包格式组织数据并从8084端口发送“请求包”到8199端口（详情请见《UDP数据包》）。
 - 引擎端在接收游戏端的功能请求后，会进行相应信息处理与打包，并从8199端口发送“回复包”到8084端口。
 - 游戏端发送包代码示例（以Unity为例）：
```C#
private void SendData(object data)
{
    string json = JsonUtility.ToJson(data);  // 提取数据data中的字符串信息
    json = $"@1@1@{json}";  // 左添加头信息
    byte[] bytes = Encoding.UTF8.GetBytes(json);  // 对字符串数据编码
    this.sock.Send(bytes, bytes.Length, this.targetUrl, this.targetPort);  // 通过socket向目标端口发送数据包
}
```
 - 游戏端接收数据包并组装的代码示例（以Unity为例）：
```C#
this.listenThread = new Thread(Listen);
this.listenThread.Start();
this.thread_stop = false;

//接收包
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
#### 引擎关闭
游戏端通过发送“close”功能数据包给引擎端来请求关闭引擎（详见下文）。

### 配置文档

#### 配置文件结构
- python_lib(依赖库)
- code(项目代码)
  - npc-engine\
    - logs\(运行日志)
    - src\(源代码)
      - config\(配置文件)
        - action\(场景中允许的动作配置文件)
          - chat.json\(自定义第一个动作的配置文件)
          - ...
        - npc\(npc描述配置文件)
          - 村长.json\(自定义第一个角色的配置文件)
          - ...
        - knowledge\(知识、场景配置文件)
          - scenes\(子场景配置文件)
            - 警察局.json(自定义第一个具体场景的配置文件)
            - ...

#### 配置示例（python）
-\action\chat.json
```python
{
  "name": "chat",   # 动作名称
  "definition": "<chat|person|content>，以扮演的角色身份对[person]说话，内容是[content]",  # 动作格式化模板
  "multi_param": false,  # 是否需要多个输入参数
  "example": "<chat|人名A|早上好！>或<chat|人名B|好久不见，最近你去哪里了>等",  # 根据动作格式化模板写的例子
  "log_template":{ 
    "success": "{npc_name}对{object}说：{parameters}",  # 如果动作执行成功则生成该描述信息
    "fail": "{npc_name}试图与{object}对话，但是失败了. 原因是{reason}"  # 如果动作执行失败则生成该描述信息
  }
}
```
-\npc\村长.json
```python
{
    "name": "村长",  # 角色姓名
    "desc": "村长有着浓密的白色胡须，出生于1940年，喜欢抽中华烟，他白天会在瓜田工作，晚上会在广场上遛弯，如果遇到矛盾他会主持调节，太晚了的时候就会回家睡觉。村长最喜欢吃西瓜。",  # 角色描述，一般包含外貌、出生日期、兴趣爱好、生活习惯等
    "mood": "开心",   # 当前的角色情绪
    "npc_state": {   # 角色当前状态
        "position": "李大爷家",   # 角色所在位置
        "observation": {   # 角色观测到的信息
            "people": [   # 角色观测到的人
                "王大妈",
                "村长",
                "隐形李飞飞"
            ],
            "items": [   # 角色观测到的物体
                "椅子#1",
                "椅子#2",
                "椅子#3[李大爷占用]",
                "床[包括:被子、枕头、床单、床垫、私房钱]"
            ],
            "locations": [   # 角色观测到的地点
                "李大爷家大门",
                "李大爷家后门",
                "李大爷家院子"
            ]
        },
        "backpack": [   # 角色随身携带的物体
            "中华烟[剩余4根]",
            "1000元",
            "吃了一半的西瓜"
        ]
    },
    "memory": [   # 角色的记忆，一般按照时间顺序列举
        "11年前由于对村子做出巨大贡献被村民们推举为新一任村长。",
        "9年前调节某村民婚礼期间发生的纠纷。",
        "7年前管理的村子被评为十佳美丽乡村。"
    ],
    "purpose": "村长想去广场散步，因为他喜欢晚上在广场上遛弯，享受清新的空气和宁静的夜晚。",   # 角色当前的意图，一般指短期意图
    "action": {   # 角色当前执行的动作
        "action": "mov",
        "object": "广场",
        "parameters": "",
        "npc_name": "村长",
        "name": "action"
    }
}
```
-\knowledge\scenes\警察局.json
```python
{
 "all_actions": ["mov", "get", "put", "use"],   # 场景中可支持的动作类型
 "all_places": ["牢房", "雁栖村入口"],   # 场景中的子地点
 "all_moods": ["正常", "焦急", "严肃", "开心", "伤心"],    #场景中可支持的情绪，一般情况下所有场景的情绪信息是一致的
 "all_people": ["囚犯阿呆","警员1","警员2"]   # 场景中的存在的角色名称
 }

```

### UDP数据包

#### 数据包格式记录
https://aimakers.atlassian.net/wiki/spaces/npcengine/pages/3735735/NPC

#### 引擎初始化和关闭：
在引擎初始化或者加载一个新场景的时候发送init数据包给引擎端，需要指定加载的场景json
```python
# 引擎初始化的包
{
    "func":"init",   # 表示该传送的数据包是用于加载场景
    # 必填字段
    "scene_name":"雁栖村",   # 加载场景的名称，代表在什么场景下初始化
    "language":"C",   # 选择语言版本，“E”表示英文，“C”表示中文。默认且推荐使用中文。
    # 🉑️选字段
    "npc":[
        {
            "name":"李大爷",
            "desc":"是个好人",
            "npc_state": {
                  "position": "李大爷家",
                  "observation": {
                          "people": ["王大妈", "村长", "隐形李飞飞"],
                          "items": ["椅子#1","椅子#2","椅子#3[李大爷占用]","床"],
                          "locations": ["李大爷家大门","李大爷家后门","李大爷家院子"]
                                },
                  "backpack":["黄瓜", "1000元", "老报纸"]
                       },
            "mood":"正常",
            "memory":[ ]
        },
        {
            "name":"王大妈",
            "desc":"是个好人",
            "npc_state": {
                  "position": "李大爷家",
                  "observation": {
                          "people": ["李大爷", "村长", "隐形李飞飞"],
                          "items": ["椅子#1","椅子#2","椅子#3[李大爷占用]","床"],
                          "locations": ["李大爷家大门","李大爷家后门","李大爷家院子"]
                                },
                  "backpack":["优质西瓜", "大砍刀", "黄金首饰"]
                       },
        "mood":"焦急",
        "memory":[ ]
        }], # 可以留空，默认按照gscene.json初始化场景NPC。非空则在之前基础上添加。
}
# 引擎关闭的包
{
    "func":"close" # 关闭引擎,并保存所有NPC到json
}
```

#### NPC自主行为:
NPC不会开始自主行动，除非你发送了wakeup包给它。
npc-engine接到wakeup包之后，会返回action行为。
游戏这边需要执行对应action，执行最终状态以action_done的形式返回给npc-engine
engine接收到action_done包之后会继续返回action行为包。

```python
# wakeup包例：
{
    "func":"wake_up",
    "npc_name": "王大妈",
  
    "scenario_name": "李大爷家", 
    "npc_state": {
      "position": "李大爷家卧室",
      "observation": {
              "people": ["李大爷", "村长", "李飞飞"],
              "items": ["椅子#1","椅子#2","椅子#3[李大爷占用]","床"],
              "locations": ["李大爷家大门","李大爷家后门","李大爷家院子"]
                    },
      "backpack":["优质西瓜", "大砍刀", "黄金首饰"]
    },

    "time": "2021-01-01 12:00:00", # 游戏世界的时间戳 
}

# action_done包例
{
    "func":"action_done",
    "npc_name":"王大妈",
    "status": "success",
    "time": "2021-01-01 12:00:00", # 游戏世界的时间戳
  
    "scenario_name": "李大爷家", 
    "npc_state": {
      "position": "李大爷家卧室",
      "observation": {
              "people": ["李大爷", "村长", "李飞飞"],
              "items": ["椅子#1","椅子#2","椅子#3[李大爷占用]","床"],
              "locations": ["李大爷家大门","李大爷家后门","李大爷家院子"]
                    },
      "backpack":["优质西瓜", "大砍刀", "黄金首饰"]
    },

    "action":"mov",
    "object":"李大爷家",  # 之前传过来的动作对象
    "parameters":[], # 之前传过来的参数
    "reason": "", # "王大妈在去往‘警察局’的路上被李大爷打断"
}
        
# action_done、wakeup发给游戏包后返回的ACTION包
{
    "name":"action",
    "npc_name":"李大妈",
    "action":"mov",
    "object":"李大爷家",
    "parameters":[],
}
```

#### 对话相关行为：
游戏需要自己确认npc的群体对话触发机制，通常是一个包含固定半径的对话房间。
发送create_conversation给engine后，engine会根据提供的参数返回一个长剧本包，游戏需要自己实现剧本演出。
每一行剧本演出完成后，需要发送确认包给engine否则不会有记忆。

剧本有插入功能，比如玩家要插入对话或者一个新的npc进入了对话，这时候发送re_create_conversation包便可，会重新生成一个考虑到插入npc的接续剧本。

```python
# create_conversation游戏端发给引擎的包
{
    "func": "create_conversation",
    "npc": ["王大妈","李大爷"],   # npc列表

    "scenario_name": "李大爷家",        
    "location": "李大爷家卧室",
    "topic": "王大妈想要切了自己的西瓜给李大爷吃，并收钱", # 可以留空，会自动生成topic
    "npc_states": [   # 该列表中的每个状态对应于npc列表的相应角色名称
                {
                  "position": "李大爷家",
                  "observation": {
                          "people": ["李大爷", "村长", "隐形李飞飞"],
                          "items": ["椅子#1","椅子#2","椅子#3[李大爷占用]","床"],
                          "locations": ["李大爷家大门","李大爷家后门","李大爷家院子"]
                                },
                  "backpack":["优质西瓜", "大砍刀", "黄金首饰"]
                },
                {
                  "position": "李大爷家",
                  "observation": {
                          "people": ["王大妈", "村长", "隐形李飞飞"],
                          "items": ["椅子#1","椅子#2","椅子#3[李大爷占用]","床"],
                          "locations": ["李大爷家大门","李大爷家后门","李大爷家院子"]
                                },
                  "backpack":["黄瓜", "1000元", "老报纸"]
                },
                ],
    "starting": "你好，嫩们在干啥腻？",  # 玩家说的话，可选留空
    "player_desc": "玩家是一个疯狂的冒险者，喜欢吃圆圆的东西",  # 玩家的描述，可选留空
    "memory_k": 3,  # npc的记忆检索条数，必须填写
    "length": "M"  # 可以选择的剧本长度，S M L X 可选。 
}

# 引擎端创造并生成剧本后传给游戏端的数据包
{
    "name": "conversation",
    "id": "123456789",  # conversation对象的索引号
    "length": "M",  # 可以选择的剧本长度，S M L X 可选。 
    "location": "李大爷家",  # 对话发生所在的地点
    "lines": [line1, line2, line3, line4, ...]  # 剧本信息，由若干行对话组成的序列
}

# 引擎端生成剧本的每一行的格式
{
    "type": "Interaction",  # 剧本行的类型，可以是State，Interaction，Error
    "state": "李大爷退出。剩下的角色：王大妈",  # 当剧本行类型是State和Error时，"state"才会有具体内容
    "name": "李大爷",  # 剧本行对应的角色姓名，当剧本行类型是Interaction时才不为空
    "mood": "开心",  # 剧本行对应角色的情绪，当剧本行类型是Interaction时才不为空
    "words": "我喜好吃西瓜",  # 剧本行对应角色的说话内容，当剧本行类型是Interaction时才不为空
    "action": {
              "type": "对话",
              "args": "王大妈"}  # 剧本行对应角色的动作，当剧本行类型是Interaction时不为空
}

# 游戏端传给引擎端的剧本演示确认包
{
    "func": "confirm_conversation_line",
    "conversation_id": "123456789",  # conversation对象的索引号
    "index": 2,  # 游戏端展示完成的剧本行索引号
}

# re_create_conversation游戏端发给引擎的包
{
    "func": "re_create_conversation",
    "id": "123456789",  # conversation对象的索引号
    "character": "警长",  # 新加入角色的名称
    "interruption": "大家好呀，你们刚刚在说什么",  # 玩家插入的说话内容
    "player_desc": "玩家是一个疯狂的冒险者，喜欢吃圆圆的东西",  # 玩家的描述，可选留空
    "length": "M"  # 可以选择的剧本长度，S M L X 可选。 
}

```
### 引擎交互注意事项

- 游戏端发送init包后，引擎端会读取数据包中场景名称所对应的配置文件scene_name.json，然后初始化场景。
- 如果init数据包中包含npc信息，那么引擎端会默认从该数据包中读入角色信息；如果不包含，则引擎端会从scene_name.json配置文件中读入角色信息。
- 每个场景配置文件scene_name.json中的可支持动作和存在的角色名称都需要在\action和\npc中进行定义，如果未定义则会报错。
- 每个npc在游戏中的自主行动需要游戏端对针对该角色向引擎端发送wakeup包来实现的。
 - 长时间没有自主行为的npc需要游戏端自行检测，发送wakeup包到引擎进行再次唤醒
 - 引擎端接收wakeup包后会生成npc的动作并返回action包给游戏端
 - 游戏端执行对应的action包之后，需要发送action_done包到引擎，这样引擎才会继续生成npc下一步行为。

## 测试方式

### 测试数据
测试数据统一放在test/test_packets.py中，可以自己添加测试数据。

### NPC_ACTION测试参考代码:
1.test_npc_action.py
运行这个脚本然后查看logs/下的日志
2.test_npc_action.ipynb
运行CELL然后查看logs/下的日志，可以自定义自己的包。
上面的代码仅供参考，可以自己写一个脚本来测试。
在npc_engine父目录中import npc_engine 然后 engine = NPCEngine() 就可以启动。


## 版本发布

### 打包方式

项目使用pyarmor加密，然后在windows中使用嵌入式的python执行engine.py。

打包脚本为npc_engine/dist/release_windows.sh

打包后可运行的windows项目在npc_engine/dist/release/windows_ver，其中脚本start_engine.bat用来启动engine







