## Scenario配置总览
场景配置文件在nuwa/src/config/knowledge/scenes/文件夹下，以json格式存储。

Scenario规范了子场景中的路点，动作空间，情绪空间等。更重要的是决定了哪些NPC会在该场景下被加载到内存中。

场景.json通过init包初始化，决定初始化哪些NPC和这些NPC的动作空间。

Scenario文件是NPC Engine的核心配置文件，它组织了NPC、Action和Knowledge的关系。

## Scenario配置方法
Scenario(场景)例子如下:
```python
# nuwa/src/config/knowledge/scenes/警察局.json
{
 "all_actions": ["mov", "get", "put", "use"], # 场景中可支持的Action类型
 "all_places": ["牢房", "雁栖村入口"], # 场景中的子地点(用于NPC移动的参数，可视作场景子地点)
 "all_moods": ["正常", "焦急", "严肃", "开心", "伤心"], # 场景中可支持的情绪，一般情况下所有场景的情绪信息是一致的
 "all_people": ["囚犯阿呆","警员1","警员2"] # 场景中的存在的NPC，会在[场景初始化]时加载到内存中
 }
```

## 配置文件初始化
Scenario配置文件在nuwa/src/config/knowledge/scenes/文件夹下配置完成后，则会在引擎启动的时候被加载到内存中。

当游戏切入到一个场景的时候，需发送一个init包到引擎端，引擎会根据你发送的场景名字来加载对应的场景配置文件中的NPC。

一个初始化场景的例子如下:
```python
# nuwa/src/config/knowledge/scenes/警察局.json
{
 "func": "init", # 初始化场景
 "scene_name": "警察局", # 场景名字,会去加载对应的场景配置文件.json
 "language": "C", # 语言
 "npc": [] # 场景中的存在的NPC，会在[场景初始化]时加载到内存中
 }
```

