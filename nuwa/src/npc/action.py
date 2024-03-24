import json
from typing import List, Dict, Any, Tuple
import re


class ActionItem:
    def __init__(self, name: str, definition: str, example: str, log_template: Dict[str, str],
                 multi_param: bool = False):
        self.name = name
        self.definition = definition
        self.multi_param = multi_param
        self.example = example
        self.log_template = log_template
        self.vec = ""
        """
        log_template的例子：
        {npc_name} 成功地从{object}获得{parameters}
        {npc_name} 未能从{object}获得{parameters}。原因：{reason}
        """

    @staticmethod
    def str2json(string: str) -> Dict[str, Any]:
        """
        从字符串中提取动作和参数
        :param string:
        :return: Dict[str, Any]
        """
        string = string.replace('｜', '|').replace('，', ',')
        print(string)
        # 使用两种正则表达式，一种匹配带 <> 的形式，一种匹配无 <> 的形式
        pattern_with_angle_brackets = r'<(\w+)\|([^|]+)\|?([^|>]*)>'
        pattern_without_angle_brackets = r'(\w+)\|([^|]+)\|?([^|]*)'

        # 尝试匹配带 <> 的形式
        matches_with_angle_brackets = re.findall(pattern_with_angle_brackets, string)
        if matches_with_angle_brackets:
            function_name, obj, param = matches_with_angle_brackets[0]
            return {'action': function_name, 'object': obj, 'parameters': param.split(',')}

        # 如果带 <> 的形式没有匹配到，则尝试匹配无 <> 的形式
        matches_without_angle_brackets = re.findall(pattern_without_angle_brackets, string)
        if matches_without_angle_brackets:
            function_name, obj, param = matches_without_angle_brackets[0]
            return {'action': function_name, 'object': obj, 'parameters': param.split(',')}

        return {'action': "", 'object': "", 'parameters': ""}

    def get_log(self, action_status: str, npc_name: str, obj: str, parameters: List[str], reason: str) -> str:
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
        # 若动作处理成功就不加载reason
        if action_status == "success":
            return self.log_template['success'].format(npc_name=npc_name, object=obj,
                                                       parameters=','.join(parameters))

        return self.log_template['fail'].format(npc_name=npc_name, object=obj,
                                                parameters=','.join(parameters), reason=reason)
