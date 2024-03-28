def get_npc_response(self, player_name: str, player_speech: str, items_visible: List[str],
                     player_state_desc: str,
                     time: str, fail_safe: "FailSafe", k: int = 3) -> Dict[str, Any]:
    query_text: str = self.purpose + ",".join(self.state.observation.items) + ",".join(
        self.state.observation.people) + ",".join(
        self.state.observation.locations)  # 这里暴力相加，感觉这不会影响提取的记忆相关性[或检索两次？]
    memory_dict: Dict[str, Any] = self.memory.search_memory(query_text=query_text, query_game_time=time, k=k)
    memory_related_text_purpose = [each.text for each in memory_dict["related_memories"]]
    memory_latest_text = [each.text for each in memory_dict["latest_memories"]]
    # 按照玩家的问句检索记忆
    query_text_player: str = player_speech
    memory_dict_player: Dict[str, Any] = self.memory.search_memory(query_text=query_text_player, query_game_time=time,
                                                                   k=k)
    memory_related_text_player = [each.text for each in memory_dict_player["related_memories"]]
    """
        2.按照记忆、之前的目的、当前状态、观察等，生成目的(包含情绪)，动作，回答
    """
    # 根据允许动作的预定义模版设置prompt
    scene_allowed_actions: list[str] = self.scene_knowledge.all_actions
    allowed_actions: list[str] = [action_name for action_name in scene_allowed_actions if
                                  action_name in self.action_space]  # 场景action和人物action取交集
    allowed_actions_dict = {action_name: self.action_dict[action_name] for action_name in allowed_actions}
    action_prompt = ""
    for key, item in allowed_actions_dict.items():
        action_prompt += f"-`{item.example}`：{item.definition}\n"
    # 根据当前位置构造可去的位置(排除当前位置
    scene_allowed_places: list[str] = [place for place in self.scene_knowledge.all_places if
                                       place != self.state.position]
    instruct = f"""
    请你扮演{self.name}，设定是：{self.desc}。
    每当有人与你对话时，你都会以符合角色情绪和背景的方式回应，应包含：1.情绪，2.角色目的，3.角色行为，4.回答内容，采用特定格式：`@[情绪]<角色目的>@<动作|对象|参数>@回答内容@`。
    这个格式方便游戏端进行解析。`<动作|对象|参数>`部分需要限定在以下[行为定义]中：
    {action_prompt}
    你的心情是{self.mood}，现在时间是{time},
    {self.name}当前位置是:{self.state.position}，
    你之前的目的是:{self.purpose},
    你的最近记忆:{memory_latest_text},
    你脑海中相关记忆:{memory_related_text_purpose + memory_related_text_player}，
    你现在看到的人:{self.state.observation.people}，
    你现在看到的物品:{self.state.observation.items}，
    你现在身上的物品:{self.state.backpack}，
    你可去的地方:{scene_allowed_places}，
    你现在看到的地点:{self.state.observation.locations}，
    """
    # 目的(包含情绪)，动作，回答
    prompt = f"""
                {player_name}对你说：“{player_speech}”，
                他的背景：{player_state_desc}，
                他身上有：{items_visible}。
            """
    # 发起请求
    response: str = self.call_llm(instruct=instruct, prompt=prompt)
    """
        3.更新目的和情绪，返回动作和回答组成的数据包
    """
    # 抽取 "目的情绪"、"动作"、"回答" 三个部分
    try:
        [mood_purpose, action_prompt, answer_prompt] = response.strip("@").split("@")
        # 格式化回答，去掉两边的引号
        answer_prompt = answer_prompt.strip('"').strip("“").strip("”")
    except ValueError:
        self.logger.error(f"NPC:{self.name}的回复格式不正确，回复为:{response}")
    except Exception as e:
        mood_purpose = "[正常]<>"
        action_prompt = "<||>"
        answer_prompt = [x for x in response.strip("@").split("@") if x][-1]
        self.logger.error(
            f"NPC:{self.name}的回复格式不正确，回复为:{response}, 返回默认 mood_purpose:{mood_purpose} action_prompt:{action_prompt} answer_prompt:{answer_prompt}")

    # 检查抽取到的动作
    self.action_result: Dict[str, Any] = ActionItem.str2json(action_prompt)
    # 检查action合法性，如不合法那就返回空动作
    action_name = self.action_result["action"]
    # 如果没有找到匹配的action那么就在NPC的动作空间中搜索
    if action_name not in self.action_dict.keys():
        # failSafe
        fail_safe_action: "ActionItem" = fail_safe.action_fail_safe(action_name, list(self.action_dict.values()))
        if not fail_safe_action:
            illegal_action = self.action_result
            self.action_result = {"name": "", "object": "", "parameters": []}
            self.logger.error(
                f"NPC:{self.name}的行为不合法，错误行为为:{illegal_action}, 返回空动作:{self.action_result}")
        else:
            # 如果匹配到了fail_safe_action则替代
            action_name = fail_safe_action

    # 按照配置文件决定是否分割参数
    if action_name in self.action_dict.keys():
        if not self.action_dict[action_name].multi_param:
            # 如果非多参数，比如对话，那就把参数合并成一个字符串
            self.action_result["parameters"] = ",".join(self.action_result["parameters"])
    self.action_result["npc_name"] = self.name
    # 更新NPC的情绪和purpose
    try:
        purpose: str = mood_purpose.split("]<")[1].replace(">", "")
        mood: str = mood_purpose.split("]<")[0].replace("[", "")
    except IndexError:
        self.logger.error(f"返回的目的格式不正确，返回内容为：{mood_purpose}, 设定purpose为''")
        purpose = ""  # NULL
        mood = self.mood
    self.purpose = purpose
    self.mood = mood

    """
        4.添加本次交互的记忆元素
    """
    memory_text = f"""
        {self.name}在{self.state.position}和{player_name}相遇，
        {self.name}的目的是{purpose}，
        {player_name} 的状态是{player_state_desc}，
        {player_name} 说: {player_speech}
        {self.name} 回答{player_name}: {answer_prompt}
        然后 采取了动作: {action_prompt}
        时间在：{time}
    """
    self.memory.add_memory_text(text=memory_text, game_time=time)

    response_package = {
        "name": "talk_result",
        "npc_name": self.name,
        "answer": answer_prompt,
        "actions": [self.action_result]
    }

    self.logger.debug(f"""
                <TALK2NPC请求>
                <请求内容>:{instruct}
                <请求提示>:{prompt}
                <返回内容>:{response}
                <返回行为>:{self.action_result}
                <返回回答>:{answer_prompt}
                <心情和目的>:{self.mood} {self.purpose}
                        """)
    return response_package