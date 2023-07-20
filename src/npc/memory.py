import openai
#import zhipuai
import os

openai.api_key = "sk-8p38chfjXbbL1RT943B051229a224a8cBdE1B53b5e2c04E2"
openai.api_base = "https://api.ai-yyds.com/v1"
os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890"
