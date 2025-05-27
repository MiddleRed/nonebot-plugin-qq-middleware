from nonebot import get_plugin_config
from pydantic import BaseModel


class Config(BaseModel):
    qbot_middleware_official_qbot_id: str | int
    qbot_middleware_yasei_qbot_id: str | int
    qbot_middleware_matching_timeout: int = 10
    qbot_middleware_accepted_threshold: float = 0.5

config = get_plugin_config(Config)
config.qbot_middleware_official_qbot_id = str(config.qbot_middleware_official_qbot_id)
config.qbot_middleware_yasei_qbot_id = str(config.qbot_middleware_yasei_qbot_id)
