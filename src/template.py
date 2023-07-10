from typing import List, Tuple, Dict, Any

class Engine_Prompt:
    # length annotation
    def __init__(self) -> None:
        self.number_of_lines = {
            'S' : (10 ,  25),
            'M' : (25 ,  45),
            "L" : (45 ,  70),
            'X' : (70 , 100)}
    
    # conversation system prompt in english
    def prompt_for_conversation_E(
        self,
        names,
        location,
        topic,
        descs,
        moods,
        memories,
        observations,
        all_actions,
        all_places,
        all_people,
        all_moods,
        starting,
        length
    ):
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
        :param length:
        :return:
        """
        if starting == "" or not starting:
            introduction = rf"""Now there are {len(names)} characters having a conversation about "{topic}" at the location : {location}. """
            task = rf"""Based on the information provided above, please use your imagination and generate a script of how these characters interact with each other around the topic. """
        else:
            introduction = rf"""Now I start a conversation with "{starting}" for {len(names)} characters about "{topic}" at the location : {location}. """ + '\n' + \
            rf"""My characteristic descriptions are : {descs[-1]}"""
            task = rf"""Based on the information provided above, please use your imagination and generate a script of how these characters interact with each other or respond to me around the topic. """
        supplementary = "\n"
        for i in range(len(names)):
            supplementary += (
                names[i] + "'s characteristic descriptions are : "
                + descs[i]
                + "\n"
                + "In " + names[i] + "'s memory : "
                + " ".join(memories[i])
                + "\n"
                + names[i]
                + rf"""'s current mood is : {moods[i]}. """
                + "\n"
            )  # memories = ['sentence1', 'sentence2', ...]
        observe = rf"""These characters observe that : {observations} """ + '\n'
        pre_statement = introduction + supplementary + observe + task

        # inform the constraints of generation
        constraint_statement =  rf"""The script consists of multiple lines of characters' interactions and conversation states. """ + '\n' + \
                                rf"""The template of character's interaction is - <Character Name>(<Mood>, <Action Type> <Action Argument>): "<Spoken Content>".""" + '\n' + \
                                rf"""Where,""" + '\n' + \
                                rf"""<Character Name>: {", ".join(names)}""" + '\n' + \
                                rf"""<Mood>: {", ".join(all_moods)}""" + '\n' + \
                                rf"""<Action Type>: {", ".join(all_actions)}""" + '\n' + \
                                rf"""<Action Argument>: can be <Place Name>, <Character Name>, or None.""" + '\n' + \
                                rf"""<Place Name>: {", ".join(all_places)}""" + '\n' + \
                                rf"""<Spoken Content>: can be any proper content related to topic, or None, and names of <All People> can appear in the content.""" + '\n' + \
                                rf"""<All People>: {", ".join(all_people)}""" + '\n' + \
                                rf"""The templates of conversation state are - <<Character Name> Exits. Remaining Characters: <Character Name>...> and <EOS>. """ + '\n' + \
                                rf"""At the beginning of the script, or, when a character exits the conversation, you should use <<Character Name> Exit. Remaining Characters : <Character Name>...>. """ + '\n' + \
                                rf"""When all characters exist and no character left in the conversation, which is considered the end of the script, you should use <EOC> as ending symbol of script. """

        # show some examples
        if starting == "":
            example_statement = rf"""Example: """ + '\n' + \
                                rf"""Generate a script of how these characters interact around the topic with about 10 to 25 lines.""" + '\n'+ \
                                rf"""<Nobody Exits. Remaining Characters: Lily, Jack, Tom>""" + '\n' + \
                                rf"""Lily(Calm, Chat Jack&Tom): "Hi, how are you." """ + '\n' + \
                                rf"""Jack(Calm, Chat Lily): "I'am fine and we are discussing about math." """ + '\n' + \
                                rf"""Tom(Calm, Chat Lily): "Yes, we are busy doing math homework." """ + '\n' + \
                                rf"""Lily(Calm, Chat Jack&Tom): "OK, see you next time." """ + '\n' + \
                                rf"""Jack(Calm, Chat Lily): "OK, see you." """ + '\n' + \
                                rf"""Tom(Calm, Chat Lily): "See you Lily." """ + '\n' + \
                                rf"""Lily(Calm, Move Home): None""" + '\n' + \
                                rf"""<Lily Exits. Remaining Charecters: Jack, Tom>""" + '\n' + \
                                rf"""Jack(Anxious, Chat Tom): "Oh! My mom call me back, I have to go now." """ + '\n' + \
                                rf"""Tom(Calm, Chat Tom): "OK, see you, I want to go to the park." """ + '\n' + \
                                rf"""Jack(Anxious, Move Home): None""" + '\n' + \
                                rf"""<Jack Exits. Remaining Characters: Tom>""" + '\n' + \
                                rf"""Tom(Calm, Move Park): None""" + '\n' + \
                                rf"""<Tom Exits. Remaining Characters: Nobody>""" + '\n' + \
                                rf"""<EOC>"""
        else:
            example_statement = rf"""Example: """ + '\n' + \
                                rf"""Generate a script of how these characters interact or respond to me around the topic with about 10 to 25 lines.""" + '\n'+ \
                                rf"""Me: "Hi, how are you?" """ + '\n' + \
                                rf"""<Nobody Exists. Remaining Characters: Jack, Tom>""" + '\n' + \
                                rf"""Jack(Calm, Chat Me): "I'am fine and we are talking about flowers." """ + '\n' + \
                                rf"""Tom(Happy, Chat Me): "Yes, these flowers are so beautiful." """ + '\n' + \
                                rf"""Jack(Calm, Chat Tom): "My mom likes flowers very much." """ + '\n' + \
                                rf"""Tom(Calm, Chat Jack): "Well, my mom doesn't but my dad likes flowers." """ + '\n' + \
                                rf"""Jack(Calm, Chat Me&Tom): "Ok, I have to go home for dinner, see you next time." """ + '\n' + \
                                rf"""Tom(Calm, Chat Jack): "Ok, see you Jack." """ + '\n' + \
                                rf"""Jack(Calm, Move Home): None""" + '\n' + \
                                rf"""<Jack Exits. Remaining Charecters: Tom>""" + '\n' + \
                                rf"""Tom(Calm, Chat Me): "It is dark outside, I have to go home, too, see you." """ + '\n' + \
                                rf"""Tom(Calm, Move Home): None""" + '\n' + \
                                rf"""<Tom Exits. Remaining Characters: Nobody>""" + '\n' + \
                                rf"""<EOC>"""

        whole_statements = ("\n\n").join([pre_statement, constraint_statement, example_statement])
        print(whole_statements)
        system_prompt = {"role": "system", "content": whole_statements}

        if starting == "" :
            query_content = rf"""Generate a script of how these characters interact around the topic with about {self.number_of_lines[length][0]} to {self.number_of_lines[length][1]} lines."""
        else:
            query_content = rf"""Generate a script of how these characters interact or respond to me around the topic with about {self.number_of_lines[length][0]} to {self.number_of_lines[length][1]} lines.""" + '\n' + "Me: " + starting
        print(query_content)
        query_prompt = {"role": "user", "content": query_content}

        return system_prompt, query_prompt

    # conversation system prompt in chinese
    def prompt_for_conversation_C(
        self,
        names,
        location,
        topic,
        descs,
        moods,
        memories,
        observations,
        all_actions,
        all_places,
        all_people,
        all_moods,
        starting,
        length
    ):
        if starting == "" or not starting:
            introduction = rf"""现在有{len(names)}个角色正在地点：{location}，交流有关“{topic}”主题的内容。"""
            task = rf"""基于上述信息，请发挥你的想象力，生成一个剧本，展现这些角色是如何围绕主题进行交互的。"""
        else:
            introduction = rf"""现在我说了一句“{starting}”作为开头，向{len(names)}个角色发起了有关“{topic}”主题的交流，交流地点在：{location}。""" + '\n' + \
            rf"""我的个性描述是：{descs[-1]}"""
            task = rf"""基于上述信息，请发挥你的想象力，生成一个剧本，展现这些角色是如何围绕主题进行交互或者回复我的。"""
        supplementary = "\n"
        for i in range(len(names)):
            supplementary += (
                names[i] + "的个性描述是："
                + descs[i]
                + "\n"
                + "在" + names[i] + "的记忆中："
                + "".join(memories[i])
                + "\n"
                + names[i]
                + rf"""此刻的心情是: {moods[i]}。"""
                + "\n"
            )  # memories = ['sentence1', 'sentence2', ...]
        observe = rf"""这些角色观测到：{observations} """ + '\n'
        pre_statement = introduction + supplementary + observe + task

        constraint_statement =  rf"""这个剧本由许多行角色交互和会话状态组成。""" + '\n' + \
                                rf"""角色交互的模板是 - <角色姓名>（<情绪状态>，<动作类型> <动作参数>）：“<说话内容>”。""" + '\n' + \
                                rf"""其中，""" + '\n' + \
                                rf"""<角色姓名>：{", ".join(names)}""" + '\n' + \
                                rf"""<情绪状态>：{", ".join(all_moods)}""" + '\n' + \
                                rf"""<动作类型>：{", ".join(all_actions)}""" + '\n' + \
                                rf"""<动作参数>：可以是<场所名>，<角色姓名>，或者空。""" + '\n' + \
                                rf"""<场所名>：{", ".join(all_places)}""" + '\n' + \
                                rf"""<说话内容>：可以是任务与主题有关的合规的内容，也可以是空，并且<所有角色>的名字均可以出现在内容中。""" + '\n' + \
                                rf"""当某个角色退出交流的时候，其将不再出现在后续的剧本，并且你需要展示此时交流中角色的存在状态。""" + '\n' + \
                                rf"""<所有角色>：{", ".join(all_people)}""" + '\n' + \
                                rf"""会话状态的模板是 - <<角色姓名>退出。剩下的角色：<角色姓名>。。。> 以及 <结束>。""" + '\n' + \
                                rf"""当剧本刚开始，或者当有角色退出交流的时候，你需要使用 <<角色姓名>退出了。剩下的角色：<角色姓名>。。。>。""" + \
                                rf"""当所有角色都退出交流并且没有角色剩余的时候，你需要用 <结束> 作为剧本的结束标志。"""
        
        # show some examples
        if starting == "":
            example_statement = rf"""例子：""" + '\n' + \
                                rf"""生成一个大约10到25行的剧本，展现这些角色是如何围绕主题进行交互的。""" + '\n'+ \
                                rf"""<无人退出。剩下的角色：小明，小李，小张>""" + '\n' + \
                                rf"""小明（稳定，对话 小李&小张）：“你好呀，你们最近过得如何？”""" + '\n' + \
                                rf"""小李（稳定，对话 小明）：“我很好，我们现在正在讨论数学。”""" + '\n' + \
                                rf"""小张（稳定，对话 小明）：“是的，我们忙于做数学作业。”""" + '\n' + \
                                rf"""小明（稳定，对话 小李&小张）：“好吧，下次再见。”""" + '\n' + \
                                rf"""小李（稳定，对话 小明）：“好的，再见。”""" + '\n' + \
                                rf"""小张（稳定，对话 小明）：“再见小明。”""" + '\n' + \
                                rf"""小张（稳定，前往 家）：空""" + '\n' + \
                                rf"""<小明退出。剩下的角色：小李，小张>""" + '\n' + \
                                rf"""小李（着急，对话 小张）：“哦！我妈妈让我回家，我得走了。”""" + '\n' + \
                                rf"""小张（稳定，对话 小李）：“好的，再见，我想去公园看看。”""" + '\n' + \
                                rf"""小李（着急，前往 家）：空""" + '\n' + \
                                rf"""<小李退出。剩下的角色：小张>""" + '\n' + \
                                rf"""小张（稳定，前往 公园）：空""" + '\n' + \
                                rf"""<小张退出。剩下的角色：无人>""" + '\n' + \
                                rf"""<结束>"""
        else:
            example_statement = rf"""例子：""" + '\n' + \
                                rf"""生成一个大约10到25行的剧本，展现这些角色是如何围绕主题进行交互或者回复我的。""" + '\n'+ \
                                rf"""我：“你好，最近怎么样？”""" + '\n' + \
                                rf"""<无人退出。剩下的角色：小李，小张>""" + '\n' + \
                                rf"""小李（稳定，对话 我）：“我很好，我们在讨论花朵。”""" + '\n' + \
                                rf"""小张（开心，对话 我）：“对的，这些花很漂亮。”""" + '\n' + \
                                rf"""小李（稳定，对话 小张）：“我母亲很喜欢花朵。”""" + '\n' + \
                                rf"""小张（稳定，对话 小李）：“喔喔，我母亲不喜欢，但是我父亲喜欢花。”""" + '\n' + \
                                rf"""小李（稳定，对话 我&小张）：“好吧，我要回家吃晚饭了，下次再见。”""" + '\n' + \
                                rf"""小张（稳定，对话 小李）：“好的，再见小李。”""" + '\n' + \
                                rf"""小李（稳定，前往 家）：空""" + '\n' + \
                                rf"""<小李退出。剩下的角色：小张>""" + '\n' + \
                                rf"""小张（稳定，对话 我）：“现在外面很黑，我也要回家了，再见。”""" + '\n' + \
                                rf"""小张（稳定，前往 家）：空""" + '\n' + \
                                rf"""<小张退出。剩下的角色：无人>""" + '\n' + \
                                rf"""<结束>"""

        whole_statements = ("\n\n").join([pre_statement, constraint_statement, example_statement])
        print(whole_statements)
        system_prompt = {"role": "system", "content": whole_statements}

        if starting == "" :
            query_content = rf"""生成一个大约{self.number_of_lines[length][0]}到{self.number_of_lines[length][1]}行的剧本，展现这些角色是如何围绕主题进行交互的。"""
        else:
            query_content = rf"""生成一个大约{self.number_of_lines[length][0]}到{self.number_of_lines[length][1]}行的剧本，展现这些角色是如何围绕主题进行交互或者回复我的。""" + "\n" + "我：" + starting
        print(query_content)
        query_prompt = {"role": "user", "content": query_content}

        return system_prompt, query_prompt

    @staticmethod
    def prompt_for_topic(
        names: List[str], location: str, observations: str, language: str
    ) -> Tuple[Dict[str, str], Dict[str, str]]:
        if language == "E":
            system_content = rf"""Now there are {len(names)} characters communicating together at the location : {location}. They are {", ".join(names)}, and their observations are: {observations}. """ + '\n' \
                           + rf"""Please generate a topic they might be discussed by them based on the above information.""" + '\n' \
                           + rf"""For example : the big tree nearby."""
            query_content = rf"""Generate your topic."""
        else:
            system_content = rf"""现在有{len(names)}个角色在地点：{location}，一起交流，他们分别是{"，".join(names)}，他们观测到周围信息是{observations}。""" + '\n' \
                           + rf"""请根据上述信息生成一个他们可能共同交谈的主题。""" + '\n' \
                           + rf"""比如：身边的大树。"""
            query_content = rf"""生成你的主题。"""
        
        system_prompt = {"role": "system", "content": system_content}            
        query_prompt = {"role": "user", "content": query_content}

        return system_prompt, query_prompt

    @staticmethod
    def prompt_for_re_creation(language, interruption, memory):
        if language == "E":
            query_prompt = {"role": "user", "content": "Player : " + interruption}
        else:
            query_prompt = {"role": "user", "content": "我：" + interruption}

        assistant_content = "\n".join(memory)
        assistant_prompt = {
                "role": "assistant",
                "content": assistant_content}
        return assistant_prompt, query_prompt

if __name__ == '__main__':
    prompt = Engine_Prompt()
    '''
    prompt.prompt_for_conversation_E(
        names = ["Tony", "Austin"],
        location = "park",
        topic = "how to write math homework faster",
        descs = ["He is a teacher.", "He is a docter."],
        moods = ["calm", "calm"],
        memories = [["He finished homework just now.","He was a singer 10 years ago."], ["He had courses just now.", "He was a dancer."]],
        observations = "tree, grass, flower.",
        all_actions = ["chat","move"],
        all_places = ["Austin's home", "Tony's home", "park"],
        all_people = ["Tony", "Austin", "Cherry"],
        all_moods = ["calm", "happy", "sad", "anxious"],
        starting = "Hi, bro",
        length='S'
    )
    '''
    prompt.prompt_for_conversation_C(
        names = ["小白", "小黑"],
        location = "公园",
        topic = "如何种植一棵苹果树",
        descs = ["他是一位老师。", "他是一个医生。"],
        moods = ["稳定", "稳定"],
        memories = [["他刚刚做完作业。","他10年前是个歌手。"], ["他刚刚上完课。", "他曾经是一个舞蹈演员。"]],
        observations = "树、花、草",
        all_actions = ["对话","前往"],
        all_places = ["小白的家", "小黑的家", "公园"],
        all_people = ["小白", "小黑", "小灰"],
        all_moods = ["稳定", "开心", "伤心", "着急"],
        starting = "你好，兄弟们。",
        length = 'X'
    )
    '''
    #memory = ["Tony|Hey, how's it going? Talking about math homework, huh?|calm|calm|Action|chat|Player", "Austin|Hey, what's up? Math homework can be pretty time-consuming sometimes.|calm|calm|Action|chat|Player", "Player|Yeah, it's really taking up a lot of my time. I was wondering if you guys had any tips to make it go faster.|calm|calm|None|None", 'Tony|Well, as a teacher, my advice would be to break down the problem into smaller steps. It makes it easier to tackle and saves time in the long run.|calm|calm|Action|chat|Austin', "Austin|That's a great tip, Tony. Another thing that helps is to practice regularly. The more familiar you are with the concepts, the faster you'll be able to solve problems.|calm|calm|Action|chat|Tony", "Tony|Exactly, consistency is key. And don't forget to double-check your work before submitting it. It saves you from making careless mistakes or having to redo the whole thing.|calm|calm|None|None", "Austin|I couldn't agree more. And if you're feeling really stuck on a problem, don't hesitate to ask for help. Sometimes a fresh perspective can make all the difference.|calm|calm|None|None", "Tony|Absolutely. It's always a good idea to collaborate with classmates or seek guidance from your teacher.|calm|calm|Action|chat|Player", "Player|Thanks for the advice, guys. I'll definitely try implementing these strategies. Hopefully, it'll help me save some time and still get good grades.|calm|calm|None|None", "Tony|I'm sure it will, bro. Just keep practicing and stay organized.|calm|calm|None|None", 'Austin|Indeed, staying organized is crucial. Good luck with your math homework, and if you ever need any more tips, feel free to ask.|calm|calm|None|None', "Player|Thanks, I really appreciate it. I'll remember to reach out if I need any more help. Take care, guys.|calm|calm|None|None", 'Tony|You too, bro. Have a great day!|calm|calm|None|None', "Austin|You as well. Have a productive day, and don't forget to take breaks too.|calm|calm|None|None", 'Tony||calm|calm|Action|move|Park', '(Tony Exit. Remaining Characters : Player, Austin)', 'Austin||calm|calm|Action|move|Park', '(Austin Exit. Remaining Characters : Player)', '<EOC>']
    #prompt.prompt_for_re_creation('E',"I agree with you",memory)
    #prompt.prompt_for_topic(names = ["小明","小张"], location = "公园", observations = "树木、草、湖泊、石头", language = 'C')
    '''