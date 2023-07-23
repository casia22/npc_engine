"""
Filename : template.py
Author : Yangzejun
Contact : yzj_cs_ilstar@163.com
"""

from typing import List, Tuple, Dict

class EnginePrompt:
    """
    EnginePrompt类，内有四个函数提供大模型提示词
    """
    def __init__(
        self,
        knowledge,
    ) -> None:
        # 剧本长字典{ 标识 : 长度范围 }
        self.number_of_lines: Dict[str, Tuple] = {
            'S' : (10 ,  25),
            'M' : (25 ,  45),
            "L" : (45 ,  70),
            'X' : (70 , 100),
        }
        self.all_actions: List[str] = knowledge["all_actions"]
        self.all_places: List[str] = knowledge["all_places"]
        self.all_people: List[str] = knowledge["all_people"]
        self.all_moods: List[str] = knowledge["all_moods"]

    def prompt_for_conversation_e(
        self,
        names: List[str] = None,
        location: str = "",
        topic: str = "",
        descs: List[str] = None,
        moods: List[str] = None,
        memories: List[List[str]] = None,
        observations: str = "",
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
        Austin's characteristic descriptions are : He is a docter.
        In Austin's memory : He had courses just now. He was a dancer.
        Austin's current mood is : calm.
        These characters observe that : tree, grass, flower.
        Based on the information provided above, please use your imagination and generate a script of how these characters interact with each other or respond to me around the topic.

        The script consists of multiple lines of characters' interactions and conversation states.
        The template of character's interaction is - Character Name(Mood|Action Type|Action Argument): Spoken Content
        Where,
        Character Name: Tony, Austin
        Mood: calm, happy, sad, anxious
        Action Type: chat, move
        Action Argument: can be Place Name, Character Name, or None.
        Place Name: Austin's home, Tony's home, park
        Spoken Content: can be any proper content related to topic, or None.
        The templates of conversation state are - <Nobody / Character Name Exits. Remaining Characters: Character Names / Nobody> and <EOS>.
        At the beginning of the script, nobody exists and all charachters remain in the conversation.
        Afterwards, when a character exits the conversation, he/she no longer appear in the following script, the other remaining characters continue to interact.
        When all characters exist and no character remained in the conversation, which means the end of the script, you should use <EOC> as the ending symbol.

        Example:
        Generate a script of how these characters interact or respond to me around the topic with about 10 to 25 lines.
        Me: "Hi, how are you?"
        <Nobody Exists. Remaining Characters: Jack, Tom>
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
        Generate a script of how these characters interact or respond to me around the topic with about 10 to 25 lines.
        Me: Hi, bro
        
        :param names:
        :param location:
        :param topic:
        :param descs:
        :param moods:
        :param memories:
        :param observations:
        :param starting:
        :param length:
        :return system_prompt, query_prompt:
        """
        # 根据是否有玩家的起头获取不同的对话介绍和任务信息
        if starting == "" or not starting:
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
                                {name}'s current mood is : {moods[i]}. """
            supplementary_new = supplementary_new.replace("    ","",16)
            supplementary_list.append(supplementary_new)
        supplementary = "\n".join(supplementary_list)
        # 获取对话角色的观测信息
        observe = rf"""These characters observe that : {observations}"""
        # 蒋对话介绍、角色信息、观测信息和任务信息按顺序整合成预陈述
        pre_statement = "\n".join([introduction, supplementary, observe, task])

        # 获取约束陈述，用来规范大模型输出剧本的格式和逻辑
        constraint_statement = rf"""The script consists of multiple lines of characters' interactions and conversation states.
                                    The template of character's interaction is - Character Name(Mood|Action Type|Action Argument): Spoken Content
                                    Where,
                                    Character Name: {", ".join(names)}
                                    Mood: {", ".join(self.all_moods)}
                                    Action Type: {", ".join(self.all_actions)}
                                    Action Argument: can be Place Name, Character Name, or None.
                                    Place Name: {", ".join(self.all_places)}
                                    Spoken Content: can be any proper content related to topic, or None.
                                    The templates of conversation state are - <Nobody / Character Name Exits. Remaining Characters: Character Names / Nobody> and <EOS>.
                                    At the beginning of the script, nobody exists and all charachters remain in the conversation.
                                    Afterwards, when a character exits the conversation, he/she no longer appear in the following script, the other remaining characters continue to interact.
                                    When all characters exist and no character remained in the conversation, which means the end of the script, you should use <EOC> as the ending symbol. """
        constraint_statement = constraint_statement.replace("    ","",108)

        # 根据是否有玩家的起头获取不同的案例陈述，为大模型提供生成对话剧本的简单例子
        if starting == "":
            example_statement = """Example:
                                Generate a script of how these characters interact around the topic with about 10 to 25 lines.
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
            example_statement = example_statement.replace("    ","",136)
        else:
            example_statement = """Example:
                                Generate a script of how these characters interact or respond to me around the topic with about 10 to 25 lines.
                                Me: "Hi, how are you?"
                                <Nobody Exists. Remaining Characters: Jack, Tom>
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
            example_statement = example_statement.replace("    ","",120)

        # 将预陈述、约束陈述和案例陈述按顺序拼接得到完整陈述，作为系统提示词的内容
        whole_statements = ("\n\n").join([pre_statement, constraint_statement, example_statement])
        # 获取系统提示词
        system_prompt = {"role": "system", "content": whole_statements}

        # 根据是否有玩家的起头获取不同的查询提示词内容
        if starting == "" :
            query_content = rf"""Generate a script of how these characters interact around the topic with about {self.number_of_lines[length][0]} to {self.number_of_lines[length][1]} lines."""
        else:
            query_content = rf"""Generate a script of how these characters interact or respond to me around the topic with about {self.number_of_lines[length][0]} to {self.number_of_lines[length][1]} lines.
                                Me: {starting}"""
            query_content = query_content.replace("    ","",8)
        # 获取查询提示词
        query_prompt = {"role": "user", "content": query_content}

        return system_prompt, query_prompt

    def prompt_for_conversation_c(
        self,
        names: List[str] = None,
        location: str = "",
        topic: str = "",
        descs: List[str] = None,
        moods: List[str] = None,
        memories: List[List[str]] = None,
        observations: str = "",
        starting: str = "",
        length: str = "",
    ) -> Tuple[Dict[str, str], Dict[str, str]]:
        """
        根据提供的信息和函数内的模板获取用于生成中文对话剧本的提示词，包括系统提示词和查询提示词
        系统提示词例子：
        现在我说了一句“你好，兄弟们。”作为开头，向2个角色发起了有关“如何种植一棵苹果树”主题的交流，交流地点在：公园。
        我的个性描述是：他是一个医生。
        小白的个性描述是：他是一位老师。
        在小白的记忆中：他刚刚做完作业。他10年前是个歌手。
        小白此刻的心情是: 稳定。
        小黑的个性描述是：他是一个医生。
        在小黑的记忆中：他刚刚上完课。他曾经是一个舞蹈演员。
        小黑此刻的心情是: 稳定。
        这些角色观测到：树、花、草 
        基于上述信息，请发挥你的想象力，生成一个剧本，展现这些角色是如何围绕主题进行交互或者回复我的。

        这个剧本由许多行角色交互和会话状态组成。
        角色交互的模板是 - 角色姓名（情绪状态|动作类型|动作参数）：说话内容 
        其中，
        角色姓名：小白, 小黑
        情绪状态：稳定, 开心, 伤心, 着急
        动作类型：对话, 前往
        动作参数：可以是场所名，角色姓名，或者空。
        场所名：小白的家, 小黑的家, 公园
        说话内容：可以是任务与主题有关的合规的内容，也可以是空。
        会话状态的模板是 - <角色姓名 / 无人 退出。剩下的角色：若干角色姓名 / 无人> 以及 <结束>。
        当剧本刚开始的时候，无人退出且所有角色都参与交流。
        后面当有角色退出会话的时候，他/她将不再出现在后续剧本中，其余角色继续交流。
        当所有角色都退出交流并且没有角色剩余的时候，这意味着剧本结束，你需要用 <结束> 作为结束标志。

        例子：
        生成一个大约10到25行的剧本，展现这些角色是如何围绕主题进行交互或者回复我的。
        我：“你好，最近怎么样？”
        <无人退出。剩下的角色：小李，小张>
        小李（稳定|对话|我）：“我很好，我们在讨论花朵。”
        小张（开心|对话|我）：“对的，这些花很漂亮。”
        小李（稳定|对话|小张）：“我母亲很喜欢花朵。”
        小张（稳定|对话|小李）：“喔喔，我母亲不喜欢，但是我父亲喜欢花。”
        小李（稳定|对话|我&小张）：“好吧，我要回家吃晚饭了，下次再见。”
        小张（稳定|对话|小李）：“好的，再见小李。”
        小李（稳定|前往|家）：空
        <小李退出。剩下的角色：小张>
        小张（稳定|对话|我）：“现在外面很黑，我也要回家了，再见。”
        小张（稳定|前往|家）：空
        <小张退出。剩下的角色：无人>
        <结束>
        生成一个大约70到100行的剧本，展现这些角色是如何围绕主题进行交互或者回复我的。
        我：你好，兄弟们。

        查询提示词例子：
        生成一个大约70到100行的剧本，展现这些角色是如何围绕主题进行交互或者回复我的。
        我：你好，兄弟们。
        
        :param names:
        :param location:
        :param topic:
        :param descs:
        :param moods:
        :param memories:
        :param observations:
        :param starting:
        :param length:
        :return system_prompt, query_prompt:
        """
        # 根据是否有玩家的起头获取不同的对话介绍和任务信息
        if starting == "" or not starting:
            introduction = rf"""现在有{len(names)}个角色正在地点：{location}，交流有关“{topic}”主题的内容。"""
            task = """基于上述信息，请发挥你的想象力，生成一个剧本，展现这些角色是如何围绕主题进行交互的。"""
        else:
            introduction = rf"""现在我说了一句“{starting}”作为开头，向{len(names)}个角色发起了有关“{topic}”主题的交流，交流地点在：{location}。
                                我的个性描述是：{descs[-1]}"""
            introduction = introduction.replace("    ","",8)
            task = """基于上述信息，请发挥你的想象力，生成一个剧本，展现这些角色是如何围绕主题进行交互或者回复我的。"""
        # 收集每个参与对话角色的特征描述、记忆内容和当前情绪状态并整合成角色信息
        supplementary_list = []
        for i, name in enumerate(names):
            supplementary_new = rf"""{name}的个性描述是：{descs[i]}
                                在{name}的记忆中：{" ".join(memories[i])}
                                {name}此刻的心情是：{moods[i]}。"""
            supplementary_new = supplementary_new.replace("    ","",16)
            supplementary_list.append(supplementary_new)
        supplementary = "\n".join(supplementary_list)
        # 获取对话角色的观测信息
        observe = rf"""这些角色观测到：{observations}"""
        # 蒋对话介绍、角色信息、观测信息和任务信息按顺序整合成预陈述
        pre_statement = "\n".join([introduction, supplementary, observe, task])

        # 获取约束陈述，用来规范大模型输出剧本的格式和逻辑
        constraint_statement = rf"""这个剧本由许多行角色交互和会话状态组成。
                                    角色交互的模板是 - 角色姓名（情绪状态|动作类型|动作参数）：说话内容
                                    其中，
                                    角色姓名：{", ".join(names)}
                                    情绪状态：{", ".join(self.all_moods)}
                                    动作类型：{", ".join(self.all_actions)}
                                    动作参数：可以是场所名，角色姓名，或者空。
                                    场所名：{", ".join(self.all_places)}
                                    说话内容：可以是任务与主题有关的合规的内容，也可以是空。
                                    会话状态的模板是 - <角色姓名 / 无人 退出。剩下的角色：若干角色姓名 / 无人> 以及 <结束>。
                                    当剧本刚开始的时候，无人退出且所有角色都参与交流。
                                    后面当有角色退出会话的时候，他/她将不再出现在后续剧本中，其余角色继续交流。
                                    当所有角色都退出交流并且没有角色剩余的时候，这意味着剧本结束，你需要用 <结束> 作为结束标志。"""
        constraint_statement = constraint_statement.replace("    ","",108)

        # 根据是否有玩家的起头获取不同的案例陈述，为大模型提供生成对话剧本的简单例子
        if starting == "":
            example_statement = """例子：
                                生成一个大约10到25行的剧本，展现这些角色是如何围绕主题进行交互的。
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
                                <结束>"""
            example_statement = example_statement.replace("    ","",136)
        else:
            example_statement = """例子：
                                生成一个大约10到25行的剧本，展现这些角色是如何围绕主题进行交互或者回复我的。
                                我：“你好，最近怎么样？”
                                <无人退出。剩下的角色：小李，小张>
                                小李（稳定|对话|我）：“我很好，我们在讨论花朵。”
                                小张（开心|对话|我）：“对的，这些花很漂亮。”
                                小李（稳定|对话|小张）：“我母亲很喜欢花朵。”
                                小张（稳定|对话|小李）：“喔喔，我母亲不喜欢，但是我父亲喜欢花。”
                                小李（稳定|对话|我&小张）：“好吧，我要回家吃晚饭了，下次再见。”
                                小张（稳定|对话|小李）：“好的，再见小李。”
                                小李（稳定|前往|家）：空
                                <小李退出。剩下的角色：小张>
                                小张（稳定|对话|我）：“现在外面很黑，我也要回家了，再见。”
                                小张（稳定|前往|家）：空
                                <小张退出。剩下的角色：无人>
                                <结束>"""
            example_statement = example_statement.replace("    ","",120)

        # 将预陈述、约束陈述和案例陈述按顺序拼接得到完整陈述，作为系统提示词的内容
        whole_statements = ("\n\n").join([pre_statement, constraint_statement, example_statement])
        # 获取系统提示词
        system_prompt = {"role": "system", "content": whole_statements}

        # 根据是否有玩家的起头获取不同的查询提示词内容
        if starting == "" :
            query_content = rf"""生成一个大约{self.number_of_lines[length][0]}到{self.number_of_lines[length][1]}行的剧本，展现这些角色是如何围绕主题进行交互的。"""
        else:
            query_content = rf"""生成一个大约{self.number_of_lines[length][0]}到{self.number_of_lines[length][1]}行的剧本，展现这些角色是如何围绕主题进行交互或者回复我的。
                                我：{starting}"""
            query_content = query_content.replace("    ","",8)
        # 获取查询提示词
        query_prompt = {"role": "user", "content": query_content}

        return system_prompt, query_prompt

    @staticmethod
    def prompt_for_topic(
        names: List[str],
        location: str,
        observations: str,
        language: str
    ) -> Tuple[Dict[str, str], Dict[str, str]]:
        """
        根据提供的信息和函数内的模板获取用于生成对话主题的系统提示词和查询提示词
        英文系统提示词例子：
        Now there are 2 characters communicating together at the location : park. They are Tony, Austin, and their observations are: tree, grass, flower..
        Please generate a topic they might be discussed by them based on the above information.
        For example : the big tree nearby.

        中文系统提示词例子：
        现在有2个角色在地点：公园，一起交流，他们分别是小白，小黑，他们观测到周围信息是树、花、草。
        请根据上述信息生成一个他们可能共同交谈的主题。
        比如：身边的大树。

        英文查询提示词例子：
        Generate your topic.

        中文查询提示词例子：
        生成你的主题。

        :param names:
        :param location:
        :param observations:
        :param language:
        :return system_prompt, query_prompt:
        """
        # 获取系统提示词和查询提示词的内容
        if language == "E":
            system_content = rf"""Now there are {len(names)} characters communicating together at the location : {location}. They are {", ".join(names)}, and their observations are: {observations}.
                                Please generate a topic they might be discussed by them based on the above information.
                                For example : the big tree nearby."""
            query_content = """Generate your topic."""
        else:
            system_content = rf"""现在有{len(names)}个角色在地点：{location}，一起交流，他们分别是{"，".join(names)}，他们观测到周围信息是{observations}。
                                请根据上述信息生成一个他们可能共同交谈的主题。
                                比如：身边的大树。"""
            query_content = """生成你的主题。"""
        system_content = system_content.replace("    ","",16)
        # 获取系统提示词和查询提示词
        system_prompt = {"role": "system", "content": system_content}
        query_prompt = {"role": "user", "content": query_content}

        return system_prompt, query_prompt

    @staticmethod
    def prompt_for_re_creation(
        language: str,
        interruption: str,
        memory: List[str]
    ) -> Tuple[Dict[str, str], Dict[str, str]]:
        """
        根据提供的信息和函数内的模板获取用于继续生成对话剧本的助理提示词和查询提示词
        英文助理提示词例子：
        Jack(Calm|Chat|Me): "I'am fine and we are talking about flowers." 
        Tom(Happy|Chat|Me): "Yes, these flowers are so beautiful."
        Jack(Calm|Chat|Tom): "My mom likes flowers very much."
        Tom(Calm|Chat|Jack): "Well, my mom doesn't but my dad likes flowers."

        中文助理提示词例子：
        <无人退出。剩下的角色：小李，小张>
        小李（稳定|对话|我）：“我很好，我们在讨论花朵。”
        小张（开心|对话|我）：“对的，这些花很漂亮。”
        小李（稳定|对话|小张）：“我母亲很喜欢花朵。”
        小张（稳定|对话|小李）：“喔喔，我母亲不喜欢，但是我父亲喜欢花。”

        英文查询提示词例子：
        Me: "My mom doesn't too."

        中文查询提示词例子：
        我：“我母亲也不喜欢”

        :param language:
        :param interruption:
        :param memory:
        :return assistant_prompt, query_prompt:
        """
        # 获取查询提示词
        if language == "E":
            query_prompt = {"role": "user", "content": rf"""Me: "{interruption}" """}
        else:
            query_prompt = {"role": "user", "content": rf"""我：“{interruption}”"""}
        # 获取助理提示词的内容
        assistant_content = "\n".join(memory)
        # 获取助理提示词
        assistant_prompt = {"role": "assistant","content": assistant_content}

        return assistant_prompt, query_prompt

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
