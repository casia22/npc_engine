import re

def extract_action(string):
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


text = '''<chat|李大爷|李大爷你吃了吗>
<mov｜李大爷家｜>
<mov｜李大爷家|>
<put|箱子|苹果派>
<take|箱子｜西瓜汁，桃子，枕头>
<take|箱子｜西瓜汁,桃子，枕头>
<take｜箱子｜枕头>
<use|刀|西瓜>
<use|门|开>
<give|李大爷|茶叶>'''

li = text.split('\n')
for each in li:
    print(extract_action(each))
