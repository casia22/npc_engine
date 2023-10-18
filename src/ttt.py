import re

def parse_response(response):
    mood_purpose_pattern = r'@\[(.*?)\]'
    action_prompt_pattern = r'<(.*?)>@<'
    answer_prompt_pattern = r'>@<(.*?)>@'

    try:
        mood_purpose = re.search(mood_purpose_pattern, response).group(1)
    except AttributeError:
        mood_purpose = ""

    try:
        action_prompt = re.search(action_prompt_pattern, response).group(1)
    except AttributeError:
        action_prompt = ""

    try:
        answer_prompt = re.search(answer_prompt_pattern, response).group(1)
    except AttributeError:
        answer_prompt = ""

    return mood_purpose, action_prompt, answer_prompt

try:
    response = "@[开心]<警员1想巡逻林区，因为警员1想确认是否有人偷砍树。>@<mov|林区|>@我来帮你确认一下。@"
    mood_purpose, action_prompt, answer_prompt = parse_response(response)
    print(f"Mood and Purpose: {mood_purpose}, Action Prompt: {action_prompt}, Answer Prompt: {answer_prompt}")
except Exception as e:
    print(f"An error occurred: {e}")
