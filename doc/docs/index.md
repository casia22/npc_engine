# 🎮 NPC-Engine 🚀

NPC-Engine 是一个由 CogniMatrix™️ 提供的游戏AI引擎，它赋予游戏AI以群体智能。

![Author Badge](https://img.shields.io/badge/author-CogniMatrix-blue)
[![Documentation](https://img.shields.io/badge/Documentation-Available-blue)](https://docs.cognimatrix.games/npc_engine_doc/)
[![Discord Chat](https://img.shields.io/badge/Discord-Chat-blue)](https://discord.com/channels/1159008679308308480/1159008679308308483)

## 📦 用户安装
本项目免安装，直接在发行版中运行start_engine.bat脚本就可以

## 📦 开发者安装
本项目可以通过两种方式安装依赖，使用 Poetry 或者使用 pip。

### 使用 Poetry

首先，你需要安装 Poetry。你可以使用以下命令安装 Poetry：

```bash
curl -sSL https://install.python-poetry.org | python - # 安装 Poetry
poetry export -f requirements.txt --without-hashes -o requirements.txt # 生成 requirements.txt(提供给pip使用)
```

然后，你可以使用以下命令在项目目录中安装依赖：

```bash
poetry install
```

### 使用 pip

如果你更倾向于使用 pip，你可以使用以下命令安装依赖：

```bash
pip install -r requirements.txt
```

## 项目进展

### 🚀 开发进度：

- [x] 🔨 工程化代码
- [ ] 🧪 完成测试用例 (进行中)
- [x] 🤖 NPC决策
- [ ] 💬 添加单人对话
- [ ] 📝 完善文档 (进行中)
- [x] 🗃️ 本地向量数据库
- [x] 🧠 本地embedding模型
- [ ] 💡 添加基于embedding搜索的action决策
- [ ] 🔄 场景切换的大模型功能

### 🎉 项目里程碑

- 🗓️ 2023年6月: 项目开始，实现对话房间功能
- 🗓️ 2023年7/8月: 实现NPC action功能
- 🎈 2023年9月16日: DEMO小镇运行成功，代码初步可用

### 🏆 获得荣誉

- 🥈 2023年8月: 获得国科大创新创业大赛二等奖
- 🎖️ 2023年9月: 获得面壁智能hackthon挑战赛优胜奖

🔔 请持续关注我们的项目，以获取最新的进展和更新！
