## Action配置总览
Action配置文件在project/config/action/文件夹下，以json格式存储。

Action模块支持开发者通过[配置文件](#action配置例)的方式定义NPC的具体行为。

Action模块和[Scenario配置文件](scenario.md#Scenario配置方法)结合，可以控制NPC在不同场景下的动作空间。

## Action配置例
Action(动作)例子如下:
```python
# project/config/action/get.json
{
  # 动作名字。支持自定义，最好具有代表性。
  "name": "get", 
  # 动作的自然语言约束，用于教LLM调用。需要是<action_name|object|params>这种三元组的形式
  "definition": "<get|object1|object2>，从[object2]中获得[object1]，[object2]可以是人物或者存储器皿；你只可以get'看到的/身上的'物品；", # 
  # 是否期待多参数，也就是三元组中params是多个参数还是一个参数
  "multi_param": True,
  # 动作调用的自然语言例子，用于教LLM调用。需要是<action_name|object|params>这种三元组的形式
  "example": "<get|冰箱|西瓜>或<get|西瓜|冰箱>等",
  # 记忆条目的模板，用于生成记忆条目。有三个内置参量，分别是npc_name, object, parameters。分别代表NPC名字，对象，参数。
  "log_template":{
    "success": "{npc_name}成功地从{object}获得了{parameters}",
    "fail": "{npc_name}试图从{object}里获得{parameters}，但是失败了. 原因是{reason}"
  }
}
```
Action的调用表现取决于配置文件中prompt写的好坏，开发者可以参照例子自行配置。

## 场景下的多个Action配置
只有一个Action肯定是难以满足NPC的复杂行为需求的，因此Action模块支持开发者配置多个Action。
通过配置[scenario配置文件](scenario.md#Scenario配置方法)中的all_actions字段，就可以约束NPC在该场景下的动作空间。
