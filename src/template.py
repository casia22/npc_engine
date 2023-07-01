from typing import List, Tuple, Dict, Any

class Engine_Prompt():
    # conversation system prompt in english
    def prompt_for_conversation_E(self, names, location, topic, descs, moods, memories, observations, all_actions,
                                  all_places, all_people, all_moods, starting):
        """
        生成英语对话剧本的prompt

        :param names:
        :param location:
        :param topic:
        :param descs:
        :param moods:
        :param memories:
        :param observations:
        :param all_actions:
        :param all_places:
        :param all_people:
        :param all_moods:
        :param starting:
        :return:
        """
        if starting == "" or not starting:
            introduction = rf"""There are currently {len(names)} characters engaging in a conversation about "{topic}" at "{location}". """
            task = rf"""
            Please use the information provided above, focus on the theme, and write the script for all characters to interact with each other. """
        else:
            introduction = rf"""A player is currently initiating a conversation with {len(names)} characters about "{topic}" at "{location}", starting with "{starting}". The player {descs[-1]}."""
            task = rf"""
            Please use the information provided above, focus on the theme, and continue writing the script for all other characters to interact with each other following the player's opening. """
        supplementary = "\n"
        for i in range(len(names)):
            supplementary += names[i] + descs[i] + names[i] + memories[i] + names[
                i] + rf"""'s current mood is {moods[i]}. """ + '\n'
        observe = rf"""
        Now these characters observe that: {observations}"""
        pre_statement = introduction + supplementary + observe + task

        # inform the constraints of generation
        constraint_statement = rf"""
        Each character's reply includes spoken content and possible action.
        The template for the reply is: <Character Name>|<Spoken Content>|Emotion|<Emotional State>|Action|<Action Name>|<Action Parameter>
        where,
        <Character Name>: {all_people}
        <Spoken Content>: Make guesses based on the previous context
        <Emotion>: {all_moods}
        <Action Type>: {all_actions}
        <Action Argument>: Can be <Place Name>, <Character Name>, or None
        <Place Name>: {all_places}
        When a character exits the conversation, it will no longer appear in the subsequent script. 
        When there is only one character left in the conversation and all the other characters exited, it is considered the end of the script. The ending symbol is: <EOC>.
        """

        # show some examples
        example_statement = rf"""
        Example : 
        (Remaining Characters : Lily, Jack, Tom)
        Lily|Hi, how are you.|Mood|Calm|Action|Chat|Jack&Tom
        Jack|I'am fine and we are discussing about math.|Mood|Calm|Action|Chat|Lily
        Tom|Yes, we are busy doing math homework.|Mood|Calm|Action|Chat|Lily
        Lily|OK, see you next time.|Mood|Calm|Action|Chat|Jack&Tom
        Jack|OK, see you.|Mood|Calm|Action|Chat|Lily
        Tom|See you Lily.|Mood|Calm|Action|Chat|Lily
        Lily||Mood|Calm|Action|Move|Home
        (Lily Exit. Remaining Charecters : Jack, Tom)
        Jack|Oh! My mom call me back, I have to go now.|Mood|Anxious|Action|Chat|Tom
        Tom|OK, see you, hove a good night.|Mood|Calm|Action|Chat|Tom
        Jack||Mood|Anxious|Action|Move|Home
        (Jack Exit. Remaining Characters : Tom)
        <EOC>
        """

        whole_statements = pre_statement + constraint_statement + example_statement
        system_prompt = {"role": "system", "content": whole_statements}
        query = {"role": "user", "content": "Player: " + starting + '\n'}

        return system_prompt, query

    # conversation system prompt in chinese
    def prompt_for_conversation_C(self, names, location, topic, descs, moods, memories, observations, all_actions,
                                  all_places, all_people, all_moods, starting):
        if starting == "" or not starting:
            introduction = rf"""现在有{len(names)}个角色正在‘{location}’中交流有关“{topic}”的内容。"""
            task = rf"""
            请基于上述信息，围绕主题，写一个所有角色互相交流的剧本。"""
        else:
            introduction = rf"""现有一位玩家在‘{location}’向{len(names)}个角色发起了有关“{topic}”话题的交流，玩家的开头说的是“{starting}”。该玩家{descs[-1]}。"""
            task = rf"""
            请基于上述信息，围绕主题，在玩家的开头后面续写所有其他角色互相交流的剧本。"""
        supplementary = "\n"
        for i in range(len(names)):
            supplementary += names[i] + descs[i] + names[i] + memories[i] + names[
                i] + rf"""此刻的心情是{moods[i]}。""" + '\n'
        observe = rf"""
        现在这些角色观测到：{observations}"""
        pre_statement = introduction + supplementary + observe + task

        # inform the constraints of generation
        constraint_statement = rf"""
        每个角色的回复包括说话内容和可能的动作
        回复的模板是：<角色姓名>|<语言内容>|情绪|<情绪状态>|动作|<动作名>|<动作参数>
        其中，
        <角色姓名>：{all_people}
        <语言内容>：自己根据上文推测
        <情绪状态>：{all_moods}
        <动作名>：{all_actions}
        <动作参数>：可以是<场所名>，可以是<角色姓名>，可以是None
        <场所名>：{all_places}
        当某个角色退出交流的时候，其将不再出现在后续的剧本中。
        当只剩下一个角色在交流而其他角色都退出了，则视为剧本结束，结束标志是：<EOC>。
        """

        # show some examples
        example_statement = rf"""
        例子：
        （剩下的角色：小明，小李，小张）
        小明|你好呀，你们最近过得如何？|情绪|稳定|动作|对话|小李&小张
        小李|我很好，我们现在正在讨论数学。|情绪|稳定|动作|对话|小明
        小张|是的，我们忙于做数学作业。|情绪|稳定|动作|对话|小明
        小明|好吧，下次再见。|情绪|稳定|动作|对话|小李&小张
        小李|好的，再见。|情绪|稳定|动作|对话|小明
        小张|再见小明。|情绪|稳定|动作|对话|小明
        小张||情绪|稳定|动作|前往|家
        （小明离开。剩下的角色：小李，小张）
        小李|哦！我妈妈让我回家，我得走了。|情绪|着急|动作|对话|小张
        小张|好的，祝你有个愉快的夜晚，再见。|情绪|稳定|动作|对话|小李
        小李||情绪|着急|动作|前往|家
        （小李离开。剩下的角色：小张）
        <EOC>
        """

        whole_statements = pre_statement + constraint_statement + example_statement
        system_prompt = {"role": "system", "content": whole_statements}
        query = {"role": "user", "content": "玩家：" + starting + '\n'}

        return system_prompt, query

    @staticmethod
    def prompt_for_topic(names: List[str], location: str, observations: str, language: str) -> Tuple[
        Dict[str, str], Dict[str, str]]:
        if language == "E":
            system_prompt = {"role": "system",
                             "content": rf"""Now there are {len(names)} characters communicating together at {location}, they are {", ".join(names)}, and their observations are: {observations}. Please generate a topic they might be discussed by them based on the above information.
            For example: the big tree nearby"""}
            query = {"role": "user", "content": rf"""
            Now, please generate a topic:
            """}
        else:
            system_prompt = {"role": "system",
                             "content": rf"""现在有{len(names)}个角色在{location}一起交流，他们分别是{"，".join(names)}，他们观测到周围信息是{observations}，请根据上述信息生成一个他们可能共同交谈的主题。
            比如：身边的大树"""}
            query = {"role": "user", "content": rf"""
            现在请生成一个主题：
            """}
        return system_prompt, query

    @staticmethod
    def prompt_for_re_creation(language, interruption, memory):
        if language == "E":
            assistant_prompt = {"role": "assistant", "content": "\n".join(memory) + '\n'}
            query = {"role": "user", "content": "Player: " + interruption + '\n'}
        else:
            assistant_prompt = {"role": "assistant", "content": "\n".join(memory + '\n')}
            query = {"role": "user", "content": "玩家：" + interruption + '\n'}
        return assistant_prompt, query
