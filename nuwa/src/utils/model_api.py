# -*- coding: utf-8 -*-
import json
import os
import random
import time
from pathlib import Path

import google.generativeai as genai
import openai
import requests

# import zhipuai
# zhipuai.api_key = "3fe121b978f1f456cfac1d2a1a9d8c06.iQsBvb1F54iFYfZq"


"""
model_name = ['gpt-3.5-turbo-16k', 'cpm-bee]
"""


def get_model_answer(model_name, inputs_list, project_root_path,  stream=False):
    PROJECT_ROOT_PATH = project_root_path  # 用户输入的项目根目录
    # 读取LLM_CONFIG

    answer = 'no answer'
    if model_name == 'gpt-3.5-turbo-16k':
        model = OPENAI(model_name, project_root_path=project_root_path)
        answer = model.get_response(inputs_list, stream=stream)
    elif model_name == 'baidu-wxyy':
        model = BAIDU_API()
        answer = model.get_response(inputs_list=inputs_list)
    elif model_name == 'gemini-pro':
        model = GEMINI(model_name, project_root_path=project_root_path)
        answer = model.get_response(inputs_list)
    return answer


class BAIDU_API:
    # DOC: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/4lilb2lpf
    # 充值: https://console.bce.baidu.com/billing/#/account/index
    # 开通新模型: https://console.bce.baidu.com/qianfan/chargemanage/list

    def __init__(self):
        API_KEY = "qq7WLVgNX88unRoUVLtNz8fQ"  # qq7WLVgNX88unRoUVLtNz8fQ
        SECRET_KEY = "gA3VOdcRnGM4gKKkKKi93A79Dwevm3zo"  # gA3VOdcRnGM4gKKkKKi93A79Dwevm3zo
        self.access_token = None
        self.api_key = API_KEY
        self.secret_key = SECRET_KEY
        self.api_base = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/eb-instant?access_token="
        self.get_access_token()

    def convert_openai_to_baidu(self, inputs_list):
        """
        将 OpenAI 的输入转换为百度的输入
        检测是否为偶数，如果为偶数，那就把system拼接到user上面

        :param inputs_list: OpenAI 的输入
        :return: 百度的输入
        """
        combined_content = '\n\n'.join(item['content'].strip() for item in inputs_list)
        baidu_inputs_list = [{"role": "user", "content": combined_content}]
        return baidu_inputs_list

    def get_response(self, inputs_list):
        self.url = self.api_base + self.access_token
        payload = json.dumps({
            "messages": self.convert_openai_to_baidu(inputs_list),
            "temperture": "0"
        })
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.request("POST", self.url, headers=headers, data=payload)
        # load json data
        data = json.loads(response.text)
        response = data["result"]
        return response

    def get_access_token(self):
        """
        使用 AK，SK 生成鉴权签名（Access Token）
        :return: access_token，或是None(如果错误)
        """
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {"grant_type": "client_credentials", "client_id": self.api_key, "client_secret": self.secret_key}
        self.access_token = str(requests.post(url, params=params).json().get("access_token"))
        return self.access_token


class OPENAI:
    def __init__(self, model_name, project_root_path):
        self.PROJECT_ROOT_PATH = Path(project_root_path)
        self.CONFIG_PATH = self.PROJECT_ROOT_PATH / "config"
        # 读取LLM_CONFIG
        OPENAI_CONFIG_PATH = self.CONFIG_PATH / "llm_config.json"
        openai_config_data = json.load(open(OPENAI_CONFIG_PATH, "r"))
        self.keys_bases = openai_config_data["OPENAI_CONFIG"]["OPENAI_KEYS_BASES"]
        self.current_key_index = 0  # 初始索引
        self.api_key, self.api_base = self.keys_bases[self.current_key_index]["OPENAI_KEY"], \
        self.keys_bases[self.current_key_index]["OPENAI_BASE"]

        self.model_name = model_name
        self.max_tokens = openai_config_data["OPENAI_CONFIG"]["OPENAI_MAX_TOKENS"]
        self.temperature = openai_config_data["OPENAI_CONFIG"]["OPENAI_TEMPERATURE"]
        self.stop = None
        self.load_model()

    def load_model(self):
        openai.api_key = self.api_key
        openai.api_base = self.api_base

    def switch_api_key(self):
        self.current_key_index = (self.current_key_index + 1) % len(self.keys_bases)
        new_key_base = self.keys_bases[self.current_key_index]
        self.api_key, self.api_base = new_key_base["OPENAI_KEY"], new_key_base["OPENAI_BASE"]
        self.load_model()
        print(f"Switched to new API key and base: {self.api_key}, {self.api_base}")

    def get_response(self, inputs_list, stream=False, max_retries=3):
        attempt = 0
        while attempt < max_retries:
            try:
                if stream:
                    print("----- Streaming Request -----")
                    stream_response = openai.ChatCompletion.create(
                        model=self.model_name,
                        messages=inputs_list,
                        stream=True,
                    )
                    return stream_response
                else:
                    response = openai.ChatCompletion.create(
                        model=self.model_name,
                        messages=inputs_list,
                        max_tokens=self.max_tokens,
                        temperature=self.temperature,
                        stop=self.stop
                    )
                    print(response.choices[0].message["content"].strip())
                    return response.choices[0].message["content"].strip()
            except Exception as e:
                attempt += 1
                print(f"Attempt {attempt} failed with error: {e}")
                if attempt < max_retries:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)  # Exponential backoff with jitter
                    print(f"Waiting {wait_time:.2f} seconds before retrying...")
                    time.sleep(wait_time)
                    self.switch_api_key()  # Optionally switch API key before retrying
                else:
                    return "An error occurred, and the request could not be completed after retries."


class GEMINI:
    def __init__(self, model_name, project_root_path):
        self.PROJECT_ROOT_PATH = Path(project_root_path)
        self.CONFIG_PATH = self.PROJECT_ROOT_PATH / "config"
        # 读取配置
        GEMINI_CONFIG_PATH = self.CONFIG_PATH / "llm_config.json"
        gemini_config_data = json.load(open(GEMINI_CONFIG_PATH, "r"))
        self.api_keys = gemini_config_data["GEMINI_CONFIG"]["GEMINI_KEYS"]
        self.api_usage_limit = gemini_config_data["GEMINI_CONFIG"].get("API_USAGE_LIMIT", 1000)
        self.api_usage = {key: 0 for key in self.api_keys}  # 初始化每个key的使用次数
        self.temperature = gemini_config_data["GEMINI_CONFIG"]["GEMINI_TEMPERATURE"]
        self.model_name = model_name
        self.model = genai.GenerativeModel(self.model_name)
        self.proxy = gemini_config_data["GEMINI_CONFIG"].get("PROXY", {"http": "", "https": ""})
        self.current_api_key_index = 0  # 初始索引
        self.configure_api(self.api_keys[self.current_api_key_index])
        self.max_tokens = gemini_config_data["GEMINI_CONFIG"]["GEMINI_MAX_TOKENS"]

    def configure_api(self, api_key):
        os.environ["HTTP_PROXY"] = self.proxy["http"]
        os.environ["HTTPS_PROXY"] = self.proxy["https"]
        genai.configure(api_key=api_key)

    def switch_api_key(self):
        self.current_api_key_index = (self.current_api_key_index + 1) % len(self.api_keys)
        self.configure_api(self.api_keys[self.current_api_key_index])
        print(f"Switched to new API key: {self.api_keys[self.current_api_key_index]}")

    def get_response(self, inputs_list):
        messages = []

        # 分别处理用户和模型的部分，确保不会添加空的内容到parts中
        user_parts = [input["content"] for input in inputs_list if
                      input["role"] in ["system", "user"] and input["content"]]
        if user_parts:  # 只有当有用户部分时才添加
            messages.append({'role': 'user', 'parts': user_parts})

        model_parts = [input["content"] for input in inputs_list if input["role"] == "assistant" and input["content"]]
        for part in model_parts:  # 对于模型的每一部分，分别添加
            messages.append({'role': 'model', 'parts': [part]})

        for retries in range(5):
            try:
                response = self.model.generate_content(messages, generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature, max_output_tokens=self.max_tokens))
                answer = response.text

                # 更新API key使用次数并检查是否需要切换
                self.api_usage[self.api_keys[self.current_api_key_index]] += 1
                if self.api_usage[self.api_keys[self.current_api_key_index]] >= self.api_usage_limit:
                    self.switch_api_key()

                return answer
            except Exception as e:
                print(f"Error when calling the GEMINI API: {e}")
                if retries < 4:
                    print("Attempting to switch API key and retry...")
                    self.switch_api_key()
                else:
                    print("Maximum number of retries reached. The GEMINI API is not responding.")
                    return "I'm sorry, but I am unable to provide a response at this time due to technical difficulties."
                sleep_time = (2 ** retries) + random.random()
                print(f"Waiting for {sleep_time} seconds before retrying...")
                time.sleep(sleep_time)


if __name__ == '__main__':
    PROJECT_ROOT_PATH = Path(os.path.abspath(__file__)).parents[3] / "example_project"
    # path: C:\python_code\npc_engine-main\example_project
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

    # print(get_model_answer(model_name='gemini-pro', inputs_list=inputs_list_openai,project_root_path=PROJECT_ROOT_PATH))
    print(get_model_answer(model_name='gpt-3.5-turbo-16k', inputs_list=inputs_list_openai,
                           project_root_path=PROJECT_ROOT_PATH))