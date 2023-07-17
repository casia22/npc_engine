import os
import subprocess
import anybadge

# 将你的项目路径替换为'your_project'
project_path = './'

# 使用pylint对你的项目进行评分
command = 'pylint ./'
score = 0.1
process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
out, err = process.communicate()

# 获取评分
lines = out.decode('utf-8').split('\n')
for line in lines:
    if 'Your code has been rated at' in line:
        score = float(line.split('/')[0].split(' ')[-1])
# 使用anybadge生成徽章
badge = anybadge.Badge('pylint', score, thresholds={2: 'red', 4: 'orange', 8: 'yellow', 10: 'green'})
print("code score:",score)

# 将徽章保存到文件
badge.write_badge('./material/badges/pylint.svg',overwrite=True)

import os
import subprocess
import pytest
import anybadge

# 将你的项目路径替换为'your_project'
project_path = './'

# 获取总的测试用例数
total_tests = 0
for root, dirs, files in os.walk(project_path):
    for file in files:
        if file.endswith('.py'):
            with open(os.path.join(root, file), 'r') as f:
                content = f.read()
                total_tests += content.count('def test_')

# 执行测试
passed_tests = 0
for root, dirs, files in os.walk(project_path):
    for file in files:
        if file.endswith('.py'):
            try:
                result = pytest.main([os.path.join(root, file), "-q"])
                if result == 0:
                    passed_tests += 1
            except:
                continue

# 计算百分比
if total_tests > 0:
    score = (passed_tests / total_tests) * 100
else:
    score = 0

sc = score
# 使用anybadge生成徽章

badge = anybadge.Badge('pytest', sc, thresholds={20: 'red', 40: 'orange', 60: 'yellow', 80: 'green', 100: 'brightgreen'})

# 将徽章保存到文件，如果文件已经存在，就覆盖它
badge.write_badge('./material/badges/pytest.svg', overwrite=True)
