import os
from datetime import datetime
from pathlib import Path

from nuwa.src.utils.model_api import get_model_answer


class TalkBox:
    def __init__(self, model, project_root_path, **kwargs):
        self.history = []
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
        self.scene_allowed_places = kwargs.get("scene_allowed_places", [])
        self.player_name = kwargs.get("player_name", "")
        self.player_state_desc = kwargs.get("player_state_desc", "")
        self.items_visible = kwargs.get("items_visible", [])
        self.action_prompt = kwargs.get("action_prompt", "")
        self.state_position = kwargs.get("state", {}).get("position", "")
        self.state_observation_people = kwargs.get("state", {}).get("people", [])
        self.state_observation_items = kwargs.get("state", {}).get("items", [])
        self.state_backpack = kwargs.get("state", {}).get("backpack", [])
        self.state_observation_locations = kwargs.get("state", {}).get("locations", [])

        instruct = f"""
                请你扮演{self.name}，设定是：{self.desc}。
                你的心情是{self.mood}，现在时间是{self.time},
                {self.name}当前位置是:{self.state_position}，
                你之前的目的是:{self.purpose},
                你的最近记忆:{self.memory_latest_text},
                你脑海中相关记忆:{self.memory_related_text_purpose + self.memory_related_text_player}，
                你现在看到的人:{self.state_observation_people}，
                你现在看到的物品:{self.state_observation_items}，
                你现在身上的物品:{self.state_backpack}，
                你可去的地方:{self.scene_allowed_places}，
                你现在看到的地点:{self.state_observation_locations}，
                他的背景：{self.player_state_desc}，
                他身上有：{self.items_visible}。
                每当有人与你对话时，你都会以符合角色情绪和背景的方式回应，应包含：1.情绪，2.角色目的，3.回答内容，4.角色行为，采用特定格式：`@[情绪]<角色目的>@回答内容@<动作|对象|参数>@`。
                这个格式方便游戏端进行解析。`<动作|对象|参数>`部分需要限定在以下[行为定义]中：
                {self.action_prompt}
                要求：
                    1.一次仅返回一个行为，而不是多个行为
                    2.行为中的动作必须是[行为定义]出现的动作，格式为<action_name|obj|param>
                    3.角色的行为必须和角色的回答内容、目的有逻辑关系。
                    4.角色目的应该为10-30字。
                """
        self.history.append({"role": "system", "content": instruct})

    def get_response(self, input_text, **kwargs):
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
        print(self.history)
        return answer

    def get_history(self):
        return self.history


if __name__ == "__main__":
    # Example of how to initialize TalkBox with specified parameters
    tb = TalkBox(
        name="李大爷",
        desc="一个普通的种瓜老头，戴着文邹邹的金丝眼镜，喜欢喝茶，最爱吃烤烧鸡喝乌龙茶。",
        mood="开心",
        time=datetime.strptime("2021-01-01 12:00:00", "%Y-%m-%d %H:%M:%S"),
        position="李大爷家",
        purpose="李大爷想去村口卖瓜，希望能够卖出新鲜的西瓜给村里的居民。",
        memory_latest_text="8年前李大爷的两个徒弟在工厂表现优异都获得表彰。6年前从工厂辞职并过上普通的生活。4年前孩子看望李大爷并带上大爷最爱喝的乌龙茶。",
        memory_related_text_purpose="15年前在工厂收了两个徒弟。",
        memory_related_text_player="",
        scene_allowed_places=["李大爷家大门", "李大爷家后门", "李大爷家院子"],
        player_name="王大妈",
        player_state_desc="正在李大爷家",
        items_visible=["椅子#1", "椅子#2", "椅子#3[李大爷占用]", "床"],
        action_prompt="行为定义列表及要求",
        state={'position': "李大爷家", 'people': ["王大妈", "村长", "隐形李飞飞"],
               'items': ["椅子#1", "椅子#2", "椅子#3[李大爷占用]", "床"],
               'locations': ["李大爷家大门", "李大爷家后门", "李大爷家院子"], 'backpack': ["西瓜"]},
        model="gpt-3.5-turbo-16k",
        project_root_path=Path(__file__).parents[3] / "example_project"
    )
    input("Press Enter to start the conversation")
    while True:
        user_input = input("User: ")
        response = tb.get_response(user_input)
        print(f"Assistant: {response}")
        if response == "Goodbye!":
            break
