# -*- coding: utf-8 -*-
import openai
import json
import requests
import json
import requests
import io
import boto3
import time
import os
from typing import List, Optional
def get_model_answer(model_name, inputs_list, stream=False):
    """
    新增qwen和GLM3_6B,qwen已测试完毕

    """
    model = None
    answer = 'no answer'

    if model_name == 'gpt-3.5-turbo-16k':
        model = OPENAI(model_name)
    elif model_name == 'cpm-bee':
        model = CPM_BEE()
    elif model_name == 'baidu-wxyy':
        model = BAIDU_API()
    elif model_name == 'baichuan2-13b-4bit':
        model = BaiChuan2()
    elif model_name == 'glm3-6b':
        model = GLM3_6B()
    elif model_name == 'qwen':
        model = QWEN()

    if model:
        answer = model.get_response(inputs_list, stream=stream)
    else:
        answer = 'Model not recognized'

    return answer




BAIDU_API_CONFIG = {

    "API_KEY": "qq7WLVgNX88unRoUVLtNz8fQ",
    "SECRET_KEY": "gA3VOdcRnGM4gKKkKKi93A79Dwevm3zo",  # gA3VOdcRnGM4gKKkKKi93A79Dwevm3zo
    "API_BASE": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/eb-instant?access_token=",
    "URL": "https://aip.baidubce.com/oauth/2.0/token",
    'ACCESS_TOKEN': None
}
CPM_BEE_API_CONFIG = {
    "CLIENT_NAME": 'sagemaker-runtime',
    "CLIENT_REGION": 'us-west-2',
    "AWS_ACCESS_KEY_ID": "AKIAQSLD5VQOWP3HFUHU",
    "AWS_SECRET_ACCESS_KEY": "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",
    "ENDPOINT_NAME": 'cpm-bee-230915134716SHWT',
    "MAX_NEW_TOKENS": 1024
}
BAICHUAN2_CONFIG = {
    "REGION_NAME": "us-east-1",
    "ACCESS_KEY": "AKIAQ33DL5YJDAN2VH4L",
    "SECRET_KEY": "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",
    "ENDPOINT_NAME": "bc2-13b-stream-2023-10-22-11-39-50-913-endpoint",
    "MAX_LENGTH": 1024,
    "TEMPERATURE": 0.1,
    "TOP_P": 0.8
}
OPENAI_KEY = "sk-hJs89lkQMzlzoOcADb6739A9091d41229c2c3c0547932fBe"
OPENAI_BASE = "https://api.qaqgpt.com/v1"
OPENAI_CONFIG = {
    "API_BASE": OPENAI_BASE,
    "API_KEY": OPENAI_KEY,
    "MAX_TOKENS": 1024,
    "TEMPERATURE": 0.5,
    "STOP": None
}
QWEN_CONFIG = {
    "API_BASE": "http://localhost:5001/v1",
    "API_KEY": "None",
}
GLM3_6B_CONFIG={
    "API_BASE":"http://127.0.0.1:5001",
}

# import zhipuai
# zhipuai.api_key = "3fe121b978f1f456cfac1d2a1a9d8c06.iQsBvb1F54iFYfZq"


"""
model_name = ['gpt-3.5-turbo-16k', 'cpm-bee]
"""


class StreamScanner:
    """
    A helper class for parsing the InvokeEndpointWithResponseStream event stream.

    The output of the model will be in the following format:
    ```
    b'{"outputs": [" a"]}\n'
    b'{"outputs": [" challenging"]}\n'
    b'{"outputs": [" problem"]}\n'
    ...
    ```

    While usually each PayloadPart event from the event stream will contain a byte array
    with a full json, this is not guaranteed and some of the json objects may be split across
    PayloadPart events. For example:
    ```
    {'PayloadPart': {'Bytes': b'{"outputs": '}}
    {'PayloadPart': {'Bytes': b'[" problem"]}\n'}}
    ```

    This class accounts for this by concatenating bytes written via the 'write' function
    and then exposing a method which will return lines (ending with a '\n' character) within
    the buffer via the 'readlines' function. It maintains the position of the last read
    position to ensure that previous bytes are not exposed again.
    """

    def __init__(self):
        self.buff = io.BytesIO()
        self.read_pos = 0

    def write(self, content):
        self.buff.seek(0, io.SEEK_END)
        self.buff.write(content)

    def readlines(self):
        self.buff.seek(self.read_pos)
        for line in self.buff.readlines():
            if line[-1] != b'\n':
                self.read_pos += len(line)
                yield line[:-1]

    def reset(self):
        self.read_pos = 0


class BaseModel:
    def get_response(self, inputs_list):
        raise NotImplementedError


class BAIDU_API:
    # DOC: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/4lilb2lpf
    # 充值: https://console.bce.baidu.com/billing/#/account/index
    # 开通新模型: https://console.bce.baidu.com/qianfan/chargemanage/list

    def __init__(self, config=BAIDU_API_CONFIG):
        self.api_key = config['API_KEY']
        self.secret_key = config['SECRET_KEY']
        self.api_base = config['API_BASE']
        self.access_token = self.get_access_token()

    def convert_openai_to_baidu(self, inputs_list):
        combined_content = '\n\n'.join(item['content'].strip() for item in inputs_list)
        baidu_inputs_list = [{"role": "user", "content": combined_content}]
        return baidu_inputs_list

    def get_response(self, inputs_list, stream=False):
        url = self.api_base + self.access_token
        payload = json.dumps({
            "messages": self.convert_openai_to_baidu(inputs_list),
            "temperture": "0",
            "stream": stream
        })
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.request("POST", url, headers=headers, data=payload, stream=stream)

        if stream:
            return self._handle_stream_response(response)
        else:
            return self._handle_standard_response(response)

    def _handle_standard_response(self, response):
        data = json.loads(response.text)
        return data.get("result", "")

    def _handle_stream_response(self, response):
        total_response = ""
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                try:
                    response_json = json.loads(decoded_line)
                    content = response_json.get("result", "")
                    total_response += content
                except Exception as e:
                    print(f"Error in stream response: {e}")
                    continue
        return total_response

    def get_access_token(self):
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {"grant_type": "client_credentials", "client_id": self.api_key, "client_secret": self.secret_key}
        response = requests.post(url, params=params)
        return response.json().get("access_token", "")


class CPM_BEE:
    def __init__(self, config=CPM_BEE_API_CONFIG):
        self.client_name = config['CLIENT_NAME']
        self.client_region = config['CLIENT_REGION']
        self.aws_access_key_id = config['AWS_ACCESS_KEY_ID']
        self.aws_secret_access_key = config['AWS_SECRET_ACCESS_KEY']
        self.endpoint_name = config['ENDPOINT_NAME']
        self.max_new_tokens = config['MAX_NEW_TOKENS']
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
            "parameters": {"max_new_tokens": self.max_new_tokens, "repetition_penalty": 1.1, "temperature": 0.5}
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


class BaiChuan2:
    def __init__(self, config=BAICHUAN2_CONFIG):
        self.endpoint = f"https://runtime.sagemaker.{config['REGION_NAME']}.amazonaws.com/endpoints/{config['ENDPOINT_NAME']}/invocations"
        self.parameters = {
            "max_length": config["MAX_LENGTH"],
            "temperature": config["TEMPERATURE"],
            "top_p": config["TOP_P"]
        }
        self.smr_client = boto3.client(
            "sagemaker-runtime",
            aws_access_key_id=config["ACCESS_KEY"],
            aws_secret_access_key=config["SECRET_KEY"],
            region_name=config["REGION_NAME"]
        )
        self.stream_scanner = StreamScanner()

    def get_response(self, inputs_list: List[str], stream: bool = False) -> str:
        return self.call_baichuan2(prompt=inputs_list[0], history=[], stream=stream)

    def call_baichuan_no_stream(self, prompt: str, history: List[str] = []) -> str:
        endpoint_name = 'bc2-13b-stream-2023-10-22-11-39-50-913-endpoint'
        start = time.time()
        response_model = self.smr_client.invoke_endpoint_with_response_stream(
            EndpointName=endpoint_name,
            Body=json.dumps(
                {
                    "inputs": prompt,
                    "parameters": self.parameters,
                    "history": history,
                    "stream": True
                }
            ),
            ContentType="application/json",
        )

        event_stream = response_model['Body']
        scanner = self.stream_scanner
        total_response = ""
        for event in event_stream:
            scanner.write(event['PayloadPart']['Bytes'])
            for line in scanner.readlines():
                try:
                    resp = json.loads(line)
                    word_slice = resp.get("outputs")['outputs']
                    total_response += word_slice
                except Exception as e:
                    import traceback
                    print(traceback.format_exc())
                    continue
        return total_response

    def call_baichuan2_stream(self, prompt: str, history: List[str] = []) -> Optional[str]:
        endpoint_name = 'bc2-13b-stream-2023-10-22-11-39-50-913-endpoint'
        start = time.time()
        response_model = self.smr_client.invoke_endpoint_with_response_stream(
            EndpointName=endpoint_name,
            Body=json.dumps(
                {
                    "inputs": prompt,
                    "parameters": self.parameters,
                    "history": history,
                    "stream": True
                }
            ),
            ContentType="application/json",
        )

        event_stream = response_model['Body']
        scanner = self.stream_scanner
        total_response = ""
        for event in event_stream:
            scanner.write(event['PayloadPart']['Bytes'])
            for line in scanner.readlines():
                try:
                    resp = json.loads(line)
                    word_slice = resp.get("outputs")['outputs']
                    total_response += word_slice
                    # 如果是stream模式，那么返回一个迭代器
                    yield word_slice
                except Exception as e:
                    import traceback
                    print(traceback.format_exc())
                    continue
        return total_response

    def call_baichuan2(self, prompt: str, history: List[str] = [], stream: bool = False) -> str:
        if stream:
            return self.call_baichuan2_stream(prompt, history)
        return self.call_baichuan_no_stream(prompt, history)


class OPENAI:
    def __init__(self, model_name, config=OPENAI_CONFIG):
        self.api_base = config["API_BASE"]
        self.api_key = config["API_KEY"]
        self.model_name = model_name
        self.max_tokens = config["MAX_TOKENS"]
        self.temperature = config["TEMPERATURE"]
        self.stop = config["STOP"]
        self.load_model()

    def load_model(self):
        openai.api_key = self.api_key
        openai.api_base = self.api_base

    def get_response(self, inputs_list, stream=False):
        try:
            response = openai.ChatCompletion.create(
                model=self.model_name,
                messages=inputs_list,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stop=self.stop,
                stream=stream
            )

            if not stream:
                return next((re["message"]["content"].strip() for re in response["choices"] if
                             re["message"]["content"].strip()), '')

            # 处理流式传输
            collected_chunks = []
            collected_messages = []
            for chunk in response:
                chunk_message = chunk['choices'][0]['delta']
                collected_chunks.append(chunk)
                collected_messages.append(chunk_message)

            full_reply_content = ''.join([m.get('content', '') for m in collected_messages])
            return full_reply_content
        except Exception as e:
            print(f"Error in OPENAI.get_response: {str(e)}")
            return ''


class QWEN:
    def __init__(self, api_base="http://localhost:5001/v1", api_key="none"):
        self.model_name = "Qwen"
        self.api_base = api_base
        self.api_key = api_key
        self.load_model()

    def load_model(self):
        openai.api_key = self.api_key
        openai.api_base = self.api_base

    def get_response(self, inputs_list, stream=False):
        try:
            formatted_inputs = self._format_inputs(inputs_list)
            response = openai.ChatCompletion.create(
                model=self.model_name,
                messages=formatted_inputs,
                stream=stream
            )

            if stream:
                return self._handle_stream_response(response)
            else:
                return self._handle_standard_response(response)
        except Exception as e:
            print(f"Error in QWEN.get_response: {str(e)}")
            return ''

    def _handle_standard_response(self, response):
        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content.strip()
        return ''

    def _handle_stream_response(self, response):
        total_response = ""
        for chunk in response:
            if hasattr(chunk.choices[0].delta, "content"):
                total_response += chunk.choices[0].delta.content
        return total_response

    def _format_inputs(self, inputs_list):
        # 将 system 和 user 内容合并
        combined_content = "\n".join(item["content"] for item in inputs_list if item["role"] in ["system", "user"])
        return [{"role": "user", "content": combined_content}]


class GLM3_6B:
    def __init__(self, base_url=GLM3_6B_CONFIG['API_BASE'], model_name="chatglm3-6b"):
        self.base_url = base_url
        self.model_name = model_name

    def get_response(self, messages: List[dict], stream: bool = False, max_tokens: int = 2048, temperature: float = 0.8,
                     top_p: float = 0.8) -> str:
        data = {
            "model": self.model_name,
            "messages": messages,
            "stream": stream,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p
        }

        response = requests.post(f"{self.base_url}/v1/chat/completions", json=data, stream=stream)
        if response.status_code == 200:
            if stream:
                return self._handle_stream_response(response)
            else:
                return self._handle_standard_response(response)
        else:
            print("Error:", response.status_code)
            return ''

    def _handle_standard_response(self, response):
        decoded_line = response.json()
        content = decoded_line.get("choices", [{}])[0].get("message", {}).get("content", "")
        return content

    def _handle_stream_response(self, response):
        total_response = ""
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')[6:]
                try:
                    response_json = json.loads(decoded_line)
                    content = response_json.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    total_response += content
                except:
                    print("Special Token:", decoded_line)
        return total_response





if __name__ == '__main__':
    inputs_list_cpm = [
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
            "<ans>": ""
        }
    ]

    inputs_list_openai = [{
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
                5.以一行的方式，返回单个结果
            """},
    ]

    inputs_list_cpm = [
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
    inputs_list_qwen = [
        {
        "role": "user",
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
            请你根据[行为定义]以及你现在看到的事物生成一个完整的行为，并且按照<动作|参数1|参数2>的结构返回：
            行为定义：
                [{'name': 'mov', 'definition': ('<mov|location|>，向[location]移动',), 'example': ('<mov|卧室|>',)}, {'name': 'get', 'definition': ('<get|object1|object2>，从[object2]中获得[object1]，[object2]处可为空',), 'example': ('<get|西瓜|>，获得西瓜',)}, {'name': 'put', 'definition': ('<put|object1|object2>，把[object2]放入[object1]',), 'example': ('<put|冰箱|西瓜>',)}, {'name': 'chat', 'definition': ('<chat|person|content>，对[person]说话，内容是[content]',), 'example': ('<chat|李大爷|李大爷你吃了吗>，对李大爷说你吃了吗',)}]
            要求:
                1.请务必按照以下形式返回动作、参数1、参数2的三元组以及行为描述："<动作|参数1|参数2>, 行为的描述"
                2.动作和参数要在20字以内。
                3.动作的对象必须要属于看到的范围！
                4.三元组两侧必须要有尖括号<>
                5.以一行的方式，返回单个结果
            """},
    ]
    print(get_model_answer(model_name='qwen', inputs_list=inputs_list_openai, stream=False))

    # print(get_model_answer(model_name='gpt-3.5-turbo-16k', inputs_list=inputs_list3))
