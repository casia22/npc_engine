# -*- coding: utf-8 -*-
import openai
import json
import boto3
from npc_engine.src.config.config import OPENAI_KEY, OPENAI_BASE, OPENAI_MODEL, CONSOLE_HANDLER, FILE_HANDLER, PROJECT_ROOT_PATH, MEMORY_DB_PATH, CONFIG_PATH
# import zhipuai
# zhipuai.api_key = "3fe121b978f1f456cfac1d2a1a9d8c06.iQsBvb1F54iFYfZq"


"""
model_name = ['gpt-3.5-turbo-16k', 'cpm-bee]
"""
def get_model_answer(model_name, inputs_list):
    model = 'no activate model'
    answer = 'no answer'
    if model_name == 'gpt-3.5-turbo-16k':
        model = OPENAI(model_name)
        answer = model.get_response(inputs_list)
    elif model_name == 'cpm-bee':
        model = CPM_BEE()
        answer = model.get_response(inputs_list=inputs_list)
    return answer


class CPM_BEE:
    def __init__(self):
        self.client_name = 'sagemaker-runtime'
        self.client_region = 'us-west-2'
        self.aws_access_key_id = "AKIAQSLD5VQOWP3HFUHU"
        self.aws_secret_access_key = "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"
        self.endpoint_name = 'cpm-bee-230915134716SHWT'
        self.max_nex_tokens = 1024
        self.load_model()

    def load_model(self):
        self.sagemaker_runtime = boto3.client(self.client_name,
                                         region_name=self.client_region,
                                         aws_access_key_id=self.aws_access_key_id,
                                         aws_secret_access_key=self.aws_secret_access_key
                                         )

    def get_response(self, inputs_list):
        input_body = {
            "inputs": inputs_list,
            "parameters": {"max_new_tokens": self.max_nex_tokens, "repetition_penalty": 1.1, "temperature": 0.5}
        }

        response = self.sagemaker_runtime.invoke_endpoint(
            EndpointName=self.endpoint_name,
            Body=bytes(json.dumps(input_body), 'utf-8'),
            ContentType='application/json',
            Accept='application/json'
        )

        # json.load是指针
        obj_json = json.load(response['Body'])
        for re in obj_json['data']:
            return re['<ans>']
        return ''


class OPENAI:
    def __init__(self, model_name):
        self.api_base = OPENAI_BASE
        self.api_key =  OPENAI_KEY
        self.model_name = model_name
        self.max_tokens = 1024
        self.temperature = 0.5
        self.stop = None
        self.load_model()

    def load_model(self):
        openai.api_key = self.api_key
        openai.api_base = self.api_base

    def get_response(self, inputs_list):
        response = openai.ChatCompletion.create(model=self.model_name, messages=inputs_list)
        for re in response["choices"]:
            # succ, answer = re["message"]["content"].strip()
            # if succ:
            #     return answer
            return re["message"]["content"].strip()
        return ''


if __name__ == '__main__':
    inputs_list1 = [
        {
            "input": """
            <用户>请你扮演李大爷，特性是：李大爷是一个普通的种瓜老头，戴着文邹邹的金丝眼镜，喜欢喝茶，平常最爱吃烤烧鸡喝乌龙茶；上午他喜欢呆在家里喝茶，下午他会在村口卖瓜，晚上他会去瓜田护理自己的西瓜，心情是开心，正在李大爷家，现在时间是2021-01-01 12:00:00,
            你的最近记忆:
                8年前李大爷的两个徒弟在工厂表现优异都获得表彰。6年前从工厂辞职并过上普通的生活。4年前孩子看望李大爷并带上大爷最爱喝的乌龙茶。，
            你脑海中相关记忆: 
                15年前在工厂收了两个徒弟。，
            你当前的目的是:
                李大爷想去村口卖瓜，因为李大爷希望能够卖出新鲜的西瓜给村里的居民，让大家都能品尝到甜美可口的水果。
            请你根据mov执行以下步骤:
                1.根据以下[动作定义]选择出当前想执行的动作
                [动作定义]:
                'mov', 'definition': '某个位置移动'
                'get', 'definition': '获取某个物品'
                'put', 'definition': '将物品放置到某个物品或位置上'
                'chat', 'definition': '对某个人物说话'
                2.根据以下[动作可选参数以及例子]对第1步选择的动作选择参数
                [动作可选参数以及例子]:
                'mov', '参数1': ['李大爷家大门', '李大爷家后门', '李大爷家院子'],  '例子': '<mov|李大爷家门口|>'
                'get', '参数1': ['椅子#1', '椅子#2', '椅子#3[李大爷占用]', '床', '冰箱'], '例子': '<get|椅子#1|>'
                'put', '参数1': ['椅子#1', '椅子#2', '椅子#3[李大爷占用]', '床', '冰箱'], '参数2': ['西瓜'], '例子': '<put|冰箱|西瓜>'
                'chat', '参数1': ['王大妈', '村长', '隐形李飞飞'],'参数2': '你生成的对话', '例子': '<chat|王大妈|王大妈你吃了吗>'
                3.根据前两步选择的参数组合出<动作|参数1|参数2>的行为三元组，其中参数2可以省略
                举例:
                '例子': '<mov|李大爷家门口|>'
                '例子': '<get|椅子#1|>'
                '例子': '<put|冰箱|西瓜>'
                '例子': '<chat|王大妈|王大妈你吃了吗>'
            """.replace("<", "<<").replace(">", ">>"),
            "<ans>":""
        }
    ]

    inputs_list2 = [{
        "role": "system",
        "content": """
            请你扮演李大爷，特性是：李大爷是一个普通的种瓜老头，戴着文邹邹的金丝眼镜，喜欢喝茶，平常最爱吃烤烧鸡喝乌龙茶；上午他喜欢呆在家里喝茶，下午他会在村口卖瓜，晚上他会去瓜田护理自己的西瓜，心情是开心，正在李大爷家，现在时间是2021-01-01 12:00:00,
            你的最近记忆:8年前李大爷的两个徒弟在工厂表现优异都获得表彰。
            6年前从工厂辞职并过上普通的生活。
            4年前孩子看望李大爷并带上大爷最爱喝的乌龙茶。，
            你脑海中相关记忆:
            15年前在工厂收了两个徒弟。，
            你现在看到的人:['王大妈', '村长', '隐形李飞飞']，
            你现在看到的物品:['椅子#1', '椅子#2', '椅子#3[李大爷占用]', '床']，
            你现在看到的地点:['李大爷家大门', '李大爷家后门', '李大爷家院子']，
            你当前的目的是:李大爷想去村口卖瓜，因为李大爷希望能够卖出新鲜的西瓜给村里的居民，让大家都能品尝到甜美可口的水果。
        """},
        {
            "role": "user",
            "content": """
            请你根据[行为定义]以及你现在看到的事物生成一个完整的行为，并且按照<动作|参数1|参数2>的结构返回：
            行为定义：
                [{'name': 'mov', 'definition': ('<mov|location|>，向[location]移动',), 'example': ('<mov|卧室|>',)}, {'name': 'get', 'definition': ('<get|object1|object2>，从[object2]中获得[object1]，[object2]处可为空',), 'example': ('<get|西瓜|>，获得西瓜',)}, {'name': 'put', 'definition': ('<put|object1|object2>，把[object2]放入[object1]',), 'example': ('<put|冰箱|西瓜>',)}, {'name': 'chat', 'definition': ('<chat|person|content>，对[person]说话，内容是[content]',), 'example': ('<chat|李大爷|李大爷你吃了吗>，对李大爷说你吃了吗',)}]
            要求:
                1.请务必按照以下形式返回动作、参数1、参数2的三元组以及行为描述："<动作|参数1|参数2>, 行为的描述"
                2.动作和参数要在20字以内。
                3.动作的对象必须要属于看到的范围！
                4.三元组两侧必须要有尖括号<>
            """},
    ]

    inputs_list3 = [
        {"role": "system",
        "content": """
            请你扮演李大爷，特性是：李大爷是一个普通的种瓜老头，戴着文邹邹的金丝眼镜，喜欢喝茶，平常最爱吃烤烧鸡喝乌龙茶；上午他喜欢呆在家里喝茶，下午他会在村口卖瓜，晚上他会去瓜田护理自己的西瓜，心情是开心，正在李大爷家，现在时间是2021-01-01 12:00:00,
            你的最近记忆:
                8年前李大爷的两个徒弟在工厂表现优异都获得表彰。6年前从工厂辞职并过上普通的生活。4年前孩子看望李大爷并带上大爷最爱喝的乌龙茶。，
            你脑海中相关记忆: 
                15年前在工厂收了两个徒弟。，
            你当前的目的是:
                李大爷想去村口卖瓜，因为李大爷希望能够卖出新鲜的西瓜给村里的居民，让大家都能品尝到甜美可口的水果。
        """},
        {"role": "user",
         "content": """
         请你根据记忆以及目的执行以下步骤来生成完整的行为:
        1.根据以下[动作定义]选择出当前想执行的动作
            [动作定义]:
            'mov', 'definition': '某个位置移动'
            'get', 'definition': '获取某个物品'
            'put', 'definition': '将物品放置到某个物品或位置上'
            'chat', 'definition': '对某个人物说话'
        2.根据以下[动作可选参数以及例子]对第1步选择的动作选择参数
            [动作可选参数以及例子]:
            'mov', '参数1': ['李大爷家大门', '李大爷家后门', '李大爷家院子'],  '例子': '<mov|李大爷家门口|>'
            'get', '参数1': ['椅子#1', '椅子#2', '椅子#3[李大爷占用]', '床', '冰箱'], '例子': '<get|椅子#1|>'
            'put', '参数1': ['椅子#1', '椅子#2', '椅子#3[李大爷占用]', '床', '冰箱'], '参数2': ['西瓜'], '例子': '<put|冰箱|西瓜>'
            'chat', '参数1': ['王大妈', '村长', '隐形李飞飞'],'参数2': '你生成的对话', '例子': '<chat|王大妈|王大妈你吃了吗>'
        3.根据前两步选择的参数组合出<动作|参数1|参数2>的行为三元组，其中参数2可以省略
            举例:
            '例子': '<mov|李大爷家门口|>'
            '例子': '<get|椅子#1|>'
            '例子': '<put|冰箱|西瓜>'
            '例子': '<chat|王大妈|王大妈你吃了吗>'
        """.replace("<", "<<").replace(">", ">>"),
        }]

    print(get_model_answer(model_name='cpm-bee', inputs_list=inputs_list1))
    # print(get_model_answer(model_name='gpt-3.5-turbo-16k', inputs_list=inputs_list3))

