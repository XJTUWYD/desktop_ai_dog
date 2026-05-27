"""首次启动配置对话框
配置 API 设置、狗狗名字和主人名字
"""

import json
import sys
from pathlib import Path
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QWidget,
    QStackedWidget, QComboBox, QFrame,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon


def _get_config_path(filename: str) -> Path:
    """获取配置文件路径（兼容 PyInstaller 打包）"""
    if getattr(sys, 'frozen', False):
        base = Path(sys.executable).parent
    else:
        base = Path(__file__).parent
    return base / filename


def _get_data_path(filename: str) -> Path:
    """获取数据文件路径（PyInstaller 打包时在 _MEIPASS 中）"""
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS) / filename
    else:
        return Path(__file__).parent / filename


# 默认宠物配置模板
def get_default_pet_config(dog_name: str = "", owner_name: str = "") -> dict:
    """生成默认宠物配置，使用用户输入的名字"""
    dname = dog_name or "旺财"
    oname = owner_name or "小主人"
    return {
        "dog_name": dname,
        "owner_name": oname,
        "pet_phrases_normal": [
            f"{oname}干嘛呀~",
            f"{oname}我在呢！",
            f"{oname}想我了吗？",
            f"{oname}陪我玩！",
            f"嘿嘿，{oname}真好~",
            f"{oname}别闹~",
        ],
        "pet_phrases_time": {
            "morning": [
                f"{oname}早上好！☀️",
                f"{oname}起床啦？早呀~",
                f"早安{oname}！今天也要开心哦！",
                f"{oname}早上好，汪汪~",
            ],
            "noon": [
                f"{oname}中午好！🍚",
                f"{oname}吃饭了吗？",
                f"中午好{oname}，该吃午饭啦~",
                f"{oname}中午好，记得休息哦！",
            ],
            "afternoon": [
                f"{oname}下午好呀~",
                f"下午啦{oname}，喝口水吧！",
                f"{oname}下午好，我在陪你呢~",
            ],
            "evening": [
                f"{oname}晚上好！🌙",
                f"{oname}晚上好，吃饭了吗？",
                f"{oname}今天开心吗？汪汪~",
                f"晚上好呀{oname}，早点休息啦！",
            ],
        },
        "pet_phrases_annoyed": [
            f"干嘛呀{oname}！",
            f"{oname}你讨厌！",
            "我都快要被你薅秃了！！",
            f"别摸啦{oname}！毛都掉了！",
            f"啊啊啊{oname}住手！",
            f"再摸就咬你啦{oname}！",
            f"{oname}你手不累吗！",
        ],
        "pet_annoy_threshold": 7,
        "pet_cooldown": 300,
        "love_phrases": [
            f"{oname}，陪你一起成长是最幸福的事~ ❤️",
            f"{oname}，你是最棒的{oname}！💪",
            f"汪汪~ {oname}开心我就开心！",
            f"{oname}，今天的你也是最可爱的！",
            "有你陪伴的每一天都超棒🌟",
            f"{oname}，我会一直陪着你的~",
            f"{oname}，我们一起出去玩吧！",
            "月亮替我守护你🌙",
            "有你在的每一天都是晴天☀️",
            f"汪汪！{oname}最厉害了！",
            "和你一起的时光都是甜的🍬",
            f"我的{oname}是全世界最棒的小孩！",
            f"{oname}，你是我最好的朋友💕",
            f"{oname}，今天也要快快乐乐呀~",
            f"你是我的小太阳，{oname}☀️",
            f"汪汪~ {oname}，想和你一起玩耍🎾",
            f"{oname}，你就是最闪亮的星⭐",
            f"{oname}，有你就是最好的时光",
            f"{oname}，我们一起慢慢长大🌱",
            f"汪汪~ {oname}今天特别帅！",
            f"我要一直守护你呀，{oname}~",
            f"{oname}，你是上天最好的礼物🎁",
            f"无论多远，我都会陪着{oname}",
            "汪汪~ 今天的心情是心形的☁️",
            f"{oname}，你是我最骄傲的小英雄🦸",
            f"认识{oname}是我最大的幸运🍀",
            f"一天不见{oname}就特别想，汪汪~",
            f"{oname}，你的笑容是最美的🌸",
            f"能陪着{oname}是最开心的事💗",
        ],
        "special_dates": {
            "11-13": [
                f"{oname}生日快乐！🎂🎉",
                f"{oname}生日快乐！今天你最大！🎊",
                f"{oname}生日快乐呀！汪汪爱你！🎁💕",
                f"生日快乐{oname}！许个愿吧🎂✨",
            ],
            "1-1": [
                f"{oname}新年快乐！🎉🐶",
                f"新年快乐{oname}！今年也要幸福满满！",
                f"新的一年，陪着{oname}一起成长！❤️🎊",
            ],
            "6-1": [
                f"{oname}儿童节快乐！🎈🍭",
                f"{oname}儿童节快乐！今天你最大！🎉",
                f"汪汪~ 儿童节快乐{oname}！一起玩吧！🎠",
            ],
            "10-1": [
                f"{oname}国庆快乐！🇨🇳🎉",
                f"国庆快乐！带{oname}出去玩吧！",
            ],
            "12-25": [
                f"{oname}圣诞快乐！🎄🎅",
                f"圣诞快乐{oname}！Merry Christmas！🎁✨",
            ],
            "12-31": [
                f"{oname}跨年快乐！新的一年继续陪你！🎆🐶",
                f"{oname}新年快乐！感谢有你陪伴！🎉",
            ],
        },
        "water_reminders": [
            f"{oname}，该喝水啦！💧",
            f"{oname}喝水时间到！多喝水身体棒~💪",
            f"{oname}喝口水吧！身体健康最重要！💧❤️",
            f"{oname}你已经好久没喝水了！快喝！🚰",
            f"温馨提醒：{oname}该喝水了💙💧",
            f"{oname}，记得补充水分哦~💧",
        ],
    }


class SetupDialog(QDialog):
    """首次启动配置对话框"""

    def __init__(self, parent=None):
        super().__init__(None, Qt.WindowStaysOnTopHint)
        self.setWindowTitle("🐕 Desktop Dog - 初始设置")
        self.setFixedSize(500, 420)

        self._api_skipped = False
        self._result_config = {}
        self._result_pet_config = {}

        self._init_ui()
        self._set_style()
        self._load_existing_config()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # 标题
        title = QLabel("🐕 欢迎使用 Desktop Dog！")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("在开始之前，请进行一些基本设置~")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(subtitle)

        layout.addSpacing(8)

        # --- API 配置区域 ---
        api_frame = QFrame()
        api_frame.setObjectName("apiFrame")
        api_layout = QVBoxLayout(api_frame)
        api_layout.setSpacing(8)

        api_title = QLabel("🤖 API 设置（用于 AI 对话功能）")
        api_title.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        api_layout.addWidget(api_title)

        api_tip = QLabel("不填也可以跳过，但对话功能将不可用")
        api_tip.setStyleSheet("color: #777; font-size: 11px;")
        api_layout.addWidget(api_tip)

        # API Key
        key_layout = QHBoxLayout()
        key_label = QLabel("API Key:")
        key_label.setFixedWidth(80)
        key_layout.addWidget(key_label)
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("输入你的 API Key（如 DeepSeek API Key）")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        key_layout.addWidget(self.api_key_input, 1)
        api_layout.addLayout(key_layout)

        # Model
        model_layout = QHBoxLayout()
        model_label = QLabel("Model:")
        model_label.setFixedWidth(80)
        model_layout.addWidget(model_label)
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("deepseek-chat")
        self.model_input.setText("deepseek-chat")
        model_layout.addWidget(self.model_input, 1)
        api_layout.addLayout(model_layout)

        # Base URL
        url_layout = QHBoxLayout()
        url_label = QLabel("Base URL:")
        url_label.setFixedWidth(80)
        url_layout.addWidget(url_label)
        self.base_url_input = QLineEdit()
        self.base_url_input.setPlaceholderText("https://api.deepseek.com")
        self.base_url_input.setText("https://api.deepseek.com")
        url_layout.addWidget(self.base_url_input, 1)
        api_layout.addLayout(url_layout)

        # 跳过按钮
        skip_layout = QHBoxLayout()
        skip_layout.addStretch()
        self.skip_api_btn = QPushButton("跳过 API 设置（对话功能不可用）")
        self.skip_api_btn.setObjectName("skipBtn")
        self.skip_api_btn.clicked.connect(self._skip_api)
        skip_layout.addWidget(self.skip_api_btn)
        skip_layout.addStretch()
        api_layout.addLayout(skip_layout)

        layout.addWidget(api_frame)

        # 分隔线
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #e8d5b0;")
        layout.addWidget(sep)

        # --- 宠物名字区域 ---
        pet_frame = QFrame()
        pet_frame.setObjectName("petFrame")
        pet_layout = QVBoxLayout(pet_frame)
        pet_layout.setSpacing(8)

        pet_title = QLabel("🐶 宠物设置")
        pet_title.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        pet_layout.addWidget(pet_title)

        # 狗狗名字
        dog_layout = QHBoxLayout()
        dog_label = QLabel("狗狗名字:")
        dog_label.setFixedWidth(80)
        dog_layout.addWidget(dog_label)
        self.dog_name_input = QLineEdit()
        self.dog_name_input.setPlaceholderText("给你的狗狗起个名字吧~")
        self.dog_name_input.setText("旺财")
        dog_layout.addWidget(self.dog_name_input, 1)
        pet_layout.addLayout(dog_layout)

        # 主人名字
        owner_layout = QHBoxLayout()
        owner_label = QLabel("主人名字:")
        owner_label.setFixedWidth(80)
        owner_layout.addWidget(owner_label)
        self.owner_name_input = QLineEdit()
        self.owner_name_input.setPlaceholderText("你的名字是什么？")
        self.owner_name_input.setText("小宝")
        owner_layout.addWidget(self.owner_name_input, 1)
        pet_layout.addLayout(owner_layout)

        pet_tip = QLabel("设置后，狗狗会用这些名字称呼你们~ 之后也可以在 pet_config.json 中修改所有对话内容")
        pet_tip.setStyleSheet("color: #777; font-size: 11px;")
        pet_tip.setWordWrap(True)
        pet_layout.addWidget(pet_tip)

        layout.addWidget(pet_frame)

        layout.addStretch()

        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.quit_btn = QPushButton("❌ 退出")
        self.quit_btn.setObjectName("quitBtn")
        self.quit_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.quit_btn)

        self.ok_btn = QPushButton("✅ 开始使用")
        self.ok_btn.clicked.connect(self._on_confirm)
        btn_layout.addWidget(self.ok_btn)

        layout.addLayout(btn_layout)

    def _load_existing_config(self):
        """加载已有配置作为默认值"""
        config_path = _get_config_path("config.json")
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                if cfg.get("api_key") and cfg.get("api_key") != "YOUR_DEEPSEEK_API_KEY_HERE":
                    self.api_key_input.setText(cfg.get("api_key", ""))
                self.model_input.setText(cfg.get("model", "deepseek-chat"))
                self.base_url_input.setText(cfg.get("base_url", "https://api.deepseek.com"))
            except Exception:
                pass

        pet_config_path = _get_config_path("pet_config.json")
        if pet_config_path.exists():
            try:
                with open(pet_config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                self.dog_name_input.setText(cfg.get("dog_name", "旺财"))
                self.owner_name_input.setText(cfg.get("owner_name", "小宝"))
            except Exception:
                pass

    def _skip_api(self):
        """跳过 API 配置"""
        reply = QMessageBox.warning(
            self,
            "确认跳过",
            "跳过 API 设置后，AI 对话功能将不可用。\n\n"
            "你仍然可以和狗狗互动（摸摸头、散步等），\n"
            "但无法和狗狗进行 AI 对话。\n\n"
            "确定要跳过吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self._api_skipped = True
            self.api_key_input.clear()
            self.api_key_input.setPlaceholderText("已跳过 - AI 对话不可用")
            self.api_key_input.setEnabled(False)
            self.model_input.setEnabled(False)
            self.base_url_input.setEnabled(False)
            self.skip_api_btn.setEnabled(False)
            self.skip_api_btn.setText("✓ 已跳过")

    def _on_confirm(self):
        """确认配置"""
        dog_name = self.dog_name_input.text().strip()
        owner_name = self.owner_name_input.text().strip()

        if not dog_name:
            QMessageBox.warning(self, "提示", "请输入狗狗的名字！")
            return
        if not owner_name:
            QMessageBox.warning(self, "提示", "请输入主人的名字！")
            return

        # 构建 API 配置
        self._result_config = {
            "api_key": self.api_key_input.text().strip() if not self._api_skipped else "",
            "model": self.model_input.text().strip() or "deepseek-chat",
            "base_url": self.base_url_input.text().strip() or "https://api.deepseek.com",
            "setup_complete": True,
        }

        # 保持 system_prompt 和对话历史配置
        config_path = _get_config_path("config.json")
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    old_cfg = json.load(f)
                self._result_config["system_prompt"] = old_cfg.get("system_prompt", "")
                self._result_config["remember_history"] = old_cfg.get("remember_history", True)
                self._result_config["max_history"] = old_cfg.get("max_history", 20)
            except Exception:
                pass

        # 构建宠物配置
        self._result_pet_config = get_default_pet_config(dog_name, owner_name)

        self.accept()

    def get_api_config(self) -> dict:
        """返回 API 配置"""
        return self._result_config

    def get_pet_config(self) -> dict:
        """返回宠物配置"""
        return self._result_pet_config

    @property
    def api_skipped(self) -> bool:
        return self._api_skipped

    def _set_style(self):
        self.setStyleSheet("""
            SetupDialog {
                background-color: #fff8f0;
            }
            QLabel {
                font-family: "Microsoft YaHei";
                color: #333333;
            }
            QLineEdit {
                background-color: #ffffff;
                color: #333333;
                border: 2px solid #e0d0b0;
                border-radius: 8px;
                padding: 6px 10px;
                font-size: 13px;
                font-family: "Microsoft YaHei";
            }
            QLineEdit:focus {
                border-color: #e8a040;
            }
            QLineEdit:disabled {
                background-color: #f5f5f5;
                color: #999999;
            }
            QFrame#apiFrame, QFrame#petFrame {
                background-color: #ffffff;
                border: 1px solid #f0d0a0;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton {
                background-color: #f5a040;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 20px;
                font-size: 13px;
                font-weight: bold;
                font-family: "Microsoft YaHei";
            }
            QPushButton:hover {
                background-color: #e89030;
            }
            QPushButton:pressed {
                background-color: #d88020;
            }
            QPushButton#skipBtn {
                background-color: #e0d0c0;
                color: #666666;
                font-size: 11px;
                padding: 4px 12px;
                font-weight: normal;
            }
            QPushButton#skipBtn:hover {
                background-color: #d0c0b0;
                color: #444444;
            }
            QPushButton#skipBtn:disabled {
                background-color: #c8e6c9;
                color: #2e7d32;
            }
            QPushButton#quitBtn {
                background-color: #e0e0e0;
                color: #555555;
                font-weight: normal;
            }
            QPushButton#quitBtn:hover {
                background-color: #d0d0d0;
                color: #333333;
            }
        """)


def run_setup(parent=None) -> tuple[dict | None, dict | None, bool]:
    """
    运行首次设置对话框
    返回: (api_config, pet_config, api_skipped)
    如果用户选择退出，返回 (None, None, False)
    """
    dlg = SetupDialog(parent)
    if dlg.exec() == QDialog.Accepted:
        return dlg.get_api_config(), dlg.get_pet_config(), dlg.api_skipped
    else:
        return None, None, False


def needs_setup() -> bool:
    """检查是否需要运行设置向导"""
    config_path = _get_config_path("config.json")
    pet_config_path = _get_config_path("pet_config.json")

    # 检查 config.json 是否有 setup_complete 标记
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            if cfg.get("setup_complete", False) and pet_config_path.exists():
                return False
        except Exception:
            pass
    else:
        # config.json 不存在
        pass

    # pet_config.json 不存在就需要设置
    if not pet_config_path.exists():
        return True

    return False