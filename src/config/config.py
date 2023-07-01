import json



# KEYS
ZHIPU_KEY = '3fe121b978f1f456cfac1d2a1a9d8c06.iQsBvb1F54iFYfZq'
OPENAI_KEY = "sk-8p38chfjXbbL1RT943B051229a224a8cBdE1B53b5e2c04E2"
OPENAI_BASE = "https://api.ai-yyds.com/v1"

# PACKS
INIT_PACK = json.loads("""
{
        "func":"init",
		 "npc":"{npc_list}",
		 "knowledge":{
			"all_actions": "{all_actions}",
			 "all_places": "{all_places}",
			 "all_moods": "{all_moods}",
			 "all_people": "{all_people}"
				     },
   		"language":"{language}"
}
""")

NPC_CONFIG = json.loads("""
    {
        "name": "{name}",
        "desc": "{desc}",
        "mood": "{mood}",
        "location": "{location}",
        "memory": "{memory}"
    }
""")

CONV_CONFIG = json.loads("""
    {
        "func": "create_conversation",
        "npc": "{npc}",
        "location": "{location}",
        "topic": "{topic}",
        "observations": "{observations}",
        "starting": "{starting}",
        "player_desc": "{player_desc}"
    }
""")


ALL_ACTIONS = ["stay", "move", "chat"]
ALL_PLACES = ["李大爷家", "王大妈家", "广场", "瓜田", "酒吧", "警局"]
ALL_MOODS = ["正常", "焦急", "严肃", "开心", "伤心"]

if __name__ == "__main__":
    #NPC_CONFIG.format(name="李大爷", desc="是个好人", mood="正常", location="李大爷家", memory=[])
    print(INIT_PACK)
    pass