import logging
import os
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
        self.memory_latest_text = kwargs.get("memory_latest_text", "")
        self.memory_related_text_purpose = kwargs.get("memory_related_text_purpose", "")
        self.memory_related_text_player = kwargs.get("memory_related_text_player", "")
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

        prompts = [
            generate_prompt("地点", self.scene_allowed_places, "你现在去不了任何地方", "你现在可以去{}"),
            generate_prompt("人", self.state_observation_people, "你现在看不到什么人", "你现在看到的人有{}"),
            generate_prompt("物品", self.state_observation_items, "周围没有什么能捡的东西", "周围能捡的东西有{}"),
            generate_prompt("地方", self.state_observation_locations, "周围看不到什么地方", "周围能看到的地方有{}"),
            generate_prompt("身上物品", self.state_backpack, "你现在身上空无一物", "你现在身上有{}")
        ]

        player_info_prompt = f"{self.player_name}正在和你说话，"
        player_info_prompt += "你对他一无所知" if not self.player_state_desc else f"你知道一些关于他的信息，{self.player_state_desc}"
        prompts.append(player_info_prompt)

        player_items_prompt = f"{self.player_name}身上"
        player_items_prompt += "没有任何东西" if not self.items_visible else f"有{self.items_visible}"
        prompts.append(player_items_prompt)

        prompt_text = "。".join(prompts)
        # print(prompts)

        instruct = f"""
                你是{self.name}，{self.desc}。现在时间是{self.time}，你当前在{self.state_position}，心情很{self.mood}。你的目的是:{self.purpose}，你记得{self.memory_latest_text}，{self.memory_related_text_purpose}， {self.memory_related_text_player}。{prompt_text}
                你需要以符合角色情绪和背景的方式作出回应，你的回应内容应包含：1.你当前的情绪，2.你接下来的目的，3.你想说的话，4.你想做出的行动。你的回应要采用特定格式：`@[你当前的情绪]<你接下来的目的>@你想说的话@<你想做出的行动>@`。`<你想做出的行动>`部分需要限定在以下定义中：
                {self.action_prompt}
                要求：
                - 你想做出的行为格式应为<动作|对象|参数>。
                - 行为必须与你的回答内容、情绪和目的逻辑上相关。
                - 你的目的描述应在10-30字之间。
                """
        # 删掉instruct中多余的空格和换行符
        instruct = '\n'.join([line.strip() for line in instruct.strip().split('\n')])
        print(instruct)
        self.history.append({"role": "system", "content": instruct})

    def generate_response(self, input_text, **kwargs):
        """
        生成回答
        :param input_text:
        :param kwargs:
        :return:
        """
        # 获取新的输入参数，对比是否和原先一致，不一致则更新，并且加入指令中
        instruct = []
        mood = kwargs.get("mood", "")
        memory_related_text_player = kwargs.get("memory_related_text_player", "")
        items_visible = kwargs.get("items_visible", [])
        state_backpack = kwargs.get("state", {}).get("backpack", [])

        if mood != self.mood and mood != "":
            instruct.append(f"{self.name}的心情是{mood}。")
            self.mood = mood
        if memory_related_text_player != self.memory_related_text_player and memory_related_text_player != "":
            instruct.append(f"{self.name}脑海中相关记忆:{memory_related_text_player}。")
            self.memory_related_text_player = memory_related_text_player
        if items_visible != self.items_visible and items_visible != []:
            instruct.append(f"{self.player_name}身上有：{items_visible}。")
            self.items_visible = items_visible
        if state_backpack != self.state_backpack and state_backpack != "":
            instruct.append(f"{self.name}现在身上的物品:{state_backpack}。")
            self.state_backpack = state_backpack

        if instruct:
            instruct = "，".join(instruct)
            self.history.append({"role": "system", "content": instruct})
        self.history.append({"role": "user", "content": input_text})
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
                history.append(f"{self.player_name}: {item['content']}")
            elif item["role"] == "assistant":
                assistant_content = self.parse_response(item['content'])
                history.append(f"{self.name}[{assistant_content.get('mood', '')}]: {assistant_content['answer']}")
        last_assistant_content = self.parse_response(self.history[-1]['content'])
        history.append(
            f"对话过后，{self.name}的心情很{last_assistant_content.get('mood', '')}，接下来的行动是{last_assistant_content.get('action', '')}。")
        history_content = "\n".join(history)
        return history_content

    def parse_response(self, content):
        if not content:
            content = self.response
        # 抽取 "目的情绪"、"动作"、"回答" 三个部分
        try:
            res1 = content.strip("@").split("@")
            if len(res1) == 3:
                mood_purpose, answer, action = res1
            else:
                mood_purpose, res2 = res1
                answer, action = res2.split("<")
                action = "<" + action
            # 格式化回答，去掉两边的引号
            mood, purpose = mood_purpose.split("<")
            # 去掉两边的"“”"|[]<>@等符号
            mood = mood.strip('"').strip("“").strip("”").strip("|").strip("[").strip("]").strip("<").strip(">")
            purpose = purpose.strip('"').strip("“").strip("”").strip("|").strip("[").strip("]").strip("<").strip(">")
            answer = answer.strip('"').strip("“").strip("”")
        except Exception as e:
            self.logger.error(f"解析回答时出错：{e}, {content}")
            mood = ""
            purpose = ""
            action = "<||>"
            answer = [x for x in content.strip("@").split("@") if x][-1]
        dict_response = {'mood': mood, 'purpose': purpose, 'answer': answer, 'action': action}
        return dict_response


if __name__ == "__main__":
    # Example of how to initialize TalkBox with specified parameters
    tb = TalkBox(
        name="草泥马",
        desc="一匹很凶的马，对人非常无理粗暴，喜欢说草泥马",
        mood="烦躁",
        time=datetime.strptime("2023-04-01 15:00:00", "%Y-%m-%d %H:%M:%S"),  # 假设当前时间
        position="沙漠中",
        purpose="草泥马现在又渴又饿，想找到吃的",
        memory_latest_text="做马真是太讨厌了，草泥马，我真的受够了！",
        memory_related_text_purpose="因为和大司马吵了一架而离开了马群，这是草泥马第一次冒险进入沙漠。",
        memory_related_text_player="",
        scene_allowed_places=["沙漠东部", "沙漠中心", "即将到达的绿洲"],
        action_prompt="[{'name': 'mov', 'definition': ('<mov|location|>，向[location]移动',), 'example': ('<mov|绿洲|>',)}, {'name': 'get', 'definition': ('<get|object1|object2>，从[object2]中获得[object1]，[object2]处可为空',), 'example': ('<get|水|水壶>',)}, {'name': 'put', 'definition': ('<put|object1|object2>，把[object2]放入[object1]',), 'example': ('<put|帐篷|沙漠中心>',)}, {'name': 'chat', 'definition': ('<chat|person|content>，对[person]说话，内容是[content]',), 'example': ('<chat|旅行者|你好呀，欢迎来到沙漠！>',)}]",
        state={'position': "沙漠中", 'people': ["沙漠商人"],
               'items': [],
               'locations': ["沙漠东部", "沙漠中心", "即将到达的绿洲"], 'backpack': ["遮阳帽"]},
        player_name="杨泽君",
        player_state_desc="杨泽君是一位年轻的法师，他看起来很帅气，穿着一身灰色的袍子，拿着一根法杖。看起来十分威风",
        items_visible=["法杖", "望远镜", "水", "饼干"],
        model="gpt-3.5-turbo-16k",
        project_root_path=Path(__file__).parents[3] / "example_project"
    )
    input("Press Enter to start the conversation")
    while True:
        user_input = input("User: ")
        if user_input == "exit":
            print(tb.get_history_content())
            break
        response = tb.generate_response(user_input)
        print(f"Assistant: {response}")
