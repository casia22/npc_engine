import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path

from nuwa.src.npc.action import ActionItem
from nuwa.src.utils.model_api import get_model_answer


class TalkBox:
    def __init__(self, model, project_root_path, **kwargs):
        self.logger = logging.getLogger("NPC")
        self.history = []
        self.response = ""
        self.ACTION_MODEL = model
        self.PROJECT_ROOT_PATH = project_root_path

        # 根据各种参数初始化npc的系统指令
        self.name = kwargs.get("name", "")
        self.desc = kwargs.get("desc", "")
        self.mood = kwargs.get("mood", "")
        self.time = kwargs.get("time", "")
        self.purpose = kwargs.get("purpose", "")
        self.latest_memory = kwargs.get("latest_memory", [])
        self.purpose_related_memory = kwargs.get("purpose_related_memory", [])
        self.player_related_memory = kwargs.get("player_related_memory", [])
        self.action_prompt = kwargs.get("action_prompt", "")
        self.state_position = kwargs.get("state", {}).get("position", "")
        self.state_observation_people = kwargs.get("state", {}).get("people", [])
        self.state_observation_items = kwargs.get("state", {}).get("items", [])
        self.state_backpack = kwargs.get("state", {}).get("backpack", [])
        self.state_observation_locations = kwargs.get("state", {}).get("locations", [])
        self.scene_allowed_places = kwargs.get("scene_allowed_places", [])
        self.player_name = kwargs.get("player_name", "")
        self.player_state_desc = kwargs.get("player_state_desc", "")
        self.items_visible = kwargs.get("items_visible", [])

        def generate_prompt(description, items, empty_msg, non_empty_msg):
            """
            简化重复代码，根据信息生成指令
            """
            if not items:
                return empty_msg
            return non_empty_msg.format('、'.join(items))

        npc_info_prompts = [
            generate_prompt("时间", [self.time], "", "现在的时间是{}，"),
            generate_prompt("位置", [self.state_position], "", "你现在位于{}，"),
            generate_prompt("心情", [self.mood], "", "心情是{}，"),
            generate_prompt("目的", [self.purpose], "", "目的是{}，"),
            generate_prompt("记忆", self.latest_memory + self.purpose_related_memory, "", "你记得{}。"),
            generate_prompt("身上物品", self.state_backpack, "你现在身上空无一物", "你现在身上有{}。"),
            generate_prompt("地点", self.scene_allowed_places, "", "你现在可以去{}。"),
            generate_prompt("人", self.state_observation_people, "你现在看不到什么人。", "周围能看到的人有{}。"),
            generate_prompt("物品", self.state_observation_items, "周围没有什么能捡的东西。", "周围能捡的东西有{}。"),
            generate_prompt("地方", self.state_observation_locations, "周围看不到什么地方。", "周围能看到的地方有{}。"),
        ]

        player_info_prompts = [
            generate_prompt("人物", [self.player_name], "", "{}正在和你说话，"),
            generate_prompt("人物信息", [self.player_state_desc] + self.player_related_memory, "你对他一无所知。",
                            "你知道一些关于他的信息，{}。"),
            generate_prompt("人物身上物品", self.items_visible, "他身上没有任何东西。", "他身上有{}。")
        ]

        npc_prompt_text = "".join(npc_info_prompts)
        player_prompt_text = "".join(player_info_prompts)

        # instruct = f"""
        #         你是{self.name}，{self.desc}。现在的时间是{self.time}，你位于{self.state_position}，心情{self.mood}。你的目的是{self.purpose}。
        #         你记得最近的记忆是{self.latest_memory}，相关的记忆是{self.purpose_related_memory}，{self.player_related_memory}。
        #         {prompt_text}
        #
        #         请以符合你角色情绪和背景的方式作出回应，包括：
        #         1. 当前的情绪
        #         2. 想说的话
        #         3. 计划采取的行动
        #
        #         你的回应格式应该是：`@当前情绪@想说的话@<计划行动>@`。
        #         行动的格式应该是：<动作|对象|参数>，并且只能选择一个行动。
        #
        #         请注意，你的行动应该符合以下定义：
        #         {self.action_prompt}
        #         """
        instruct = f"""
                你是{self.name}，{self.desc}
                {npc_prompt_text}
                {player_prompt_text}
                You need to respond in a way that fits the character's emotions and background. 
                The output should be a markdown code snippet formatted in the following schema, including the leading and trailing "```json" and "```". including the content, {{"mood": Your current mood. "answer": What you want to say. "action": The actions you want to take. }}:
                
                ```json
                {{
                    "mood": string  // 开心
                    "answer": string  // 你好
                    "action": string  // <continue||>
                }}
                
                The action should be defined in the format: <Action|Object|Parameter>, and only one action can be selected from the following definitions:
                {self.action_prompt}
                ```
                用中文回答
                """
        # 删掉instruct中多余的空格和换行符
        instruct = '\n'.join([line.strip() for line in instruct.strip().split('\n')])
        print(instruct)
        self.history.append({"role": "system", "content": instruct})

    def generate_response(self, input_text, **kwargs):
        """
        生成回答
        """
        # 获取新的输入参数，对比是否和原先一致，不一致则更新，并且加入指令中
        instruct = []
        mood = kwargs.get("mood", "")
        memory_related_text_player = kwargs.get("player_related_memory", "")
        items_visible = kwargs.get("items_visible", [])
        state_backpack = kwargs.get("state", {}).get("backpack", [])

        if mood != self.mood and mood != "":
            instruct.append(f"{self.name}的心情是{mood}。")
            self.mood = mood
        # todo 目前记忆有问题，做好了再加上
        # if memory_related_text_player != self.player_related_memory and memory_related_text_player != "":
        #     instruct.append(f"{self.name}脑海中相关记忆:{memory_related_text_player}。")
        #     self.player_related_memory = memory_related_text_player
        if items_visible != self.items_visible and items_visible != []:
            instruct.append(f"{self.player_name}身上有：{items_visible}。")
            self.items_visible = items_visible
        if state_backpack != self.state_backpack and state_backpack != "":
            instruct.append(f"{self.name}现在身上的物品:{state_backpack}。")
            self.state_backpack = state_backpack

        if instruct:
            instruct = "，".join(instruct)
            self.history.append({"role": "system", "content": instruct})
        self.history.append({"role": "user", "content": f'{self.player_name}：{input_text}'})
        answer = get_model_answer(model_name=self.ACTION_MODEL, inputs_list=self.history,
                                  project_root_path=self.PROJECT_ROOT_PATH)
        self.history.append({"role": "assistant", "content": answer})
        # print(self.history)
        self.logger.debug(f"""
                    <TalkBox of {self.name}>
                    <对话列表>:{self.history}
                            """)
        self.response = answer
        return answer

    def get_history_content(self) -> str:
        """
        获取对话历史，只保留对话内容和最后的动作，整合成字符串
        """
        history = [f'{self.name}与{self.player_name}在{self.time}，{self.state_position}，发生了一次对话：']
        for item in self.history:
            if item["role"] == "user":
                history.append(f"{item['content']}")
            elif item["role"] == "assistant":
                assistant_content = self.parse_response_json(item['content'])
                history.append(f"{self.name}[{assistant_content.get('mood', '')}]：{assistant_content['answer']}")
        last_assistant_content = self.parse_response_json(self.history[-1]['content'])
        history.append(
            f"对话过后，{self.name}的心情很{last_assistant_content.get('mood', '')}，接下来的行动是{last_assistant_content.get('action', '')}。")
        history_content = "\n".join(history)
        return history_content

    def parse_response_json(self, content):
        """
        解析回答的json格式
        """
        if not content:
            content = self.response
        # remove ```json from the beginning and ``` from end
        content = content.lstrip("```json").rstrip("```")
        try:
            dict_response = json.loads(content)
        except Exception as e:
            self.logger.error(f"解析回答时出错：{e}, {content}")
            dict_response = {'mood': self.mood, 'purpose': self.purpose, 'answer': content, 'action': "<continue||>"}
        return dict_response


def remove_non_alphanumeric_from_ends(input_str):
    # 匹配字符串两端的中文、英文和数字之外的字符
    pattern = r'^[^>\u4e00-\u9fa5a-zA-Z0-9]*|[^>\u4e00-\u9fa5a-zA-Z0-9]*$'
    # 使用正则表达式匹配并删除
    result = re.sub(pattern, '', input_str)
    return result


if __name__ == "__main__":
    # Example of how to initialize TalkBox with specified parameters
    # tb = TalkBox(
    #     name="草泥马",
    #     desc="一匹很凶的马，对人非常无理粗暴，喜欢说草泥马",
    #     mood="烦躁",
    #     time=datetime.strptime("2023-04-01 15:00:00", "%Y-%m-%d %H:%M:%S"),  # 假设当前时间
    #     position="沙漠中",
    #     purpose="草泥马现在只想要远离人类",
    #     latest_memory="草泥马在沙漠中找到了一顶遮阳帽。",
    #     purpose_related_memory="因为和大司马吵了一架而离开了马群，这是草泥马第一次冒险进入沙漠。",
    #     player_related_memory="",
    #     scene_allowed_places=["沙漠东部", "沙漠中心", "即将到达的绿洲"],
    #     action_prompt="[{'name': 'move', 'definition': ('<move|location|>，向[location]移动',), 'example': ('<move|绿洲|>',)}, {'name': 'chat', 'definition': ('<chat|person|content>，对[person]说话，内容是[content]',), 'example': ('<chat|旅行者|你好呀，欢迎来到沙漠！>',)}, {'name': 'follow', 'definition': ('<follow|person|>，跟随[person]',), 'example': ('<follow|商人|>',)}, {'name': 'give', 'definition': ('<give|item|person>，给[person]一个[item]',), 'example': ('<give|水|商人>',)}]",
    #     state={'position': "沙漠中", 'people': ["沙漠商人"],
    #            'items': [],
    #            'locations': ["沙漠东部", "沙漠中心", "即将到达的绿洲"], 'backpack': ["遮阳帽"]},
    #     player_name="杨泽君",
    #     player_state_desc="杨泽君是一位年轻的法师，他看起来很帅气，穿着一身灰色的袍子，拿着一根法杖。看起来十分威风",
    #     items_visible=["法杖", "望远镜", "水", "饼干"],
    #     model="gpt-3.5-turbo-16k",
    #     project_root_path=Path(__file__).parents[3] / "example_project"
    # )
    tb = TalkBox(
        name="西格马",
        desc="一匹喜欢沉思的马，整天在思考数学问题。说话风格很简单，喜欢给别人出数学题。西格玛很独立，只有当别人解出正确答案时，西格马才会跟随别人，也就是follow。",
        mood="沉思",
        time="下午3:00",
        position="沙漠中",
        purpose="思考数学问题",
        memory_latest_text="",
        memory_related_text_purpose="",
        memory_related_text_player="",
        scene_allowed_places=[],
        action_prompt="[{'name': 'continue', 'definition': ('<continue||>，继续保持之前的动作',), 'example': ('<continue||>',)}, {'name': 'follow', 'definition': ('<follow|person|>，跟随[person]',), 'example': ('<follow|商人|>',)}, {'name': 'give', 'definition': ('<give|item|person>，将身上的[item]给[person]',), 'example': ('<give|水|商人>',)}]",
        state={'position': "沙漠中", 'people': ["沙漠商人"],
               'items': [],
               'locations': ["沙漠东部", "沙漠中心", "即将到达的绿洲"], 'backpack': [""]},
        player_name="杨泽君",
        player_state_desc="杨泽君是一位年轻的法师，他看起来很帅气，穿着一身灰色的袍子，拿着一根法杖。看起来十分威风",
        items_visible=["法杖", "望远镜", "水", "饼干"],
        model="gpt-3.5-turbo-16k",
        project_root_path=Path(__file__).parents[3] / "example_project"
    )
    input("Press Enter to start the conversation")
    while True:
        user_input = input("杨泽君: ")
        if user_input == "exit":
            print(tb.history)
            print(tb.get_history_content())
            break
        response = tb.generate_response(user_input)
        print(f"Assistant: {tb.parse_response_json(response)}")
