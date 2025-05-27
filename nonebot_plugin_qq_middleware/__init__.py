import asyncio
from datetime import datetime
from typing import cast

from arclet.alconna import Alconna, AllParam, Args
from nonebot import get_driver, require
from nonebot.adapters import Bot, Event
from nonebot.adapters.onebot.v11.event import MessageEvent
from nonebot.adapters.qq import Bot as QQBot
from nonebot.adapters.qq.event import QQMessageEvent
from nonebot.log import logger
from nonebot.plugin import PluginMetadata
from nonebot_plugin_alconna import At, UniMsg, on_alconna
from nonebot_plugin_uninfo import Uninfo

from .utils import pair_avatar

require("nonebot_plugin_alconna")
require("nonebot_plugin_uninfo")

from .config import Config, config

__plugin_meta__ = PluginMetadata(
    name="qq_middleware",
    description="一个简易的用于让野Q机器人提供发送者qq号给官Q机器人的中间件",
    usage="",
    type="library",
    homepage="https://github.com/MiddleRed/nonebot-plugin-qq-middleware",
    config=Config,
    supported_adapters={"~onebot.v11", "~qq"}
)

driver = get_driver()
offical_qbot: QQBot | None = None
yasei_qbot: Bot | None = None

offical_id = str(config.qbot_middleware_official_qbot_id)
yasei_id = str(config.qbot_middleware_yasei_qbot_id)

# key: (timestamp, raw_message) | value: [qq_id]
_yasei_qbot_message: dict[tuple[int,str],list[str]] = {}
_yasei_qbot_message_waiting: dict[tuple[int,str], asyncio.Event] = {}


def is_collaborating() -> bool:
    """检查是否有官方机器人和野生机器人连接"""
    return offical_qbot is not None and yasei_qbot is not None

@driver.on_bot_connect
async def _(bot: Bot):
    """处理机器人连接事件"""

    global offical_qbot, yasei_qbot
    bot_adapter = bot.adapter.get_name()

    if bot_adapter == "QQ":
        bot = cast(QQBot, bot)
        offical_qbot = bot
        logger.opt(colors=True).info(f"<y>Official Bot {bot.self_id}</y> connected.")
    elif bot_adapter == "OneBot V11":
        yasei_qbot = bot
        logger.opt(colors=True).info(f"<y>Yasei Bot {bot.self_id}</y> connected.")


# 野生机器人观察官方机器人被 At 消息
_spec_ping = on_alconna(
    Alconna(
        At(flag="user", target=offical_id),
        Args["_any", AllParam]
    ),
    rule=is_collaborating,
    block=True
)
@_spec_ping.handle()
async def _(event: Event, msg: UniMsg, info: Uninfo):
    """收集野生机器人收到的官方机器人被 At 消息"""

    # You can implement your own extract logic for extracting message timestamp
    msg_time: int = -1
    if isinstance(event, MessageEvent):
        msg_time = event.time
    else:
        raise NotImplementedError(f"Unsupported event type for message time extraction: {type(event)}")

    key = (msg_time, msg.extract_plain_text().lstrip())

    if key not in _yasei_qbot_message:
        _yasei_qbot_message[key] = []
        asyncio.get_event_loop().call_later(
            config.qbot_middleware_matching_timeout,
            _yasei_qbot_message.pop, key, None
        )
    _yasei_qbot_message[key].append(info.user.id)

    if key in _yasei_qbot_message_waiting:
        _yasei_qbot_message_waiting[key].set()


from typing import Annotated

from nonebot.params import Depends


async def get_qq_id(event: QQMessageEvent, msg: UniMsg, info: Uninfo) -> str | None:
    key = (int(datetime.fromisoformat(event.timestamp).timestamp()), msg.extract_plain_text())
    url = info.user.avatar
    if url is None:
        logger.warning(f"{info.user.id}: Avatar URL is None, cannot do auto pairing.")
        return None

    async def matching() -> str | None:
        if key in _yasei_qbot_message and \
            (result := (await pair_avatar(info.user.id, _yasei_qbot_message[key]))) is not None:
            return result

        wait_new_msg = _yasei_qbot_message_waiting.setdefault(key, asyncio.Event())
        wait_new_msg.clear()
        await wait_new_msg.wait()

    async def _task() -> str | None:
        while True:
            result = await matching()
            if result is not None:
                return result

    try:
        wait_task = asyncio.create_task(_task())
        result = await asyncio.wait_for(wait_task, config.qbot_middleware_matching_timeout)
        return result
    except asyncio.TimeoutError:
        logger.warning(f"Matching user task timed out: {info.user.id}")
        return None

GetQQId = Annotated[str | None, Depends(get_qq_id)]
