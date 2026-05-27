"""宠物配置加载模块
从 pet_config.json 加载所有宠物的俏皮话、提醒、特殊日期等配置
支持运行时重载，方便用户随时修改 JSON
"""

import json
import logging
import sys
from pathlib import Path
from typing import Optional

logging.basicConfig(level=logging.INFO, format="[PetConfig] %(message)s")
logger = logging.getLogger("PetConfig")


def _get_config_path() -> Path:
    """获取 pet_config.json 路径（兼容 PyInstaller 打包）"""
    if getattr(sys, 'frozen', False):
        base = Path(sys.executable).parent
    else:
        base = Path(__file__).parent
    return base / "pet_config.json"


class PetConfig:
    """宠物配置单例，从 pet_config.json 加载并缓存"""

    def __init__(self):
        self._data: dict = {}
        self._load()

    def _load(self):
        """加载配置文件"""
        path = _get_config_path()
        if not path.exists():
            logger.warning(f"pet_config.json not found at {path}")
            self._data = self._get_defaults()
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                self._data = json.load(f)
            logger.info(f"Loaded pet_config.json (dog: {self.dog_name}, owner: {self.owner_name})")
        except Exception as e:
            logger.error(f"Failed to load pet_config.json: {e}")
            self._data = self._get_defaults()

    def reload(self):
        """重新加载配置（用户修改 JSON 后调用）"""
        self._load()

    def _get_defaults(self) -> dict:
        """返回默认配置"""
        return {
            "dog_name": "旺财",
            "owner_name": "小主人",
            "pet_phrases_normal": [
                "小主人干嘛呀~",
                "小主人我在呢！",
                "小主人想我了吗？",
                "小主人陪我玩！",
                "嘿嘿，小主人真好~",
                "小主人别闹~",
            ],
            "pet_phrases_time": {
                "morning": ["小主人早上好！☀️", "小主人起床啦？早呀~"],
                "noon": ["小主人中午好！🍚", "小主人吃饭了吗？"],
                "afternoon": ["小主人下午好呀~", "下午啦小主人，喝口水吧！"],
                "evening": ["小主人晚上好！🌙", "小主人晚上好，吃饭了吗？"],
            },
            "pet_phrases_annoyed": [
                "干嘛呀小主人！",
                "小主人你讨厌！",
                "我都快要被你薅秃了！！",
            ],
            "pet_annoy_threshold": 7,
            "pet_cooldown": 300,
            "love_phrases": [
                "小主人，陪你一起成长是最幸福的事~ ❤️",
            ],
            "special_dates": {
                "11-13": ["生日快乐！🎂🎉"],
                "1-1": ["新年快乐！🎉🐶"],
            },
            "water_reminders": [
                "小主人，该喝水啦！💧",
            ],
        }

    # ---- 属性访问 ----

    @property
    def dog_name(self) -> str:
        return self._data.get("dog_name", "旺财")

    @property
    def owner_name(self) -> str:
        return self._data.get("owner_name", "小主人")

    @property
    def phrases_normal(self) -> list[str]:
        return self._data.get("pet_phrases_normal", ["汪汪~"])

    @property
    def phrases_time(self) -> dict[str, list[str]]:
        return self._data.get("pet_phrases_time", {})

    @property
    def phrases_annoyed(self) -> list[str]:
        return self._data.get("pet_phrases_annoyed", ["别摸啦！"])

    @property
    def annoy_threshold(self) -> int:
        return self._data.get("pet_annoy_threshold", 7)

    @property
    def cooldown(self) -> int:
        return self._data.get("pet_cooldown", 300)

    @property
    def love_phrases(self) -> list[str]:
        return self._data.get("love_phrases", ["小主人，你好呀~"])

    @property
    def special_dates(self) -> dict[str, list[str]]:
        return self._data.get("special_dates", {})

    @property
    def water_reminders(self) -> list[str]:
        return self._data.get("water_reminders", ["该喝水啦！"])

    def get_data(self) -> dict:
        """返回完整配置数据"""
        return dict(self._data)


# 全局单例
_pet_config: Optional[PetConfig] = None


def get_pet_config() -> PetConfig:
    """获取全局 PetConfig 单例"""
    global _pet_config
    if _pet_config is None:
        _pet_config = PetConfig()
    return _pet_config


def reload_pet_config():
    """重新加载宠物配置"""
    global _pet_config
    if _pet_config is None:
        _pet_config = PetConfig()
    else:
        _pet_config.reload()