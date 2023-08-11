import zhipuai
from zhipuai.model_api import ChatGLM6bParams

zhipuai.api_key = ""


def invoke_example():
    params = ChatGLM6bParams(
        prompt=[{"role": "user", "content": "人工智能"}], top_p=0.7, temperature=0.9
    )
    response = zhipuai.model_api.invoke(**params.asdict())
    print(response)


def async_invoke_example():
    params = ChatGLM6bParams(
        prompt=[{"role": "user", "content": "人工智能"}], top_p=0.7, temperature=0.9
    )
    response = zhipuai.model_api.async_invoke(**params.asdict())
    print(response)


"""
    说明：
    add: 事件流开启
    error: 平台服务或者模型异常，响应的异常事件
    interrupted: 中断事件，例如：触发敏感词
    finish: 数据接收完毕，关闭事件流
"""


def sse_invoke_example():
    params = ChatGLM6bParams(
        prompt=[{"role": "user", "content": "人工智能"}], top_p=0.7, temperature=0.9
    )
    response = zhipuai.model_api.sse_invoke(**params.asdict())
    for event in response.events():
        if event.event == "add":
            print(event.data)
        elif event.event == "error" or event.event == "interrupted":
            print(event.data)
        elif event.event == "finish":
            print(event.data)
            print(event.meta)
        else:
            print(event.data)


def query_async_invoke_result_example():
    response = zhipuai.model_api.query_async_invoke_result("your task_id")
    print(response)
