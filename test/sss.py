from typing import List

class State:
    """
    游戏提供给NPC的状态
    """
    def __init__(self, position: str, backpack: List[str], ob_people: List[str], ob_items: List[str], ob_positions: List[str]):
        self.position = position
        self.backpack = backpack
        self.observation = self.Observation(ob_people, ob_items, ob_positions)

    class Observation:
        def __init__(self, people: List[str], items: List[str], positions: List[str]):
            self.people = people
            self.items = items
            self.positions = positions

        def __str__(self):
            return f'{{\n\t\t"people": {self.people},\n\t\t"items": {self.items},\n\t\t"positions": {self.positions}\n\t}}'

    def __str__(self):
        return f'{{\n\t"position": "{self.position}",\n\t"observation": {str(self.observation)},\n\t"backpack": {self.backpack}\n}}'

# 示例用法
state = State(
    position="李大爷家",
    backpack=["黄瓜", "1000元", "老报纸"],
    ob_people=["王大妈", "村长", "隐形李飞飞"],
    ob_items=["椅子#1", "椅子#2", "椅子#3[李大爷占用]", "床"],
    ob_positions=["李大爷家大门", "李大爷家后门", "李大爷家院子"]
)

print(str(state))
print(str(state.observation))
