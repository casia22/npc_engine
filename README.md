# 🎮 NPC-Engine 🚀

NPC-Engine 是一个由 CogniMatrix™️ 提供的游戏AI引擎，它赋予游戏AI以群体智能。

![Author Badge](https://img.shields.io/badge/author-CogniMatrix-blue)
![Pylint Badge](./material/badges/pylint.svg)
![Pytest Badge](./material/badges/pytest.svg)

## 📦 安装

安装方式将在稍后提供。

## 📅 项目时间表

以下是我们的项目开发时间表：

1. 工程化代码[✅]
2. 完成测试用例[WIP]
3. NPC决策[✅]
4. 添加单人对话[❌]
5. 完善文档[WIP]

请继续关注我们的项目，以获取最新的进展和更新！

## 文档

### 数据包格式记录
https://aimakers.atlassian.net/wiki/spaces/npcengine/pages/3735735/NPC
#### 引擎初始化：
在游戏场景初始化加载的时候发送给engine，需要指定加载的场景json
```python
{
    "func":"init",
    # 必填字段，代表在什么场景初始化
    "scene":"default_village",
    "language":"E" or "C",
    # 下面是🉑️选
    "npc":[
        {
            "name":"李大爷",
            "desc":"是个好人",
            "mood":"正常",
            "location":"李大爷家",
            "memory":[ ]
        },
        {"name":"王大妈",
        "desc":"是个好人",
        "mood":"焦急",
        "location":"王大妈家",
        "memory":[ ]
        }], # 可以留空，默认按照game_world.json+scene.json初始化场景NPC。非空则在之前基础上添加。
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
    "position": "李大爷家",
    "observation": ["李大爷", "椅子#1","椅子#2","椅子#3[李大爷占用]","床"]
    "time": "2021-01-01 12:00:00", # 游戏世界的时间戳 
}

# action_done包
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
    "npc": "{npc}",
    "location": "{location}",
    "topic": "{topic}",
    "observations": "{observations}",
    "starting": "{starting}",
    "player_desc": "{player_desc}",
    "memory_k": "{memory_k}",
    "length": "{length}"
}

# 引擎端创造并生成剧本后传给游戏端的数据包
{
    "name": "conversation",
    "id": "{id}",
    "length": "{length}",
    "location": "{location}",
    "lines": "{lines}"
}

# 引擎端生成剧本的每一行的格式
{
    "type": "{type}",
    "state": "{state}",
    "name": "{name}",
    "mood": "{mood}",
    "words": "{words}",
    "action": "{action}"
}

# 游戏端传给引擎端的剧本演示确认包
{
    "func": "confirm_conversation_line",
    "conversation_id": "{id}",
    "index": "{index}"
}

# re_create_conversation游戏端发给引擎的包
{
    "func": "re_create_conversation",
    "id": "{id}",
    "character": "{character}",
    "interruption": "{interruption}",
    "player_desc": "{player_desc}",
    "length": "{length}"
}

```

## 测试方式

### NPC_ACTION测试
1.test_npc_action.py
运行这个脚本然后查看logs/下的日志
2.test_npc_action.ipynb
运行CELL然后查看logs/下的日志，可以自定义自己的包。

