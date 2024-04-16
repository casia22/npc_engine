import json
import logging
import socket
from pathlib import Path
from typing import List, Dict, Any, Tuple

from nuwa.src.npc.memory import NPCMemory
from nuwa.src.npc.knowledge import PublicKnowledge, SceneConfig
from nuwa.src.npc.action import ActionItem
from nuwa.src.npc.talk_box import TalkBox
from nuwa.src.utils.embedding import LocalEmbedding, SingletonEmbeddingModel, BaseEmbeddingModel
from nuwa.src.utils.model_api import get_model_answer


# npc的宽泛知识
class PersonalKnowledge:
    """
    本质只是存储当前的个体的认知记忆，和public区分开
    """

    def __init__(self, actions: List[str], places: List[str], people: List[str], moods: List[str]):
        self.actions = actions
        self.places = places
        self.people = people
        self.moods = moods


# npc的状态
class State:
    """
    游戏提供给NPC的状态
    """

    def __init__(self, position: str, backpack: List[str], ob_people: List[str], ob_items: List[str],
                 ob_locations: List[str]):
        self.position = position
        self.backpack = backpack
        self.observation = self.Observation(ob_people, ob_items, ob_locations)

    class Observation:
        def __init__(self, people: List[str], items: List[str], locations: List[str]):
            self.people = people
            self.items = items
            self.locations = locations

        def __str__(self):
            return f'{{\n\t\t"people": {self.people},\n\t\t"items": {self.items},\n\t\t"locations": {self.locations}\n\t}}'

        def to_dict(self):
            return {
                "people": self.people,
                "items": self.items,
                "locations": self.locations
            }

    def __str__(self):
        return f'{{\n\t"position": "{self.position}",\n\t"observation": {{\n\t\t"people": {self.observation.people},\n\t\t"items": {self.observation.items},\n\t\t"locations": {self.observation.locations}\n\t}},\n\t"backpack": {self.backpack}\n}}'

    def to_dict(self):
        return {
            "position": self.position,
            "observation": {
                "people": self.observation.people,
                "items": self.observation.items,
                "locations": self.observation.locations
            },
            "backpack": self.backpack
        }


# NPC类
class NPC:
    """
    NPC类，用于存储NPC的信息，生成行为ACTION和目的PURPOSE
    初始化所需的参数Args:
        name (str): NPC的名称
        desc (str): NPC的描述
        knowledge (Dict[str, Any]): NPC的常识，包括动作、地点、人物和情绪
        state (Dict[str, Any]): NPC的状态，包括位置、背包、观察到的人物、物品和地点
        mood (str, optional): NPC的心情，默认为"正常"
        memory (List[str], optional): NPC的记忆列表，默认为空列表
        memory_k (int, optional): NPC记忆的长度，默认为3
        model (str, optional): 使用的语言模型，默认为OPENAI_MODEL
    """

    def __init__(
            self,
            name: str,
            name_index: int,
            desc: str,
            public_knowledge: PublicKnowledge,
            scenario_name: str,
            state: Dict[str, Any],
            action_dict: Dict[str, ActionItem],
            embedding_model: BaseEmbeddingModel,
            project_root_path: Path,
            model: str = "gpt-3.5-turbo-16k",
            mood: str = "正常",
            action_space: List[str] = [],
            memory: List[str] = [],
            memory_k: int = 3,
    ) -> None:
        # NPC模块LOGGER
        self.logger = logging.getLogger("NPC")
        # 用户项目根目录设置
        self.PROJECT_ROOT_PATH = project_root_path
        self.CONFIG_PATH = self.PROJECT_ROOT_PATH / "config"
        # model
        self.ACTION_MODEL: str = model
        # NPC固定参数
        self.name: str = name
        self.name_index: int = name_index
        self.desc: str = desc
        self.action_space: List[str] = action_space
        # NPC的常识
        self.public_knowledge = public_knowledge
        ## note:场景常识由scenario_name初始化决定；如果更新，使用set_scenario更新
        self.scene_knowledge: SceneConfig = public_knowledge.get_scene(scene_name=scenario_name)
        # NPC的状态
        self.state = State(
            position=state['position'],
            backpack=state['backpack'],
            ob_people=state['ob_people'],
            ob_items=state['ob_items'],
            ob_locations=state['ob_locations']
        )
        self.scenario = scenario_name
        # 为了和engine的action_dict保持一致，把输出的action结果改成了action_result
        self.action_dict = action_dict
        self.action_result = {}
        self.mood: str = mood
        self.purpose: str = ""
        # NPC的记忆
        self.embedding_model = embedding_model
        self.memory: NPCMemory = NPCMemory(npc_name=self.name, name_index=self.name_index, k=memory_k,
                                           EmbeddingModel=self.embedding_model,
                                           project_root_path=self.PROJECT_ROOT_PATH)

        ####################### 先清空现有VB #######################
        self.memory.clear_memory()
        self.initial_memory = memory
        ################# 等到记忆添加实现闭环时删除 #################
        # 实现多轮对话
        self.talk_box = None

    def _init(self):
        for piece in self.initial_memory:
            self.memory.add_memory_text(piece, game_time="XXXXXXXXXXXXXXXX")
            self.logger.debug(f"add memory {piece} into npc {self.name} done.")

    def set_state(self, state: Dict[str, Any]) -> None:
        self.state = State(
            position=state['position'],
            backpack=state['backpack'],
            ob_people=state['observation']['people'],
            ob_items=state['observation']['items'],
            ob_locations=state['observation']['locations']
        )

    def set_backpack(self, backpack: List[str]) -> None:
        self.state.backpack = backpack

    def set_observation(self, observation: Dict[str, Any]) -> None:
        self.state.observation = State.Observation(
            people=observation['people'],
            items=observation["items"],
            locations=observation["locations"]
        )

    def set_known_actions(self, actions: List[str]) -> None:
        self.scene_knowledge.all_actions = actions

    def set_action_dict(self, action_dict):
        self.action_dict = action_dict

    def set_location(self, location: str) -> None:
        self.state.position = location

    def set_scenario(self, scenario: str) -> None:
        """
        更新场景属性，更新场景knowledge
        :param scenario:
        :return:
        """
        self.scenario = scenario
        self.scene_knowledge = self.public_knowledge.get_scene(scene_name=scenario)
        self.logger.debug(f"NPC:{self.name} 已经切换到了 {self.scenario} 场景")

    def set_mood(self, mood: str) -> None:
        self.mood = mood

    def get_purpose(self, time: str, k: int = 3) -> str:
        """
        根据位置和时间+NPC记忆获取NPC的目的
        如果没有目的，那就参照最近记忆生成一个目的
        如果有了目的，那就以当前记忆检索重新生成一个目的
        :param time: str
        :param k: int
        :return: str
        """
        # 根据当前位置构造可去的位置(排除当前位置
        scene_allowed_places: list[str] = [place for place in self.scene_knowledge.all_places if
                                           place != self.state.position]
        if not self.purpose:
            # 如果没有目的，那就参照最近记忆
            role_play_instruct = f"""
            请你扮演{self.name}，特性是：{self.desc}，
            可有的心情是{self.scene_knowledge.all_moods}，
            当前心情是{self.mood}，现在时间是{time},
            {self.name}当前位置是:{self.state.position}，
            最近记忆:{[item.text for item in list(self.memory.latest_k.queue)]},
            {self.name}现在看到的人:{self.state.observation.people}，
            {self.name}现在看到的物品:{self.state.observation.items}，
            {self.name}现在身上的物品:{self.state.backpack}，
            {self.name}可去的地方:{scene_allowed_places}，
            {self.name}现在看到的地点:{self.state.observation.locations}，            
            """
            prompt = f"""
            请你为{self.name}生成一个目的，以下是例子：
            例1：[{self.scene_knowledge.all_moods[0]}]<{self.name}想去XXX，因为{self.name}想和XX聊聊天，关于{self.name}XXX>
            例2：[{self.scene_knowledge.all_moods[1]}]<{self.name}想买一条趁手的扳手，这样就可以修理{self.name}家中损坏的椅子。>
            例3：[{self.scene_knowledge.all_moods[1]}]<{self.name}想去XXX的家，因为{self.name}想跟XXX搞好关系。>
            要求：
            1.按照[情绪]<目的>的方式来返回内容
            2.尽量使用第三人称来描述
            3.如果目的达成了一部分，那就去除完成的部分并继续规划
            4.目的要在20字以内。
            5.目的要从最近记忆中出发。
            """
        else:
            # 如果有目的，那就使用目的来检索最近记忆和相关记忆
            memory_dict: Dict[str, Any] = self.memory.search_memory(query_text=self.purpose, query_game_time=time, k=k)
            memory_latest_text = [each.text for each in memory_dict["latest_memories"]]
            memory_related_text = [each.text for each in memory_dict["related_memories"]]

            # 结合最近记忆和相关记忆来生成目的
            role_play_instruct = f"""
            请你扮演{self.name}，特性是：{self.desc}，
            可有的心情是{self.scene_knowledge.all_moods}，
            心情是{self.mood}，现在时间是{time},
            {self.name}当前位置是:{self.state.position}，
            {self.name}的最近记忆:{memory_latest_text}，
            {self.name}脑海中相关记忆:{memory_related_text}，
            {self.name}现在看到的人:{self.state.observation.people}，
            {self.name}现在看到的物品:{self.state.observation.items}，
            {self.name}可去的地方:{scene_allowed_places}，
            {self.name}现在看到的地点:{self.state.observation.locations}，    
            {self.name}之前的目的是:{self.purpose}
            """
            prompt = f"""
            请你为{self.name}生成一个目的，以下是例子：
            例1：[{self.scene_knowledge.all_moods[0]}]<{self.name}想去XXX，因为{self.name}想和XX聊聊天，关于{self.name}XXXXXXX。>
            例2：[{self.scene_knowledge.all_moods[1]}]<{self.name}想买一条趁手的扳手，这样就可以修理{self.name}家中损坏的椅子。>
            例3：[{self.scene_knowledge.all_moods[1]}]<{self.name}想去XXX的家，因为{self.name}想跟XXX搞好关系。>
            要求：
            1.按照[情绪]<目的>的方式来返回内容
            2.尽量使用第三人称来描述
            3.如果目的达成了一部分，那就去除完成的部分并继续规划
            4.如果目的不改变，可以返回: [情绪]<S>
            5.目的要在20字以内。
            6.目的要从最近记忆中出发。
            """
        # 发起请求
        purpose_response: str = self.call_llm(instruct=role_play_instruct, prompt=prompt)
        # 解析返回
        try:
            purpose: str = purpose_response.split("]<")[1].replace(">", "")
            mood: str = purpose_response.split("]<")[0].replace("[", "")
        except IndexError:
            self.logger.error(f"返回的目的格式不正确，返回内容为：{purpose_response}, 设定purpose为''")
            purpose = ""  # NULL
            mood = self.mood

        self.logger.debug(f"""
            <发起PURPOSE请求>
            <请求内容>:{role_play_instruct}
            <请求提示>:{prompt}
            <返回内容>:{purpose_response}
            <返回目的>:{purpose}
            <返回情绪>:{mood}
            """)
        # 更新情绪
        self.mood = mood
        # 如果目的不改变，那就直接返回
        if purpose == "<S>":
            return self.purpose
        # 如果目的改变，那就更新目的
        self.purpose = purpose
        return purpose

    # 生成行为
    def get_action(self, time: str, fail_safe: "FailSafe", k: int = 3) -> Dict[str, Any]:
        # TODO: 将返回的action做成类似conversation一样的list，然后返回游戏执行错误/成功，作为一个memoryitem
        """
        结合NPC的记忆、目的、情绪、位置、时间等信息来生成动作和参数
        大模型返回例:
            <chat|李大爷|李大爷你吃了吗>
            <mov|李大爷|>
            todo：返回一个action列表
            [<mov|箱子>,<take|箱子|西瓜汁>]
        函数返回例：
            {'action': 'take', 'object': '箱子', 'parameters': ['西瓜汁', '桃子', '枕头']}
        :param time:
        :param k:
        :return: Dict[str, Any]
        """
        # 按照NPC目的和NPC观察检索记忆
        query_text: str = self.purpose + ",".join(self.state.observation.items) + ",".join(
            self.state.observation.people) + ",".join(
            self.state.observation.locations)  # 这里暴力相加，感觉这不会影响提取的记忆相关性[或检索两次？]
        memory_dict: Dict[str, Any] = self.memory.search_memory(query_text=query_text, query_game_time=time, k=k)
        memory_related_text = [each.text for each in memory_dict["related_memories"]]
        memory_latest_text = [each.text for each in memory_dict["latest_memories"]]

        # 根据允许动作的预定义模版设置prompt
        # WARN: 动作空间应当从场景知识中获得，而非引擎属性。
        scene_allowed_actions: list[str] = self.scene_knowledge.all_actions
        allowed_actions: list[str] = [action_name for action_name in scene_allowed_actions if
                                      action_name in self.action_space]  # 场景action和人物action取交集
        allowed_actions_dict = {action_name: self.action_dict[action_name] for action_name in allowed_actions}
        action_prompt = ""
        for action_name, action_item in allowed_actions_dict.items():
            action_prompt += f"-`{action_item.example}`：{action_item.definition}\n"

        # 设置允许位置
        scene_allowed_places: list[str] = [place for place in self.scene_knowledge.all_places if
                                           place != self.state.position]  # 保留不是当前位置的场景记忆中的位置供llm选择

        # 构造prompt请求
        instruct = f"""
            请你扮演{self.name}，特性是:{self.desc}，心情是{self.mood}，
            现在时间是{time},
            {self.name}当前位置是:{self.state.position}，
            你的最近记忆:{memory_latest_text}
            你脑海中相关记忆:{memory_related_text}，
            你现在看到的人:{self.state.observation.people}，
            你现在看到的物品:{self.state.observation.items}，
            你现在身上的物品:{self.state.backpack}，
            你可去的地方:{scene_allowed_places}，
            你现在看到的地点:{self.state.observation.locations}，
            你当前目的:{self.purpose}
            行为定义：
            {action_prompt}
        """
        prompt = f"""
        请你根据`行为定义`，看到的事物，当前目的等返回动作、对象、参数的三元组以及行为描述，即：`<action|target|parameters>`和行为的描述
        """
        # 发起请求
        response: str = self.call_llm(instruct=instruct, prompt=prompt)
        # 抽取动作和参数
        self.action_result: Dict[str, Any] = ActionItem.str2json(response)
        # 检查action合法性，如不合法那就返回默认动作
        action_name = self.action_result["action"]
        if not action_name or action_name not in self.action_dict.keys():
            # failSafe
            fail_safe_action: "ActionItem" = fail_safe.action_fail_safe(action_name, list(self.action_dict.values()))
            if not fail_safe_action:
                illegal_action = self.action_result
                self.action_result = {"name": "", "object": "", "parameters": []}
                self.logger.error(
                    f"NPC:{self.name}的行为不合法，错误行为为:{illegal_action}, 返回默认行为:{self.action_result}")
            else:
                # 如果匹配到了fail_safe_action则替代
                action_name = fail_safe_action.name
                self.action_result["action"] = action_name

        # 按照配置文件决定是否分割参数
        if action_name in self.action_dict.keys():
            if not self.action_dict[action_name].multi_param:
                # 如果非多参数，比如对话，那就把参数合并成一个字符串
                self.action_result["parameters"] = ",".join(self.action_result["parameters"])
        # 添加npc_name
        self.action_result["npc_name"] = self.name
        self.logger.debug(f"""
            <发起ACTION请求>
            <请求内容>:{instruct}
            <请求提示>:{prompt}
            <返回内容>:{response}
            <返回行为>:{self.action_result}
                    """)
        return self.action_result

    # 生成单人2NPC对话
    def get_npc_response(self, player_name: str, player_speech: str, items_visible: List[str],
                         player_state_desc: str,
                         time: str, fail_safe: "FailSafe", k: int = 3) -> Dict[str, Any]:
        """
        接受玩家的状态，根据NPC的记忆和目的返回NPC的动作，回答，更新目的
            1.按照玩家问题、当前NPC目的，检索NPC的记忆
            2.按照记忆、之前的目的、当前状态、观察等，生成"目的(包含情绪)，动作，回答"
                例子： "%[开心]<找到西瓜汁>%<mov|大门|>%再见啦李大爷我有事先走啦%
            3.更新目的和情绪，返回动作和回答组成的数据包
            4.将本次交互组装为记忆，放入记忆库

        返回对象:
            {
            "name":"talk_result",
            "npc_name":"王大妈",
            "answer":"你吃饭了没？"
            "actions": [{
                "name":"action",
                "npc_name":"王大妈",
                "action":"mov",
                "object":"雁栖村入口",
                "parameters":[],
                        }]
            }

        :param player_name:
        :param player_speech:
        :param items_visible:
        :param player_state_desc:
        :param time:
        :param k:
        :return:
        """
        """
            1.按照玩家问题、当前NPC目的，检索NPC的记忆                        
        """
        query_text: str = self.purpose + ",".join(self.state.observation.items) + ",".join(
            self.state.observation.people) + ",".join(
            self.state.observation.locations)  # 这里暴力相加，感觉这不会影响提取的记忆相关性[或检索两次？]
        memory_dict: Dict[str, Any] = self.memory.search_memory(query_text=query_text, query_game_time=time, k=k)
        memory_related_text_purpose = [each.text for each in memory_dict["related_memories"]]
        memory_latest_text = [each.text for each in memory_dict["latest_memories"]]
        # 按照玩家的问句检索记忆
        query_text_player: str = player_speech
        memory_dict_player: Dict[str, Any] = self.memory.search_memory(query_text=query_text_player,
                                                                       query_game_time=time, k=k)
        memory_related_text_player = [each.text for each in memory_dict_player["related_memories"]]
        """
            2.按照记忆、之前的目的、当前状态、观察等，生成目的(包含情绪)，动作，回答
        """
        # 根据允许动作的预定义模版设置prompt
        scene_allowed_actions: list[str] = self.scene_knowledge.all_actions
        allowed_actions: list[str] = [action_name for action_name in scene_allowed_actions if
                                      action_name in self.action_space]  # 场景action和人物action取交集
        print(self.action_space)
        print(scene_allowed_actions)
        print(allowed_actions)
        allowed_actions_dict = {action_name: self.action_dict[action_name] for action_name in allowed_actions}
        action_prompt = ""
        for key, item in allowed_actions_dict.items():
            action_prompt += f"-`{item.example}`：{item.definition}\n"
        # 根据当前位置构造可去的位置(排除当前位置
        scene_allowed_places: list[str] = [place for place in self.scene_knowledge.all_places if
                                           place != self.state.position]

        # 创建talk_box
        if self.talk_box is None:
            self.talk_box = TalkBox(name=self.name, desc=self.desc, mood=self.mood, time=time,
                                    position=self.state.position, purpose=self.purpose,
                                    memory_latest_text=memory_latest_text,
                                    memory_related_text_purpose=memory_related_text_purpose,
                                    memory_related_text_player=memory_related_text_player,
                                    scene_allowed_places=scene_allowed_places,
                                    player_name=player_name, player_state_desc=player_state_desc,
                                    items_visible=items_visible, action_prompt=action_prompt,
                                    state=self.state.to_dict(), project_root_path=self.PROJECT_ROOT_PATH, model=self.ACTION_MODEL)
        response: str = self.talk_box.generate_response(input_text=player_speech, mood=self.mood,
                                                        memory_related_text_player=memory_related_text_player,
                                                        items_visible=items_visible,
                                                        state=self.state.to_dict())
        """
            3.更新目的和情绪，返回动作和回答组成的数据包
        """
        # 解析返回
        results = self.talk_box.parse_response(response)
        mood = results["mood"]
        purpose = results["purpose"]
        answer_text = results["answer"]
        action_text = results["action"]

        # 检查抽取到的动作
        self.action_result: Dict[str, Any] = ActionItem.str2json(action_text)
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
                action_name = fail_safe_action.name
                self.action_result["action"] = action_name

        # 按照配置文件决定是否分割参数
        if action_name in self.action_dict.keys():
            if not self.action_dict[action_name].multi_param:
                # 如果非多参数，比如对话，那就把参数合并成一个字符串
                self.action_result["parameters"] = ",".join(self.action_result["parameters"])
        self.action_result["npc_name"] = self.name
        # 更新NPC的情绪和purpose
        if not mood:
            mood = self.mood
        else:
            self.mood = mood
        self.purpose = purpose

        # dont need to add memory
        # """
        #     4.添加本次交互的记忆元素
        # """
        # memory_text = f"""
        #     {self.name}在{self.state.position}和{player_name}相遇，
        #     {self.name}的目的是{purpose}，
        #     {player_name} 的状态是{player_state_desc}，
        #     {player_name} 说: {player_speech}
        #     {self.name} 回答{player_name}: {answer_text}
        #     然后 采取了动作: {action_text}
        #     时间在：{time}
        # """
        # self.memory.add_memory_text(text=memory_text, game_time=time)

        response_package = {
            "name": "talk_result",
            "npc_name": self.name,
            "answer": answer_text,
            "actions": [self.action_result]
        }

        self.logger.debug(f"""
                    <TALK2NPC请求>
                    <返回行为>:{self.action_result}
                    <返回回答>:{answer_text}
                    <心情和目的>:{self.mood} {self.purpose}
                            """)
        return response_package

    def end_talk(self):
        """
        结束对话，进行三件事：1）提取talk_box内容；2）进行记忆整合；3）删除talk_box。
        """
        # 提取talk_box内容
        talk_content = self.talk_box.get_history_content()
        # todo 进行记忆整合
        print(talk_content)
        # self.memory.add_memory_text(text=talk_content, game_time=self.talk_box.time)
        # 删除talk_box
        self.talk_box = None

    def call_llm(self, instruct: str, prompt: str) -> str:
        llm_prompt_list = [{
            "role": "system",
            "content": instruct},
            {
                "role": "user",
                "content": prompt}
        ]
        # 测试使用百川2
        if self.ACTION_MODEL.startswith("baichuan2"):
            prompt = instruct + prompt
            answer = get_model_answer(model_name=self.ACTION_MODEL, inputs_list=[prompt],
                                      project_root_path=self.PROJECT_ROOT_PATH)
            self.logger.debug(f"<ACTION> 使用百川模型: {self.ACTION_MODEL}")
        elif self.ACTION_MODEL.startswith("gpt"):
            # 使用openai
            answer = get_model_answer(model_name=self.ACTION_MODEL, inputs_list=llm_prompt_list,
                                      project_root_path=self.PROJECT_ROOT_PATH)
            self.logger.debug(f"<ACTION> 使用openai模型{self.ACTION_MODEL}")
        elif self.ACTION_MODEL.startswith("gemini"):
            # 使用google Gemini
            answer = get_model_answer(model_name=self.ACTION_MODEL, inputs_list=llm_prompt_list,
                                      project_root_path=self.PROJECT_ROOT_PATH)
            self.logger.debug(f"<ACTION> 使用Google模型{self.ACTION_MODEL}")
        else:
            self.logger.debug(f"<ACTION> 使用自定模型{self.ACTION_MODEL}")
            answer = get_model_answer(model_name=self.ACTION_MODEL, inputs_list=llm_prompt_list,
                                      project_root_path=self.PROJECT_ROOT_PATH)
            # answer = get_model_answer(model_name='baichuan2-13b-4bit', inputs_list=[prompt], project_root_path=self.PROJECT_ROOT_PATH)
        return answer

    def save_memory(self):
        """
        以npc_name.json的形式保存npc的状态
        """
        NPC_CONFIG_PATH = self.CONFIG_PATH / "npc" / f"{self.name}.json"
        """ 保存示例: 李大爷.json
        {
          "name":"李大爷",
          "desc": "李大爷是一个普通的种瓜老头，戴着文邹邹的金丝眼镜，喜欢喝茶，平常最爱吃烤烧鸡喝乌龙茶；上午他喜欢呆在家里喝茶，下午他会在村口卖瓜，晚上他会去瓜田护理自己的西瓜",
          "mood":"开心",
          "npc_state": {
                "position": "李大爷家",
                "observation": {
                        "people": ["王大妈", "村长", "隐形李飞飞"],
                        "items": ["椅子#1","椅子#2","椅子#3[李大爷占用]","床"],
                        "locations": ["李大爷家大门","李大爷家后门","李大爷家院子"]
                              },
                "backpack":["黄瓜", "1000元", "老报纸"]
                     },
          "memory":["20年前在工厂表现优异获得表彰。","15年前在工厂收了两个徒弟。","8年前李大爷的两个徒弟在工厂表现优异都获得表彰。","6年前从工厂辞职并过上普通的生活。","4年前孩子看望李大爷并带上大爷最爱喝的乌龙茶。"]
        }
        """
        data = {
            # 初始化的必填参数
            "name": self.name,
            "desc": self.desc,
            "mood": self.mood,
            "npc_state": self.state.to_dict(),
            "memory": [item.text for item in list(self.memory.latest_k.queue)],

            # 无任何意义只是记录的参数
            "purpose": self.purpose,
            "action": self.action_result,
        }
        # 以json字符串的形式保存
        with open(NPC_CONFIG_PATH, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        self.logger.debug(f"已保存NPC:{self.name}的状态到{NPC_CONFIG_PATH}")
