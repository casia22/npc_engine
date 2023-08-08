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
        }], # 可以留空，默认按照game_world.json+scene初始化场景NPC。非空则在之前基础上添加。
}

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

