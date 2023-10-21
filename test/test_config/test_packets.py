"""
存储用于开环测试的数据包
测试脚本统一从这个脚本导入测试数据包
"""

init_packet = {
    "func": "init",
    # 必填字段，代表在什么场景初始化
    "scene_name": "雁栖村",
    "language": "C",
    # 下面是🉑️选
    "npc": [
        {
            "name": "渔夫阿强",
            "desc": "渔夫阿强是一个老练的渔民，擅长捕鱼和航海。他有一头浓密的白发和一双狡猾的眼睛。阿强经验丰富，对海洋和天气变化有着敏锐的观察力。",
            "mood": "满足",
            "npc_state": {
                "position": "河边钓鱼点",
                "observation": {
                    "people": [],
                    "items": ["船舱", "渔网", "渔具", "航海地图", "渔获"],
                    "locations": ["船舱内部", "甲板"]
                },
                "backpack": ["鱼饵", "渔具维修工具"]
            },
            "action_space": ["mov", "chat"],
            "memory": [
                "从小就跟随父亲学习捕鱼技巧。",
                "曾多次出海捕鱼，积累丰富的经验。",
                "对海洋生态保护有着浓厚的兴趣。",
                "帮助其他渔民修理损坏的渔具。",
                "梦想拥有一艘自己的渔船，开展独立的渔业。"
            ]
        },
        {
            "name": "猎人阿明",
            "desc": "猎人阿明是一位勇敢而机敏的猎人。他身材魁梧，肌肉发达，眼神犀利。阿明擅长追踪和狩猎各种野生动物，具有过人的耐力和狙击技巧。",
            "mood": "专注",
            "npc_state": {
                "position": "猎人小屋",
                "observation": {
                    "people": [],
                    "items": ["猎枪", "弓箭", "追踪装备", "野外求生工具"],
                    "locations": ["猎人小屋内部", "周围的森林"]
                },
                "backpack": ["干粮", "水壶", "急救包"]
            },
            "action_space": ["mov", "chat"],
            "memory": [
                "从小生活在山区，接受父亲的猎人训练。",
                "熟悉各种野生动物的习性和行踪。",
                "常常在附近的森林中追踪并捕获猎物。",
                "有着长时间在野外生存的经验。",
                "一日作息：清晨起床后进行锻炼和瞄准训练，白天进行狩猎和追踪，傍晚返回小屋整理装备并准备晚餐，晚上休息并回顾一天的狩猎经历。"
            ]
        }
    ],  # 可以留空，默认按照scene.json初始化场景NPC。非空则在之前基础上添加。
}

init_packet_police = {
    "func": "init",
    # 必填字段，代表在什么场景初始化
    "scene_name": "警察局",
    "language": "C",
    "npc": []
}

wakeup_packet_1 = {
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

wakeup_packet_2 = {
    "func": "wake_up",
    "npc_name": "李大爷",

    "scenario_name": "李大爷家",
    "npc_state": {
        "position": "李大爷家卧室",
        "observation": {
            "people": ["王大妈", "村长", "隐形李飞飞"],
            "items": ["椅子#1", "椅子#2", "椅子#3[李大爷占用]", "床[包括:被子、枕头、床单、床垫、私房钱]"],
            "locations": ["李大爷家大门", "李大爷家后门", "李大爷家院子"]
        },
        "backpack": ["黄瓜", "1000元", "老报纸"]
    },
    "time": "2021-01-01 12:00:00",  # 游戏世界的时间戳
}

wakeup_packet_3 = {
    "func": "wake_up",
    "npc_name": "村长",

    "scenario_name": "李大爷家",
    "npc_state": {
        "position": "李大爷家卧室",
        "observation": {
            "people": ["王大妈", "村长", "隐形李飞飞"],
            "items": ["椅子#1", "椅子#2", "椅子#3[李大爷占用]", "床[包括:被子、枕头、床单、床垫、私房钱]"],
            "locations": ["李大爷家大门", "李大爷家后门", "李大爷家院子"]
        },
        "backpack": ["中华烟[剩余4根]", "1000元", "吃了一半的西瓜"]
    },
    "time": "2021-01-01 12:00:00",  # 游戏世界的时间戳
}

action_done_packet_1 = {
    "func": "action_done",
    "npc_name": "王大妈",
    "status": "success",
    "time": "2021-01-01 12:00:00",  # 游戏世界的时间戳

    "scenario_name": "李大爷家",
    "npc_state": {
        "position": "李大爷家卧室",
        "observation": {
            "people": ["李大爷", "村长", "李飞飞"],
            "items": ["椅子#1", "椅子#2", "椅子#3[李大爷占用]", "床"],
            "locations": ["李大爷家大门", "李大爷家后门", "李大爷家院子"]
        },
        "backpack": ["优质西瓜", "大砍刀", "黄金首饰"]
    },

    "action": "mov",
    "object": "李大爷家",  # 之前传过来的动作对象
    "parameters": [],  # 之前传过来的参数
    "reason": "",  # "王大妈在去往‘警察局’的路上被李大爷打断"
}

action_done_packet_2 = {
    "func": "action_done",
    "npc_name": "李大爷",
    "status": "fail",
    "time": "2021-01-01 12:00:00",  # 游戏世界的时间戳

    "scenario_name": "李大爷家",
    "npc_state": {
        "position": "李大爷家卧室",
        "observation": {
            "people": ["王大妈", "村长", "李飞飞"],
            "items": ["椅子#1", "椅子#2", "椅子#3[李大爷占用]", "床"],
            "locations": ["李大爷家大门", "李大爷家后门", "李大爷家院子"]
        },
        "backpack": ["优质西瓜", "大砍刀", "黄金首饰"]
    },

    "action": "mov",
    "object": "警察局",  # 之前传过来的动作对象
    "parameters": [],  # 之前传过来的参数
    "reason": "李大爷在去往‘警察局’的路上被王大妈打断",  # "王大妈在去往‘警察局’的路上被李大爷打断"
}

# player2npc的对话包
player2npc_packet = {
    "func":"talk2npc",
    "npc_name":"警员1",
    "time": "2021-01-01 12:00:00", # 游戏世界的时间戳

    # NPC的状态
    "scenario_name": "警察局",
    "npc_state": {
      "position": "雁栖村入口",
      "observation": {
              "people": ["囚犯阿呆","警员2","旅行者小王"],
              "items": ["椅子#1","椅子#2","椅子#3[李大爷占用]","床"],
              "locations": ['牢房', '雁栖村入口']
                    },
      "backpack":["优质西瓜", "大砍刀", "黄金首饰"]
    },
    # player的信息
    "player_name":"旅行者小王",  # player的名字
    "speech_content":"你好，我是旅行者小王, 我要报警, 在林区中好像有人偷砍树",  # player说的话
    "items_visible": ["金丝眼镜", "旅行签证", "望远镜"],  # player身上的物品
    "state": "旅行者小王正在严肃地站着，衣冠规整，手扶着金丝眼镜",  # player状态的自然语言描述，开发者可以随意添加
}


close_packet = {
    "func": "close"
}