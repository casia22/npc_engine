"""
Filename : template.py
Author : Yangzejun
Contact : yzj_cs_ilstar@163.com
"""

from typing import List, Tuple, Dict, Any
from nuwa.src.npc.knowledge import SceneConfig,PublicKnowledge

class EnginePrompt:
    """
    EnginePrompt类，内有四个函数提供大模型提示词
    """
    def __init__(
        self,
        knowledge: PublicKnowledge,
        scenario_name: str,
    ) -> None:
        # 剧本长字典{ 标识 : 长度范围 }
        self.number_of_lines: Dict[str, Tuple] = {
            'S' : (10 ,  25),
            'M' : (25 ,  45),
            "L" : (45 ,  70),
            'X' : (70 , 100),
        }
        self.all_actions: List[str] = knowledge.get_actions(scenario_name=scenario_name)
        self.all_places: List[str] = knowledge.get_places(scenario_name=scenario_name)
        self.all_people: List[str] = knowledge.get_people(scenario_name=scenario_name)
        self.all_moods: List[str] = knowledge.get_moods(scenario_name=scenario_name)

    def reset_knowledge(self, knowledge: PublicKnowledge, scenario_name: str):
        """
        使用新的knowledge重置EnginePrompt类属性
        :return:
        """
        self.all_actions: List[str] = knowledge.get_actions(scenario_name=scenario_name)
        self.all_places: List[str] = knowledge.get_places(scenario_name=scenario_name)
        self.all_people: List[str] = knowledge.get_people(scenario_name=scenario_name)
        self.all_moods: List[str] = knowledge.get_moods(scenario_name=scenario_name)

    @staticmethod
    def prompt_for_topic(
        names: List[str],
        location: str,
        states: List[Dict[str, Any]],
        language: str
    ) -> Tuple[Dict[str, str], Dict[str, str]]:
        """
        根据提供的信息和函数内的模板获取用于生成对话主题的系统提示词和查询提示词
        英文系统提示词例子：
        Now there are 2 characters communicating together at the location : park. They are Tony, Austin, and their observations are: tree, grass, flower..
        Please generate a topic they might be discussed by them based on the above information.
        For example : the big tree nearby.

        中文系统提示词例子：
        现在有2个角色在地点：公园，一起交流，他们分别是小白，小黑，他们观测到周围信息是小白，小黑，树，花，草，学校。
        请根据上述信息生成一个他们可能共同交谈的主题。
        比如：身边的大树。

        英文查询提示词例子：
        Generate your topic.

        中文查询提示词例子：
        生成你的主题。

        :param names:
        :param location:
        :param states:
        :param language:
        :return system_prompt, user_prompt:
        """
        ##################################################
        # 下面观测信息的提取过于死板，后续需要更改
        ##################################################
        obs_people = []
        obs_items = []
        obs_locations = []
        for state in states:
            obs_people.extend(state["observation"]["people"])
            obs_items.extend(state["observation"]["items"])
            obs_locations.extend(state["observation"]["locations"])
        observations = obs_people + obs_items + obs_locations

        # 获取系统提示词和查询提示词的内容
        if language == "E":
            system_content = rf"""Now there are {len(names)} characters communicating together at the location : {location}. They are {", ".join(names)}, and their observations are: {", ".join(observations)}.
                                Please generate a topic they might be discussed by them based on the above information.
                                For example : the big tree nearby."""
            user_content = """Generate your topic."""
        else:
            system_content = rf"""现在有{len(names)}个角色在地点：{location}，一起交流，他们分别是{"，".join(names)}，他们观测到周围信息是{"，".join(observations)}。
                                请根据上述信息生成一个他们可能共同交谈的主题。
                                比如：身边的大树。"""
            user_content = """生成你的主题。"""
        system_content = system_content.replace("    ","",16)
        # 获取系统提示词和查询提示词
        system_prompt = {"role": "system", "content": system_content}
        user_prompt = {"role": "user", "content": user_content}

        print("system prompt content for topic generation:")
        print(system_content)
        print("user prompt content for topic generation:")
        print(user_content)

        return system_prompt, user_prompt

    # TODO 将英文版对话创建于中文版的形式保持一致
    def prompt_for_conversation_e(
        self,
        names: List[str] = None,
        location: str = "",
        topic: str = "",
        descs: List[str] = None,
        moods: List[str] = None,
        memories: List[List[str]] = None,
        states: List[Dict[str, Any]] = None,
        starting: str = "",
        length: str = "",
    ) -> Tuple[Dict[str, str], Dict[str, str]]:
        """
        根据提供的信息和函数内的模板获取用于生成英文对话剧本的提示词，包括系统提示词和查询提示词
        系统提示词例子：
        Now I start a conversation with "Hi, bro" for 2 characters about "how to write math homework faster" at the location : park.
        My characteristic descriptions are : He is a docter.
        Tony's characteristic descriptions are : He is a teacher.
        In Tony's memory : He finished homework just now. He was a singer 10 years ago.
        Tony's current mood is : calm.
        Tony's current observation of people are: Austin, Lily.
        Tony's current observation of items are: tree, flower.
        Tony's current observation of locations are: church, school.
        Austin's characteristic descriptions are : He is a docter.
        In Austin's memory : He had courses just now. He was a dancer.
        Austin's current mood is : calm.
        Austin's current observation of people are: Tony, Lily.
        Austin's current observation of items are: tree, flower.
        Austin's current observation of locations are: church, school.
        Based on the information provided above, please use your imagination and generate a script of how these characters interact with each other or respond to me around the topic.

        The script consists of multiple lines of characters' interactions and conversation states.
        The template of character's interaction is - Character Name(Mood|Action Type|Action Argument): Spoken Content
        All the punctuation marks in the character's interaction template are half-width.
        Where,
        Character Name: Tony, Austin
        Mood: calm, happy, sad, anxious
        Action Type: chat, move
        Action Argument: can be Place Name, Character Name, or None.
        Place Name: Austin's home, Tony's home, park
        Spoken Content: can be any proper content related to topic, or None.
        The template of conversation state are - <Nobody / Character Name Exits. Remaining Characters: Character Names / Nobody> and <EOS>.
        All the punctuation marks in the conversation state template are half-width.
        At the beginning of the script, nobody exits and all charachters remain in the conversation.
        Afterwards, when a character exits the conversation, he/she no longer appear in the following script, the other remaining characters continue to interact.
        When all characters exit and no character remained in the conversation, which means the end of the script, you should use <EOC> as the ending symbol.

        Example:
        Input:
        Generate a script of how these characters interact or respond to me around the topic with about 10 to 25 lines.
        Me: "Hi, how are you?"
        Output:
        <Nobody Exits. Remaining Characters: Jack, Tom>
        Jack(Calm|Chat|Me): "I'am fine and we are talking about flowers."
        Tom(Happy|Chat|Me): "Yes, these flowers are so beautiful."
        Jack(Calm|Chat|Tom): "My mom likes flowers very much."
        Tom(Calm|Chat|Jack): "Well, my mom doesn't but my dad likes flowers."
        Jack(Calm|Chat|Me&Tom): "Ok, I have to go home for dinner, see you next time."
        Tom(Calm|Chat|Jack): "Ok, see you Jack."
        Jack(Calm|Move|Home): None
        <Jack Exits. Remaining Charecters: Tom>
        Tom(Calm|Chat|Me): "It is dark outside, I have to go home, too, see you."
        Tom(Calm|Move|Home): None
        <Tom Exits. Remaining Characters: Nobody>
        <EOC>

        查询提示词例子：
        Input:
        Generate a script of how these characters interact or respond to me around the topic with about 10 to 25 lines.
        Me: "Hi, bro"
        Output:
        
        :param names:
        :param location:
        :param topic:
        :param descs:
        :param moods:
        :param memories:
        :param states:
        :param starting:
        :param length:
        :return system_prompt, user_prompt:
        """
        # 根据是否有玩家的起头获取不同的对话介绍和任务信息
        if starting == "":
            introduction = rf"""Now there are {len(names)} characters having a conversation about "{topic}" at the location : {location}. """
            task = """Based on the information provided above, please use your imagination and generate a script of how these characters interact with each other around the topic. """
        else:
            introduction = rf"""Now I start a conversation with "{starting}" for {len(names)} characters about "{topic}" at the location : {location}.
                                My characteristic descriptions are : {descs[-1]}"""
            introduction = introduction.replace("    ","",8)
            task = """Based on the information provided above, please use your imagination and generate a script of how these characters interact with each other or respond to me around the topic. """
        # 收集每个参与对话角色的特征描述、记忆内容和当前情绪状态并整合成角色信息
        supplementary_list = []
        for i, name in enumerate(names):
            supplementary_new = rf"""{name}'s characteristic descriptions are : {descs[i]}
                                In {name}'s memory : {" ".join(memories[i])}
                                {name}'s current mood is : {moods[i]}. 
                                {name}'s current observation of people are: {", ".join(states[i]["observation"]["people"])}.
                                {name}'s current observation of items are: {", ".join(states[i]["observation"]["items"])}.
                                {name}'s current observation of locations are: {", ".join(states[i]["observation"]["locations"])}."""
            supplementary_new = supplementary_new.replace("    ","",40)
            supplementary_list.append(supplementary_new)
        supplementary = "\n".join(supplementary_list)
        # 蒋对话介绍、角色信息、观测信息和任务信息按顺序整合成预陈述
        pre_statement = "\n".join([introduction, supplementary, task])

        # 获取约束陈述，用来规范大模型输出剧本的格式和逻辑
        constraint_statement = rf"""The script consists of multiple lines of characters' interactions and conversation states.
                                    The template of character's interaction is - Character Name(Mood|Action Type|Action Argument): Spoken Content
                                    All the punctuation marks in the character's interaction template are half-width.
                                    Where,
                                    Character Name: {", ".join(names)}
                                    Mood: {", ".join(self.all_moods)}
                                    Action Type: {", ".join(self.all_actions)}
                                    Action Argument: can be Place Name, Character Name, or None.
                                    Place Name: {", ".join(self.all_places)}
                                    Spoken Content: can be any proper content related to topic, or None.
                                    The template of conversation state are - <Nobody / Character Name Exits. Remaining Characters: Character Names / Nobody> and <EOS>.
                                    All the punctuation marks in the conversation state template are half-width.
                                    At the beginning of the script, nobody exits and all charachters remain in the conversation.
                                    Afterwards, when a character exits the conversation, he/she no longer appear in the following script, the other remaining characters continue to interact.
                                    When all characters exit and no character remained in the conversation, which means the end of the script, you should use <EOC> as the ending symbol. """
        constraint_statement = constraint_statement.replace("    ","",126)

        # 根据是否有玩家的起头获取不同的案例陈述，为大模型提供生成对话剧本的简单例子
        if starting == "":
            example_statement = """Example:
                                Input:
                                Generate a script of how these characters interact around the topic with about 10 to 25 lines.
                                Output:
                                <Nobody Exits. Remaining Characters: Lily, Jack, Tom>
                                Lily(Calm|Chat|Jack&Tom): "Hi, how are you."
                                Jack(Calm|Chat|Lily): "I'am fine and we are discussing about math."
                                Tom(Calm|Chat|Lily): "Yes, we are busy doing math homework."
                                Lily(Calm|Chat|Jack&Tom): "OK, see you next time."
                                Jack(Calm|Chat|Lily): "OK, see you."
                                Tom(Calm|Chat|Lily): "See you Lily."
                                Lily(Calm|Move|Home): None
                                <Lily Exits. Remaining Charecters: Jack, Tom>
                                Jack(Anxious|Chat|Tom): "Oh! My mom call me back, I have to go now."
                                Tom(Calm|Chat|Tom): "OK, see you, I want to go to the park."
                                Jack(Anxious|Move|Home): None
                                <Jack Exits. Remaining Characters: Tom>
                                Tom(Calm|Move|Park): None
                                <Tom Exits. Remaining Characters: Nobody>
                                <EOC>"""
            example_statement = example_statement.replace("    ","",152)
        else:
            example_statement = """Example:
                                Input:
                                Generate a script of how these characters interact or respond to me around the topic with about 10 to 25 lines.
                                Me: "Hi, how are you?"
                                Output:
                                <Nobody Exits. Remaining Characters: Jack, Tom>
                                Jack(Calm|Chat|Me): "I'am fine and we are talking about flowers."
                                Tom(Happy|Chat|Me): "Yes, these flowers are so beautiful."
                                Jack(Calm|Chat|Tom): "My mom likes flowers very much."
                                Tom(Calm|Chat|Jack): "Well, my mom doesn't but my dad likes flowers."
                                Jack(Calm|Chat|Me&Tom): "Ok, I have to go home for dinner, see you next time."
                                Tom(Calm|Chat|Jack): "Ok, see you Jack."
                                Jack(Calm|Move|Home): None
                                <Jack Exits. Remaining Charecters: Tom>
                                Tom(Calm|Chat|Me): "It is dark outside, I have to go home, too, see you."
                                Tom(Calm|Move|Home): None
                                <Tom Exits. Remaining Characters: Nobody>
                                <EOC>"""
            example_statement = example_statement.replace("    ","",136)

        # 将预陈述、约束陈述和案例陈述按顺序拼接得到完整陈述，作为系统提示词的内容
        whole_statements = ("\n\n").join([pre_statement, constraint_statement, example_statement])
        # 获取系统提示词
        system_prompt = {"role": "system", "content": whole_statements}

        # 根据是否有玩家的起头获取不同的查询提示词内容
        if starting == "" :
            user_content = rf"""Input:
                                Generate a script of how these characters interact around the topic with about {self.number_of_lines[length][0]} to {self.number_of_lines[length][1]} lines.
                                Output:"""
            user_content = user_content.replace("    ","",16)
        else:
            user_content = rf"""Input:
                                Generate a script of how these characters interact or respond to me around the topic with about {self.number_of_lines[length][0]} to {self.number_of_lines[length][1]} lines.
                                Me: "{starting}"
                                Output:"""
            user_content = user_content.replace("    ","",24)
        # 获取查询提示词
        user_prompt = {"role": "user", "content": user_content}
        
        print("system prompt content for conversation creation in English:")
        print(whole_statements)
        print("user prompt content for conversation creation in English:")
        print(user_content)
        
        return system_prompt, user_prompt

    def prompt_for_conversation_c(
        self,
        names: List[str] = None,
        location: str = "",
        topic: str = "",
        descs: List[str] = None,
        moods: List[str] = None,
        memories: List[List[str]] = None,
        share_observations: Dict[str, List[str]] = None,
        starting: str = "",
        length: str = "",
    ) -> Tuple[Dict[str, str], Dict[str, str]]:
        """
        根据提供的信息和函数内的模板获取用于生成中文对话剧本的提示词，包括系统提示词和查询提示词

        starting为空时，系统提示词例子：

        现在有2个游戏NPC角色正在地点公园围绕“如何种植一棵苹果树”主题进行交流。
        NPC角色小白的个性描述是：他是一位老师。
        在小白的记忆中：他刚刚做完作业。他10年前是个歌手。
        小白此刻的心情是：稳定。
        玩家白的个性描述是：他是一个医生。
        发挥你的想象力，生成一个对话，展现这些NPC角色是如何围绕主题进行交流的。

        生成的对话由若干行NPC角色交互和NPC角色会话状态组成。
        NPC角色交互模板有两个，一个是NPC角色说话模板，一个是NPC角色前往模板
        NPC角色说话模板 - NPC角色姓名（情绪状态|说话|说话对象）：说话内容
        NPC角色前往模板 - NPC角色姓名（情绪状态|前往|前往对象）：空
        NPC角色姓名 ∈ {'小白', '小黑'}
        可选的情绪状态 ∈ {'伤心', '开心', '着急', '稳定'}
        可选的说话对象 ∈ {'小白', '小黑'}
        说话对象可以有多个，此时需要用&将对象名称连起来。
        说话内容可以是任务与主题有关的合规的内容。
        前往对象既可以是NPC角色也可以是地点
        可以前往的地点 ∈ {'小黑家', '小白家'}∪{'小黑的家', '公园', '小白的家'}
        可以前往的NPC角色 ∈ {'张益达', '刘芳菲'}
        会话状态的模板是 - <无人 / NPC角色姓名 退出。剩下的NPC角色：若干NPC角色姓名 / 无人> 以及 <结束>。
        当重新生成一个新对话时，无人退出且所有NPC角色都参与交流。
        后面当有NPC角色退出对话的时候，他/她将不再出现在后续对话中，其余NPC角色继续交流。
        当所有NPC角色都退出交流并且没有NPC角色剩余的时候，这意味着整个对话结束，你需要用 <结束> 作为结束标志。
        以上模板中的所有标点符号都是全角的。

        例子：
        输入：
        生成一个大约10到25行的对话内容，展现这些NPC角色是如何围绕主题进行交流的。
        输出：
        <无人退出。剩下的角色：小明，小李，小张>
        小明（稳定|对话|小李&小张）：“你好呀，你们最近过得如何？”
        小李（稳定|对话|小明）：“我很好，我们现在正在讨论数学。”
        小张（稳定|对话|小明）：“是的，我们忙于做数学作业。”
        小明（稳定|对话|小李&小张）：“好吧，下次再见。”
        小李（稳定|对话|小明）：“好的，再见。”
        小张（稳定|对话|小明）：“再见小明。”
        小张（稳定|前往|家）：空
        <小明退出。剩下的角色：小李，小张>
        小李（着急|对话|小张）：“哦！我妈妈让我回家，我得走了。”
        小张（稳定|对话|小李）：“好的，再见，我想去公园看看。”
        小李（着急|前往|家）：空
        <小李退出。剩下的角色：小张>
        小张（稳定|前往|公园）：空
        <小张退出。剩下的角色：无人>
        <结束>

        用户提示词例子：

        输入：
        生成一个大约70到100行的对话内容，展现这些NPC角色是如何围绕主题进行交流的。
        输出：

        starting非空时，系统提示词例子：

        一个游戏玩家杨泽君和2个游戏NPC角色正在地点公园围绕“如何种植一棵苹果树”主题进行交流。
        NPC角色小白的个性描述是：他是一位老师。
        在小白的记忆中：他刚刚做完作业。他10年前是个歌手。
        小白此刻的心情是：稳定。
        NPC角色小黑的个性描述是：他是一个医生。
        在小黑的记忆中：他刚刚上完课。他曾经是一个舞蹈演员。
        小黑此刻的心情是：稳定。
        玩家黑的个性描述是：是个帅哥
        发挥你的想象力，生成一个对话，展现这些NPC角色是如何围绕主题与玩家进行交流的，不能生成玩家的对话内容。

        生成的对话由若干行NPC角色交互和NPC角色会话状态组成。
        NPC角色交互模板有两个，一个是NPC角色说话模板，一个是NPC角色前往模板
        NPC角色说话模板 - NPC角色姓名（情绪状态|说话|说话对象）：说话内容
        NPC角色前往模板 - NPC角色姓名（情绪状态|前往|前往对象）：空
        NPC角色姓名 ∈ {'小白', '小黑', '杨泽君'}
        可选的情绪状态 ∈ {'着急', '伤心', '稳定', '开心'}
        可选的说话对象 ∈ {'小白', '玩家杨泽君', '小黑'}
        说话对象可以有多个，此时需要用&将对象名称连起来。
        说话内容可以是任务与主题有关的合规的内容。
        前往对象既可以是NPC角色也可以是地点
        可以前往的地点 ∈ {'小白家', '小黑家'}∪{'小黑的家', '小白的家', '公园'}
        可以前往的NPC角色 ∈ {'张益达', '刘芳菲'}
        会话状态的模板是 - <无人 / NPC角色姓名 退出。剩下的NPC角色：若干NPC角色姓名 / 无人> 以及 <结束>。
        当重新生成一个新对话时，无人退出且所有NPC角色都参与交流。
        后面当有NPC角色退出对话的时候，他/她将不再出现在后续对话中，其余NPC角色继续交流。
        当所有NPC角色都退出交流并且没有NPC角色剩余的时候，这意味着整个对话结束，你需要用 <结束> 作为结束标志。
        以上模板中的所有标点符号都是全角的。

        例子：
        输入：
        生成一个大约10到25行的对话内容，展现这些NPC角色是如何围绕主题与玩家杨泽君进行交流的。不能生成玩家的对话内容。
        玩家杨泽君：“你好，最近怎么样？”
        输出：
        <无人退出。剩下的角色：小李，小张>
        小李（稳定|对话|玩家杨泽君）：“我很好，我们在讨论花朵。”
        小张（开心|对话|玩家杨泽君）：“对的，这些花很漂亮。”
        小李（稳定|对话|小张）：“我母亲很喜欢花朵。”
        小张（稳定|对话|小李）：“喔喔，我母亲不喜欢，但是我父亲喜欢花。”
        小李（稳定|对话|玩家杨泽君&小张）：“好吧，我要回家吃晚饭了，下次再见。”
        小张（稳定|对话|小李）：“好的，再见小李。”
        小李（稳定|前往|家）：空
        <小李退出。剩下的角色：小张>
        小张（稳定|对话|玩家杨泽君）：“现在外面很黑，我也要回家了，再见。”
        小张（稳定|前往|家）：空
        <小张退出。剩下的角色：无人>
        <结束>

        用户提示词例子：
        
        输入
        生成一个大约70到100行的对话内容，展现这些NPC角色是如何围绕主题与玩家杨泽君进行交流的。不能生成玩家的对话内容。
        玩家杨泽君：“兄弟们雷好呀”
        输出：

        :param names:  参与对话的NPC角色名称列表 / + 玩家名称
        :param location:  对话发生的地点
        :param topic:  对话围绕的主题
        :param descs:  参与对话的NPC角色的个性描述列表 / + 玩家的个性描述
        :param moods:  参与对话的NPC角色的当前心情状态列表
        :param memories:  参与对话的NPC角色的记忆内容列表
        :param share_observations:  参与对话的NPC角色的观测信息
        :param starting:  玩家的起头
        :param length:  生成对话的行数范围
        :return system_prompt, user_prompt:
        """
        # 根据是否有玩家的起头获取不同的对话介绍和任务信息
        if starting == "":
            introduction = rf"""现在有{len(names)}个游戏NPC角色正在地点{location}围绕“{topic}”主题进行交流。"""
            task = """发挥你的想象力，生成一个对话，展现这些NPC角色是如何围绕主题进行交流的。"""
        else:
            introduction = rf"""一个游戏玩家{names[-1]}和{len(names)-1}个游戏NPC角色正在地点{location}围绕“{topic}”主题进行交流。"""
            task = """发挥你的想象力，生成一个对话，展现这些NPC角色是如何围绕主题与玩家进行交流的，不能生成玩家的对话内容。"""
        # 收集每个参与对话角色的特征描述、记忆内容和当前情绪状态并整合成角色信息
        supplementary_list = []

        if starting == "":
            for i, name in enumerate(names):
                supplementary_new = f"""NPC角色{name}的个性描述是：{descs[i]}
                                    在{name}的记忆中：{"".join(memories[i])}
                                    {name}此刻的心情是：{moods[i]}。"""
                supplementary_new = supplementary_new.replace("    ","",20)
                supplementary_list.append(supplementary_new)
        else:
            for i, name in enumerate(names[:-1]):
                supplementary_new = f"""NPC角色{name}的个性描述是：{descs[i]}
                                    在{name}的记忆中：{"".join(memories[i])}
                                    {name}此刻的心情是：{moods[i]}。"""
                supplementary_new = supplementary_new.replace("    ","",20)
                supplementary_list.append(supplementary_new)
        
            supplementary_player = f"""玩家{names[-1]}的个性描述是：{descs[-1]}"""
            supplementary_list.append(supplementary_player)

        supplementary = "\n".join(supplementary_list)

        # 显示地展示观测信息
        #observation_statement = rf"""这些角色除了看到了彼此以外，他们还观测到了其他的人和物。
        #                        他们观测到的远处的人有：{"，".join(share_observations["people"])}。
        #                        他们观测到的周围的物体有：{"，".join(share_observations["items"])}。
        #                        他们观测到的{location}中的地点有：{"，".join(share_observations["locations"])}。"""
        #observation_statement = observation_statement.replace("    ","",24)

        # 蒋对话介绍、角色信息、观测信息和任务信息按顺序整合成预陈述
        #pre_statement = "\n".join([introduction, supplementary, observation_statement, task])
        pre_statement = "\n".join([introduction, supplementary, task])

        # 获取约束陈述，用来规范大模型输出剧本的格式和逻辑
        if starting == "":
            constraint_statement = f"""生成的对话由若干行NPC角色交互和NPC角色会话状态组成。
                                    NPC角色交互模板有两个，一个是NPC角色说话模板，一个是NPC角色前往模板
                                    NPC角色说话模板是`NPC角色姓名（情绪状态|说话|说话对象）：说话内容`
                                    NPC角色前往模板是`NPC角色姓名（情绪状态|前往|前往对象）：空`
                                    NPC角色姓名 ∈ {set(names)}
                                    可选的情绪状态 ∈ {set(self.all_moods)}
                                    可选的说话对象 ∈ {set(names)}
                                    说话对象可以有多个，此时需要用&将对象名称连起来。
                                    说话内容可以是任务与主题有关的合规的内容。
                                    前往对象既可以是NPC角色也可以是地点
                                    可以前往的地点 ∈ {set(share_observations["locations"])}∪{set(self.all_places)}
                                    可以前往的NPC角色 ∈ {set(share_observations["people"])}
                                    会话状态的模板是`<无人 / NPC角色姓名 退出。剩下的NPC角色：若干NPC角色姓名 / 无>`以及`<结束>`。
                                    当重新生成一个新对话时，无人退出且所有NPC角色都参与交流。
                                    当有NPC角色退出对话的时候，他/她将不再出现在后续对话中，其余NPC角色继续交流。
                                    当所有NPC角色都退出交流并且没有NPC角色剩余的时候，这意味着整个对话结束，你需要用`<结束>`作为结束标志。
                                    以上模板中的所有标点符号都是全角的。"""
            constraint_statement = constraint_statement.replace("    ","",160)
        else:
            constraint_statement = f"""生成的对话由若干行NPC角色交互和NPC角色会话状态组成。
                                    NPC角色交互模板有两个，一个是NPC角色说话模板，一个是NPC角色前往模板
                                    NPC角色说话模板是`NPC角色姓名（情绪状态|说话|说话对象）：说话内容`
                                    NPC角色前往模板`NPC角色姓名（情绪状态|前往|前往对象）：空`
                                    NPC角色姓名 ∈ {set(names)}
                                    可选的情绪状态 ∈ {set(self.all_moods)}
                                    可选的说话对象 ∈ {set(names[:-1] + [f"玩家{names[-1]}"])}
                                    说话对象可以有多个，此时需要用&将对象名称连起来。
                                    说话内容可以是任务与主题有关的合规的内容。
                                    前往对象既可以是NPC角色也可以是地点
                                    可以前往的地点 ∈ {set(share_observations["locations"])}∪{set(self.all_places)}
                                    可以前往的NPC角色 ∈ {set(share_observations["people"])}
                                    会话状态的模板是`<无人 / NPC角色姓名 退出。剩下的NPC角色：若干NPC角色姓名 / 无>`以及`<结束>`。
                                    当重新生成一个新对话时，无人退出且所有NPC角色都参与交流。
                                    当有NPC角色退出对话的时候，他/她将不再出现在后续对话中，其余NPC角色继续交流。
                                    当所有NPC角色都退出交流并且没有NPC角色剩余的时候，这意味着整个对话结束，你需要用`<结束>`作为结束标志。
                                    以上模板中的所有标点符号都是全角的。"""
            constraint_statement = constraint_statement.replace("    ","",160)

        # 根据是否有玩家的起头获取不同的案例陈述，为大模型提供生成对话剧本的简单例子
        if starting == "":
            if length == "P":
                example_statement = """例子：
                                输入：
                                生成一个精简的对话，展现这些NPC角色是如何围绕主题进行交流的。不要交流与主题无关的内容。
                                输出：
                                <无人退出。剩下的NPC角色：小明，小李，小张>
                                小明（稳定|对话|小李&小张）：“你好呀，你们最近过得如何？”
                                小李（稳定|对话|小明）：“我很好，我们现在正在讨论数学。”
                                小张（稳定|对话|小明）：“是的，我们忙于做数学作业。”
                                小明（稳定|对话|小李&小张）：“好吧，下次再见。”
                                小李（稳定|对话|小明）：“好的，再见。”
                                小张（稳定|对话|小明）：“再见小明。”
                                小张（稳定|前往|家）：空
                                <小明退出。剩下的NPC角色：小李，小张>
                                小李（着急|对话|小张）：“哦！我妈妈让我回家，我得走了。”
                                小张（稳定|对话|小李）：“好的，再见，我想去公园看看。”
                                小李（着急|前往|家）：空
                                <小李退出。剩下的NPC角色：小张>
                                小张（稳定|前往|公园）：空
                                <小张退出。剩下的NPC角色：无>
                                <结束>"""
                example_statement = example_statement.replace("    ","",152)
            else:
                example_statement = """例子：
                                输入：
                                生成一个大约10到25行的对话内容，展现这些NPC角色是如何围绕主题进行交流的。
                                输出：
                                <无人退出。剩下的NPC角色：小明，小李，小张>
                                小明（稳定|对话|小李&小张）：“你好呀，你们最近过得如何？”
                                小李（稳定|对话|小明）：“我很好，我们现在正在讨论数学。”
                                小张（稳定|对话|小明）：“是的，我们忙于做数学作业。”
                                小明（稳定|对话|小李&小张）：“好吧，下次再见。”
                                小李（稳定|对话|小明）：“好的，再见。”
                                小张（稳定|对话|小明）：“再见小明。”
                                小张（稳定|前往|家）：空
                                <小明退出。剩下的NPC角色：小李，小张>
                                小李（着急|对话|小张）：“哦！我妈妈让我回家，我得走了。”
                                小张（稳定|对话|小李）：“好的，再见，我想去公园看看。”
                                小李（着急|前往|家）：空
                                <小李退出。剩下的NPC角色：小张>
                                小张（稳定|前往|公园）：空
                                <小张退出。剩下的NPC角色：无>
                                <结束>"""
                example_statement = example_statement.replace("    ","",152)
        else:
            if length == "P":
                example_statement = f"""例子：
                                输入：
                                生成一个精简的对话，展现这些NPC角色是如何围绕主题与玩家{names[-1]}进行交流的。不要交流与主题无关的内容。不能生成玩家的对话内容。
                                玩家{names[-1]}：“你好，最近怎么样？”
                                输出：
                                <无人退出。剩下的NPC角色：小李，小张>
                                小李（稳定|对话|玩家{names[-1]}）：“我很好，我们在讨论花朵。”
                                小张（开心|对话|玩家{names[-1]}）：“对的，这些花很漂亮。”
                                小李（稳定|对话|小张）：“我母亲很喜欢花朵。”
                                小张（稳定|对话|小李）：“喔喔，我母亲不喜欢，但是我父亲喜欢花。”
                                小李（稳定|对话|玩家{names[-1]}&小张）：“好吧，我要回家吃晚饭了，下次再见。”
                                小张（稳定|对话|小李）：“好的，再见小李。”
                                小李（稳定|前往|家）：空
                                <小李退出。剩下的NPC角色：小张>
                                小张（稳定|对话|玩家{names[-1]}）：“现在外面很黑，我也要回家了，再见。”
                                小张（稳定|前往|家）：空
                                <小张退出。剩下的NPC角色：无>
                                <结束>"""
                example_statement = example_statement.replace("    ","",200)
            else:
                example_statement = f"""例子：
                                输入：
                                生成一个大约10到25行的对话内容，展现这些NPC角色是如何围绕主题与玩家{names[-1]}进行交流的。不能生成玩家的对话内容。
                                玩家{names[-1]}：“你好，最近怎么样？”
                                输出：
                                <无人退出。剩下的NPC角色：小李，小张>
                                小李（稳定|对话|玩家{names[-1]}）：“我很好，我们在讨论花朵。”
                                小张（开心|对话|玩家{names[-1]}）：“对的，这些花很漂亮。”
                                小李（稳定|对话|小张）：“我母亲很喜欢花朵。”
                                小张（稳定|对话|小李）：“喔喔，我母亲不喜欢，但是我父亲喜欢花。”
                                小李（稳定|对话|玩家{names[-1]}&小张）：“好吧，我要回家吃晚饭了，下次再见。”
                                小张（稳定|对话|小李）：“好的，再见小李。”
                                小李（稳定|前往|家）：空
                                <小李退出。剩下的NPC角色：小张>
                                小张（稳定|对话|玩家{names[-1]}）：“现在外面很黑，我也要回家了，再见。”
                                小张（稳定|前往|家）：空
                                <小张退出。剩下的NPC角色：无>
                                <结束>"""
                example_statement = example_statement.replace("    ","",200)

        # 将预陈述、约束陈述和案例陈述按顺序拼接得到完整陈述，作为系统提示词的内容
        whole_statements = ("\n\n").join([pre_statement, constraint_statement, example_statement])
        # 获取系统提示词
        system_prompt = {"role": "system", "content": whole_statements}

        # 根据是否有玩家的起头获取不同的查询提示词内容
        if starting == "" :
            user_content = rf"""输入：
                                生成一个大约{self.number_of_lines[length][0]}到{self.number_of_lines[length][1]}行的对话内容，展现这些NPC角色是如何围绕主题进行交流的。
                                输出："""
            user_content = user_content.replace("    ","",16)
        else:
            user_content = rf"""输入
                                生成一个大约{self.number_of_lines[length][0]}到{self.number_of_lines[length][1]}行的对话内容，展现这些NPC角色是如何围绕主题与玩家{names[-1]}进行交流的。不能生成玩家的对话内容。
                                玩家{names[-1]}：“{starting}”
                                输出："""
            user_content = user_content.replace("    ","",24)
        # 获取查询提示词
        user_prompt = {"role": "user", "content": user_content}

        print("system prompt content for conversation creation in Chinese:")
        print(whole_statements)
        print("user prompt content for conversation creation in Chinese:")
        print(user_content)

        return system_prompt, user_prompt

    def prompt_for_re_creation(
        self,
        names: List[str] = None,
        location: str = "",
        topic: str = "",
        character: str = "",
        mood: str = "",
        descs: List[str] = None,
        memories: List[List[str]] = None,
        share_observations: Dict[str, List[str]] = None,
        interruption: str = "",
        length: str = "",
        history: List[str] = None,
    ) -> Tuple[Dict[str, str], Dict[str, str]]:
        """
        根据提供的信息和函数内的模板获取用于继续生成对话剧本的系统提示词和查询提示词
        中文系统提示词例子：

        中文查询提示词例子：

        :param names:  原先参与对话的NPC角色名称列表
        :param location:  对话发生的地点
        :param topic:  对话围绕的主题
        :param character:  新加入对话的NPC角色名称 / 玩家名称
        :param mood:  新加入对话的NPC角色的当前心情状态
        :param descs:  原先参与对话的NPC角色的个性描述列表 + （ 新加入对话的NPC角色的个性描述 / 玩家的个性描述 ）
        :param memories:  原先参与对话的NPC角色的记忆内容列表 + 新加入对话的NPC角色的记忆内容
        :param interruption:  玩家的打断
        :param length:  生成对话的行数范围
        :param history:  原先对话的历史记录
        :return system_prompt, user_prompt:
        """
        # 获取查询提示词
        if interruption == "":
            introduction = rf"""有{"，".join(names)}这{len(names)}个游戏NPC角色正在地点{location}围绕“{topic}”主题进行交流。
                                现在有一名新NPC角色{character}怀着{mood}的心情，加入了他们的对话。"""
            introduction = introduction.replace("    ","",8)
            task = """发挥你的想象力，在已经发生的对话后面续写对话，展现在新NPC角色的加入后所有NPC角色是如何共同围绕主题进行交流的。"""
        else:
            introduction = rf"""一个游戏玩家{character}和{"，".join(names)}这{len(names)}个游戏NPC角色正在地点{location}围绕“{topic}”主题进行交流。
                                这时游戏玩家{character}说了一句话：“{interruption}”"""
            introduction = introduction.replace("    ","",8)
            task = """发挥你的想象力，在已经发生的对话后面续写对话，展现这些NPC角色是如何围绕主题与玩家进行交流的，不能生成玩家的对话内容。"""
        
        if interruption == "":
            new_supplementary = f"""新NPC角色{character}的个性描述是：{descs[-1]}
                                在{character}的记忆中：{"".join(memories[-1])}"""
            new_supplementary = new_supplementary.replace("    ","",8)
        else:
            new_supplementary = f"""游戏玩家{character}的个性描述是：{descs[-1]}"""
        
        # 收集每个参与对话角色的特征描述、记忆内容和当前情绪状态并整合成角色信息
        supplementary_list = []
        for i, name in enumerate(names):
            supplementary_new = rf"""原先在对话中的NPC角色{name}的个性描述是：{descs[i]}
                                在{name}的记忆中：{"".join(memories[i])}"""
            supplementary_new = supplementary_new.replace("    ","",8)
            supplementary_list.append(supplementary_new)
        supplementary = "\n".join(supplementary_list)
        # 将对话介绍、角色信息、观测信息和任务信息按顺序整合成预陈述
        pre_statement = "\n".join([introduction, supplementary, new_supplementary, task])

        # 获取约束陈述，用来规范大模型输出剧本的格式和逻辑
    
        if interruption == "":
            constraint_statement = f"""生成的对话由若干行NPC角色交互和NPC角色会话状态组成。
                                    NPC角色交互模板有两个，一个是NPC角色说话模板，一个是NPC角色前往模板
                                    NPC角色说话模板是`NPC角色姓名（情绪状态|说话|说话对象）：说话内容`
                                    NPC角色前往模板是`NPC角色姓名（情绪状态|前往|前往对象）：空`
                                    NPC角色姓名 ∈ {set(names + [character])}
                                    可选的情绪状态 ∈ {set(self.all_moods)}
                                    可选的说话对象 ∈ {set(names + [character])}
                                    说话对象可以有多个，此时需要用&将对象名称连起来。
                                    说话内容可以是任务与主题有关的合规的内容。
                                    前往对象既可以是NPC角色也可以是地点
                                    可以前往的地点 ∈ {set(share_observations["locations"])}∪{set(self.all_places)}
                                    可以前往的NPC角色 ∈ {set(share_observations["people"])}
                                    会话状态的模板是`<无人 / NPC角色姓名 退出。剩下的NPC角色：若干NPC角色姓名 / 无>`以及`<结束>`。
                                    当重新生成一个新对话时，无人退出且所有NPC角色都参与交流。
                                    当有NPC角色退出对话的时候，他/她将不再出现在后续对话中，其余NPC角色继续交流。
                                    当所有NPC角色都退出交流并且没有NPC角色剩余的时候，这意味着整个对话结束，你需要用`<结束>`作为结束标志。
                                    以上模板中的所有标点符号都是全角的。"""
            constraint_statement = constraint_statement.replace("    ","",160)
        else:
            constraint_statement = f"""生成的对话由若干行NPC角色交互和NPC角色会话状态组成。
                                    NPC角色交互模板有两个，一个是NPC角色说话模板，一个是NPC角色前往模板
                                    NPC角色说话模板是`NPC角色姓名（情绪状态|说话|说话对象）：说话内容`
                                    NPC角色前往模板`NPC角色姓名（情绪状态|前往|前往对象）：空`
                                    NPC角色姓名 ∈ {set(names)}
                                    可选的情绪状态 ∈ {set(self.all_moods)}
                                    可选的说话对象 ∈ {set(names + [f"玩家{character}"])}
                                    说话对象可以有多个，此时需要用&将对象名称连起来。
                                    说话内容可以是任务与主题有关的合规的内容。
                                    前往对象既可以是NPC角色也可以是地点
                                    可以前往的地点 ∈ {set(share_observations["locations"])}∪{set(self.all_places)}
                                    可以前往的NPC角色 ∈ {set(share_observations["people"])}
                                    会话状态的模板是`<无人 / NPC角色姓名 退出。剩下的NPC角色：若干NPC角色姓名 / 无>`以及`<结束>`。
                                    当重新生成一个新对话时，无人退出且所有NPC角色都参与交流。
                                    当有NPC角色退出对话的时候，他/她将不再出现在后续对话中，其余NPC角色继续交流。
                                    当所有NPC角色都退出交流并且没有NPC角色剩余的时候，这意味着整个对话结束，你需要用`<结束>`作为结束标志。
                                    以上模板中的所有标点符号都是全角的。"""
            constraint_statement = constraint_statement.replace("    ","",160)

        # 根据是否有玩家的起头获取不同的案例陈述，为大模型提供生成对话剧本的简单例子
        if interruption == "":
            example_statement = """例子：
                                输入：
                                在如下已经发生的对话后面续写大约10到25行的对话内容，展现这些NPC角色是如何围绕主题进行交流的。
                                <无人退出。剩下的NPC角色：小明，小李，小张>
                                小明（稳定|对话|小李&小张）：“你好呀，你们最近过得如何？”
                                小李（稳定|对话|小明）：“我很好，我们现在正在讨论数学。”
                                小张（稳定|对话|小明）：“是的，我们忙于做数学作业。”
                                小明（稳定|对话|小李&小张）：“好吧，下次再见。”
                                小李（稳定|对话|小明）：“好的，再见。”
                                小张（稳定|对话|小明）：“再见小明。”
                                小张（稳定|前往|家）：空
                                <小明退出。剩下的NPC角色：小李，小张>
                                小李（难过|对话|小张）：“哦！今天真是糟糕的一天”
                                <小红加入对话>
                                输出：
                                <无人退出。剩下的NPC角色：小李，小张，小红>
                                小红（稳定|对话|小李&小张）：“各位好呀，我刚刚听见某人说今天很糟糕，发生什么事情了。”
                                小李（惊讶|对话|小红）：“小红你好呀，好久不见，刚刚是我说的今天很糟糕。”
                                小张（稳定|对话|小红）：“好久不见小红，小李可能遇到了什么烦心事。”
                                小李（稳定|对话|小红）：“是的，今天我总是说我贪玩，可是我已经写完作业了”
                                小红（稳定|对话|小李）：“可能是你母亲因为其他事情导致心情不好吧。”
                                小张（稳定|对话|小李）：“我也觉得有这个可能，有时候我父母也这样。”
                                小李（着急|对话|小红&小张）：“我妈让我赶紧回家了，不会又要说我吧。”
                                小红（稳定|对话|小李）：“放轻松哈，好好和你母亲聊聊天，可能就不那么生气了。”
                                小张（稳定|对话|小李）：“小红说的有道理，你快回家吧，我们明天有空再聊。”
                                小李（着急|对话|小红&小张）：“谢谢你们，我先回去了哈，再见。”
                                小红（稳定|对话|小李）：“再见小李。”
                                小张（稳定|对话|小李）：“拜拜。”
                                小李（着急|前往|家）：空
                                <小李退出。剩下的NPC角色：小张，小红>
                                小张（稳定|对话|小红）：“希望小李母亲的心情会好起来。”
                                小红（稳定|对话|小张）：“对呀，我也该回家了，回头见。”
                                小张（稳定|对话|小红）：“再见小红。”
                                小红（稳定|前往|家）：空
                                <小红退出。剩下的NPC角色：小张>
                                小张（稳定|前往|公园）：空
                                <小张退出。剩下的NPC角色：无>
                                <结束>"""
            example_statement = example_statement.replace("        ","",300)
        else:
            example_statement = f"""例子：
                                输入：
                                在如下已经发生的对话后面续写大约10到25行的对话内容，展现这些NPC角色是如何围绕主题与玩家{character}进行交流的。不能生成玩家的对话内容。
                                玩家{character}：“你好，最近怎么样？”
                                <无人退出。剩下的NPC角色：小李，小张>
                                小李（稳定|对话|玩家{character}）：“我很好，我们在讨论花朵。”
                                小张（开心|对话|玩家{character}）：“对的，这些花很漂亮。”
                                小李（稳定|对话|小张）：“我母亲很喜欢花朵。”
                                小张（稳定|对话|小李）：“喔喔，我母亲不喜欢，但是我父亲喜欢花。”
                                玩家{character}：“喜不喜欢花因人而异。”
                                输出：
                                <无人退出。剩下的NPC角色：小李，小张>
                                小李（稳定|对话|玩家{character}）：“对的，有的喜欢花就会去养花，有的人讨厌花就会远离它们。”
                                小张（稳定|对话|玩家{character}）：“我父亲的办公桌上就摆了很多小花，他很喜欢花。”
                                小李（稳定|对话|小张&玩家{character}）：“有空到我家来看看呀，我家的阳台被打扮成了小花园。”
                                小张（稳定|对话|小李）：“哇，真的吗，那我下次可以带我父亲一起来嘛？”
                                小李（稳定|对话|小张）：“当然可以，我父母和你父母也很熟，随时来做客。”
                                小张（开心|对话|小李）：“好嘞，有空格我一定要去看看，我还会带上我养的小狗一起。”
                                小李（开心|对话|小张）：“好呀好呀，我能想象出到时候我家的阳台肯定很热闹。”
                                小张（开心|对话|小李）：“那肯定的，我先去上课喽，有机会再聊。”
                                小李（开心|对话|小张）：“好嘞，如果家里没有什么事情了我就约你来我家玩哈。”
                                小张（开心|对话|小李&玩家{character}）：“好，再见啦。”
                                小李（开心|对话|小张）：“再见。”
                                小张（开心|前往|教室）：空
                                <小张退出。剩下的NPC角色：小李>
                                小李（开心|对话|玩家{character}）：“我也该回家啦，拜拜。”
                                小李（开心|前往|家）：空
                                <小李退出。剩下的NPC角色：无>
                                <结束>"""
            example_statement = example_statement.replace("        ","",300)

        # 将预陈述、约束陈述和案例陈述按顺序拼接得到完整陈述，作为系统提示词的内容
        system_content = ("\n\n").join([pre_statement, constraint_statement, example_statement])
        # 获取系统提示词
        system_prompt = {"role": "system", "content": system_content}

        # 根据是否有玩家的插入语句获取不同的查询提示词内容
        if interruption == "" :
            user_title = rf"""输入：
                                在如下已经发生的对话后面续写大约{self.number_of_lines[length][0]}到{self.number_of_lines[length][1]}行的对话内容，展现这些NPC角色是如何围绕主题进行交流的。"""
            user_title = user_title.replace("    ","",8)
            user_history = "\n".join(history)
            user_ending = rf"""<{character}加入对话>
                                输出："""
            user_ending = user_ending.replace("    ","",8)
            user_content = "\n".join([user_title, user_history, user_ending])
        else:
            user_title = rf"""输入：
                                在如下已经发生的对话后面续写大约{self.number_of_lines[length][0]}到{self.number_of_lines[length][1]}行的对话内容，展现这些NPC角色是如何围绕主题与玩家{character}进行交流的。不能生成玩家的对话内容。"""
            user_title = user_title.replace("    ","",8)
            user_history = "\n".join(history)
            user_ending = rf"""玩家{character}：“{interruption}”
                                输出："""
            user_ending = user_ending.replace("    ","",8)
            user_content = "\n".join([user_title, user_history, user_ending])
        # 获取查询提示词
        user_prompt = {"role": "user", "content": user_content}

        print("system prompt content for conversation re-creation in Chinese:")
        print(system_content)
        print("user prompt content for conversation re-creation in Chinese:")
        print(user_content)

        return system_prompt, user_prompt

if __name__ == '__main__':
    knowledge1 = {"all_actions" : ["chat","move"],
                  "all_places"  : ["Austin's home", "Tony's home", "park"],
                  "all_people"  : ["Tony", "Austin", "Cherry"],
                  "all_moods"   : ["calm", "happy", "sad", "anxious"]}
    knowledge2 = {"all_actions" : ["对话","前往"],
                  "all_places"  : ["小白的家", "小黑的家", "公园"],
                  "all_people"  : ["小白", "小黑", "小灰"],
                  "all_moods"   : ["稳定", "开心", "伤心", "着急"]}
    prompt = EnginePrompt(knowledge = knowledge2)
    '''
    prompt.prompt_for_re_creation(
        names = ["小白", "小黑"],
        location = "公园",
        topic = "如何种植一棵苹果树",
        character = "",#"小灰",
        mood = "",#"开心",
        descs = ["他是一位老师。", "他是一个医生。", "他是一个演说家。"],
        memories = [["他刚刚做完作业。","他10年前是个歌手。"], ["他刚刚上完课。", "他曾经是一个舞蹈演员。"], ["他刚刚吃了一些零食。","曾经在我是演说家比赛中获得冠军。"]],
        interruption = "其实我也很喜欢花。",
        length = "M",
        history = ["<无人退出。剩下的角色：小白，小黑>",
                  "小黑（稳定|对话|小白）：“我很好，我们在讨论花朵。”",
                  "小白（开心|对话|小黑）：“对的，这些花很漂亮。”",
                  "小黑（稳定|对话|小白）：“我母亲很喜欢花朵。”",
                  "小白（稳定|对话|小黑）：“喔喔，我母亲不喜欢，但是我父亲喜欢花。”"],
    )
    prompt.prompt_for_conversation_e(
        names = ["Tony", "Austin"],
        location = "park",
        topic = "how to write math homework faster",
        descs = ["He is a teacher.", "He is a docter."],
        moods = ["calm", "calm"],
        memories = [["He finished homework just now.","He was a singer 10 years ago."], ["He had courses just now.", "He was a dancer."]],
        observations = "tree, grass, flower.",
        starting = "Hi, bro",
        length='S'
    )
    prompt.prompt_for_conversation_c(
        names = ["小白", "小黑"],
        location = "公园",
        topic = "如何种植一棵苹果树",
        descs = ["他是一位老师。", "他是一个医生。"],
        moods = ["稳定", "稳定"],
        memories = [["他刚刚做完作业。","他10年前是个歌手。"], ["他刚刚上完课。", "他曾经是一个舞蹈演员。"]],
        observations = "树、花、草",
        starting = "你好，兄弟们。",
        length = 'X'
    )
    prompt.prompt_for_topic(names = ["小白", "小黑"],location = "公园",observations = "树、花、草",language="C")
    prompt.prompt_for_re_creation(language = 'C', interruption = "我母亲也不喜欢",
        memory = ["""<无人退出。剩下的角色：小李，小张>""",
                  """小李（稳定|对话|我）：“我很好，我们在讨论花朵。”""",
                  """小张（开心|对话|我）：“对的，这些花很漂亮。”""",
                  """小李（稳定|对话|小张）：“我母亲很喜欢花朵。”""",
                  """小张（稳定|对话|小李）：“喔喔，我母亲不喜欢，但是我父亲喜欢花。”"""])
    '''
