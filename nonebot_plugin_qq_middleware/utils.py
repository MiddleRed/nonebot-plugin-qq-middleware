from io import BytesIO
import math

import aiohttp
from nonebot.log import logger
from PIL import Image, ImageChops

from . import config, driver, offical_qbot

_http_session: aiohttp.ClientSession | None = None
_headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",  # noqa: E501
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0",  # noqa: E501
    "sec-ch-ua": '"Chromium";v="136", "Microsoft Edge";v="136", "Not.A/Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}

async def _init_http_session():
    global _http_session
    if _http_session is not None:
        return

    _http_session = aiohttp.ClientSession(headers=_headers)

@driver.on_startup
async def _():
    await _init_http_session()


def img_compare(img1: Image.Image, img2: Image.Image) -> float:
    """基于均方根误差比较两张图片的相似度。返回值越小，图片越相似。"""

    if img1.size != img2.size:
        img2 = img2.resize(img1.size, Image.Resampling.LANCZOS)
    diff = ImageChops.difference(img1, img2)
    h = diff.histogram()
    sq = (value * ((idx % 256) ** 2) for idx, value in enumerate(h))
    sum_of_squares = sum(sq)
    return math.sqrt(sum_of_squares / float(img1.size[0] * img1.size[1]))


async def pair_avatar(open_id: str, qq_id_list: list[str]) -> str | None:
    if _http_session is None:
        await _init_http_session()
    assert _http_session is not None, "Unexpected error: HTTP session is not initialized."
    assert offical_qbot is not None, "Unexpected error: Official bot is not connected."

    offi_avater = f"https://q.qlogo.cn/qqapp/{offical_qbot.bot_info.id}/{open_id}/640"
    async with _http_session.get(offi_avater) as resp:
        if resp.status != 200:
            logger.warning(f"Failed to fetch official avatar: {offi_avater}, status: {resp.status}")
            return None
        offi_img = Image.open(BytesIO(await resp.read()))

    for qq_id in qq_id_list:
        qq_avater = f"https://q.qlogo.cn/g?b=qq&nk={qq_id}&s=640"
        async with _http_session.get(qq_avater) as resp:
            if resp.status != 200:
                logger.warning(f"Failed to fetch QQ avatar: {qq_avater}, status: {resp.status}")
                continue
            qq_img = Image.open(BytesIO(await resp.read()))

        if img_compare(offi_img, qq_img) < config.qbot_middleware_accepted_threshold:
            logger.success(f"Matched QQ ID: {qq_id} with Open ID: {open_id}")
            return qq_id

    return None
