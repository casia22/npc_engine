
### game_world.json
```
{
 "all_actions": ["mov", "get", "put"],
 "all_places": ["李大爷家", "王大妈家", "广场", "瓜田", "酒吧", "警局"],
 "all_moods": ["正常", "焦急", "严肃", "开心", "伤心"],
 "all_people": ["李大爷","王大妈","村长","警长"]
 }
```
"all_actions"： 游戏中会被读取的所有动作json，如mov, get, put等。
                初始化时会被加载到内存中。
                读取路径: npc_engine/src/config/action/xxx.json

"all_places"： 游戏中涉及到的所有地点，目前仅仅是字符串

"all_moods"： 游戏中涉及到的所有心情，目前仅仅是字符串

"all_people"： 游戏中涉及到的所有人物json，如李大爷，王大妈等。
                初始化时会被加载到内存中。
                读取路径: npc_engine/src/config/npc/xxx.json

引擎初始化的时候会默认读取gameworld.json,然后按照配置文件去初始化游戏世界。
init包中的内容也会被初始化。两者是叠加的关系。


