<div align="center">
    <a href="https://v2.nonebot.dev/store">
    <img src="https://raw.githubusercontent.com/fllesser/nonebot-plugin-template/refs/heads/resource/.docs/NoneBotPlugin.svg" width="310" alt="logo"></a>

## ✨ nonebot-plugin-qq-middleware ✨

<a href="./LICENSE">
    <img src="https://img.shields.io/github/license/MiddleRed/nonebot-plugin-qq-middleware.svg" alt="license">
</a>
<img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="python">
<a href="https://github.com/astral-sh/ruff">
    <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json" alt="ruff">
</a>
<a href="https://github.com/astral-sh/uv">
    <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json" alt="uv">
</a>
</div>

## 📖 介绍

用于将用户 QQ 号通过野生 QQ Bot 读取传递给官方 QQ 机器人。

## 💿 安装
本插件仅为概念性验证，强烈建议自行 clone 源码放入机器人插件目录，并根据自己需要修改。  
如果你实在想直接用，在 nb 机器人虚拟环境下使用以下指令安装：
```
pip install git+https://github.com/MiddleRed/nonebot-plugin-qq-middleware
```

## 🎉 使用
需要官方机器人和野生机器人**在同一个群内时**才生效，私聊无效。可自行实现绑定功能。  
由于用户匹配依赖于获取 `Event` 的时间戳，而目前并没有跨平台的方式能统一获取，因此仅实现了 Onebot V11 协议。可自行修改源码适配其他协议。
```python
from nonebot import on_type, require
from nonebot.params import Depends
from nonebot.adapters.qq.event import QQMessageEvent

require("nonebot_plugin_qq_middleware")
from nonebot_plugin_alconna import UniMessage

# 依赖注入项，返回 str（匹配成功时的 qq 号）或 None（无匹配）
from nonebot_plugin_qq_middleware import get_qq_id, GetQQId 

# 是否野生机器人和官方机器人同时在线（Rule）
from nonebot_plugin_qq_middleware import is_collaborating

# 使用
ping = on_type(QQMessageEvent, rule=is_collaborating)
@ping.handle()
async def _(event: QQMessageEvent, qid: str | None = Depends(get_qq_id)):
    await Unimessage.text(str(qid)).finish()

# 或者选择不用 Depends 方式的依赖注入
@ping.handle()
async def _(event: QQMessageEvent, qid: GetQQId):
    await Unimessage.text(str(qid)).finish()
```

## ⚙️ 配置

在 nonebot2 项目的`.env`文件中添加下表中的必填配置

| 配置项  | 必填  | 默认值 |   说明   |
| :-----: | :---: | :----: | :------: |
| QBOT_MIDDLEWARE_OFFICIAL_QBOT_ID   |  是   |   \   | 官方机器人的 **QQ 号** |
| QBOT_MIDDLEWARE_YASEI_QBOT_ID      |  是   |   \   | 野生机器人的 QQ 号 |
| QBOT_MIDDLEWARE_MATCHING_TIMEOUT   |  否   |   10  | 最大等待匹配时间 |
| QBOT_MIDDLEWARE_ACCEPTED_THRESHOLD |  否   |  0.5  | 头像匹配相似度，越高容忍度越大|
