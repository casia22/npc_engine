import openai
import json

openai.api_key = 'sk-qvpKnoiDugYFOJbLC48e68E26a9e4510Ad779096Fd2019Fd'
openai.api_base = 'https://apic3.a1r.cc/v1'


# Example dummy function hard coded to return the same weather
# In production, this could be your backend API or an external API
def get_current_weather(location, unit="fahrenheit"):
    """Get the current weather in a given location"""
    if "tokyo" in location.lower():
        return json.dumps({"location": "Tokyo", "temperature": "10", "unit": unit})
    elif "san francisco" in location.lower():
        return json.dumps({"location": "San Francisco", "temperature": "72", "unit": unit})
    elif "paris" in location.lower():
        return json.dumps({"location": "Paris", "temperature": "22", "unit": unit})
    else:
        return json.dumps({"location": location, "temperature": "unknown"})


def get_action_response(player_name, player_speech, items_visible, player_state_desc, time, fail_safe, k=3):
    return


def run_conversation():
    # Step 1: send the conversation and available functions to the model
    messages = [{"role": "user", "content": "What's the weather like in San Francisco, Tokyo, and Paris?"}]
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_current_weather",
                "description": "Get the current weather in a given location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA",
                        },
                        "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                    },
                    "required": ["location"],
                },
            },
        }
    ]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0125",
        messages=messages,
        tools=tools,
        tool_choice="auto",  # auto is default, but we'll be explicit
    )
    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls
    print(response_message)

    print("-------------------")
    # Step 2: check if the model wanted to call a function
    if tool_calls:
        # Step 3: call the function
        # Note: the JSON response may not always be valid; be sure to handle errors
        available_functions = {
            "get_current_weather": get_current_weather,
        }  # only one function in this example, but you can have multiple
        messages.append(response_message)  # extend conversation with assistant's reply
        # Step 4: send the info for each function call and function response to the model
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            function_response = function_to_call(
                location=function_args.get("location"),
                unit=function_args.get("unit"),
            )

            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                }
            )  # extend conversation with function response
        second_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0125",
            messages=messages,
        )  # get a new response from the model where it can see the function response
        return second_response


import requests
import json
import requests


def get_stable_access_token(appid, secret):
    url = "https://api.weixin.qq.com/cgi-bin/stable_token"
    payload = {
        "grant_type": "client_credential",
        "appid": appid,
        "secret": secret
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print(response.json()['access_token'])
        return response.json()['access_token']
    else:
        print('Failed to retrieve stable access token')
        return None


def post_wechat_api(access_token, service, api, data, client_msg_id):
    url = f"https://api.weixin.qq.com/wxa/servicemarket?access_token={access_token}"
    payload = {
        "service": service,
        "api": api,
        "data": data,
        "client_msg_id": client_msg_id,
        "async": False
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        return {'error': 'Failed to post data to WeChat API', 'status_code': response.status_code}


# Parameters
appid = "wxb87e628eaf9e5937"
secret = "ef109bcad4dcc0c83cada824e2b202d9"
service = "wx617ea32f889ba259"
api = "BaichuanNPCTurbo"
data = {
    "character_profile": {
        "character_name": "孙悟空",
        "character_info": "孙悟空",
        "user_name": "孙悟空",
        "user_info": "孙悟空"
    },
    "messages": [
        {
            "role": "user",
            "content": "霁云，你可以空手接白刃吗？"
        }
    ],
    "temperature": 0.8,
    "top_k": 10,
    "max_tokens": 512
}
client_msg_id = "id42379554"

# Execution
access_token = get_stable_access_token(appid, secret)
if access_token:
    response = post_wechat_api(access_token, service, api, data, client_msg_id)
    print(response)
else:
    print("Error retrieving the access token.")

import requests

# 定义您的appid和secret
appid = 'wxb87e628eaf9e5937'
secret = 'ef109bcad4dcc0c83cada824e2b202d9'

# 获取access_token的URL
token_url = 'https://api.weixin.qq.com/cgi-bin/token'

# 发送GET请求获取access_token
response = requests.get(token_url, params={'grant_type': 'client_credential', 'appid': appid, 'secret': secret})
if response.status_code == 200:
    token_data = response.json()
    if 'access_token' in token_data:
        access_token = token_data['access_token']
        print("获取到的access_token:", access_token)
    else:
        print("获取access_token失败:", token_data)
        exit()

# 发送POST请求到服务市场的URL
service_market_url = f'https://api.weixin.qq.com/wxa/servicemarket?access_token={access_token}'

# 构建要发送到服务市场的数据
service_data = {
    "service": "wx617ea32f889ba259",  # Service ID
    "api": "BaichuanNPCTurbo",  # API名称
    "data": {
        "character_profile": {
            "character_name": "孙悟空",
            "character_info": "孙悟空",
            "user_name": "孙悟空",
            "user_info": "孙悟空"
        },
        "messages": [
            {
                "role": "user",
                "content": "霁云，你可以空手接白刃吗？"
            }
        ],
        "temperature": 0.8,
        "top_k": 10,
        "max_tokens": 512
    },
    "client_msg_id": "id123"
}

# 发送POST请求到服务市场
service_response = requests.post(service_market_url, json=service_data)

# 检查响应状态码
if service_response.status_code == 200:
    print("服务市场请求成功！")
    print("响应内容:", service_response.json())
else:
    print("服务市场请求失败，状态码：", service_response.status_code)
    print("错误信息：", service_response.text)
