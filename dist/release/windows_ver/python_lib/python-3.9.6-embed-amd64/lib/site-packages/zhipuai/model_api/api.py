# -*- coding:utf-8 -*-
import posixpath

import zhipuai
from zhipuai.utils import jwt_token
from zhipuai.utils.http_client import get, post, stream
from zhipuai.utils.sse_client import SSEClient


class InvokeType:
    SYNC = "invoke"
    ASYNC = "async-invoke"
    SSE = "sse-invoke"


class ModelAPI:
    @classmethod
    def invoke(cls, **kwargs):
        url = cls._build_api_url(kwargs, InvokeType.SYNC)
        return post(url, cls._generate_token(), kwargs, zhipuai.api_timeout_seconds)

    @classmethod
    def async_invoke(cls, **kwargs):
        url = cls._build_api_url(kwargs, InvokeType.ASYNC)
        return post(url, cls._generate_token(), kwargs, zhipuai.api_timeout_seconds)

    @classmethod
    def query_async_invoke_result(cls, task_id: str):
        url = cls._build_api_url(None, InvokeType.ASYNC, task_id)
        return get(url, cls._generate_token(), zhipuai.api_timeout_seconds)

    @classmethod
    def sse_invoke(cls, **kwargs):
        url = cls._build_api_url(kwargs, InvokeType.SSE)
        data = stream(url, cls._generate_token(), kwargs, zhipuai.api_timeout_seconds)
        return SSEClient(data)

    @staticmethod
    def _build_api_url(kwargs, *path):
        if kwargs:
            if "model" not in kwargs:
                raise Exception("model param missed")
            model = kwargs.pop("model")
        else:
            model = "-"

        return posixpath.join(zhipuai.model_api_url, model, *path)

    @staticmethod
    def _generate_token():
        if not zhipuai.api_key:
            raise Exception(
                "api_key not provided, you could provide it with `shell: export API_KEY=xxx` or `code: zhipuai.api_key=xxx`"
            )

        return jwt_token.generate_token(zhipuai.api_key)
