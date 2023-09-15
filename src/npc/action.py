import json
from typing import List, Dict, Any, Tuple
import re


class ActionItem:
    def __init__(self, name: str, definition: str, example: str, log_template:Dict[str, str], multi_param:bool=False):
        self.name = name
        self.definition = definition
        self.multi_param = multi_param
        self.example = example
        self.log_template = log_template
        """
        log_template的例子：
        {npc_name} 成功地从{object}获得{parameters}
        {npc_name} 未能从{object}获得{parameters}。原因：{reason}
        """

    @staticmethod
    def str2json(string:str)->Dict[str, Any]:
        """
        从字符串中提取动作和参数
        :param string:
        :return: Dict[str, Any]
        """
        string = string.replace('｜', '|').replace('，', ',')
        pattern = r'<(.*?)\|(.*?)\|(.*?)>'
        match = re.search(pattern, string)
        if match:
            action = match.group(1).strip()
            obj = match.group(2).strip()
            params = [param.strip() for param in match.group(3).split(',')]
            return {'action': action, 'object': obj, 'parameters': params}
        else:
            return {'action': "", 'object': "", 'parameters': ""}


    def get_log(self, npc_name:str, obj:str, parameters:List[str], reason:str)->str:
        """
        使用其日志模版，转换为自然语言记录在记忆中，方便语义检索
        输出例：
            李大爷成功 从 箱子 拿取 西瓜汁,桃子,枕头
            李大爷未能 从 箱子 拿取 西瓜汁,桃子,枕头。原因：箱子里没有西瓜汁

            李大爷成功 打开 门
            李大爷未能 打开 门。原因：门已经打开了

            李大爷成功 使用 刀 砍 西瓜
            李大爷未能 使用 刀 砍 西瓜。原因：附近没有西瓜
        log_template的例子：
            {npc_name}成功地从{object}获得{parameters}
            {npc_name}未能从{object}获得{parameters}。原因：{reason}
        """
        if reason:
            return self.log_template['fail'].format(npc_name=npc_name, object=obj,
                                                    parameters=','.join(parameters), reason=reason)

        return self.log_template['success'].format(npc_name=npc_name,object=obj,
                                                   parameters=','.join(parameters))
