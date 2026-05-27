"""设置对话框 - 通过右键菜单打开
支持：主人/狗狗名字修改、所有文案编辑
"""

import json
import sys
from pathlib import Path
from copy import deepcopy

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QTabWidget,
    QWidget, QTextEdit, QFrame, QGroupBox, QScrollArea,
    QFormLayout,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


def _get_config_path(filename: str) -> Path:
    """获取配置文件路径（兼容 PyInstaller 打包）"""
    if getattr(sys, 'frozen', False):
        base = Path(sys.executable).parent
    else:
        base = Path(__file__).parent
    return base / filename


def _load_json(path: Path) -> dict:
    """安全加载 JSON"""
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_json(path: Path, data: dict):
    """保存 JSON"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class SettingsDialog(QDialog):
    """设置对话框 - 名字 + 文案编辑"""

    def __init__(self, parent=None):
        super().__init__(None, Qt.WindowStaysOnTopHint)
        self.setWindowTitle("⚙️ Desktop Dog - 设置")
        self.setFixedSize(560, 520)

        # 加载当前配置
        self._pet_config = _load_json(_get_config_path("pet_config.json"))
        self._app_config = _load_json(_get_config_path("config.json"))

        self._init_ui()
        self._set_style()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        # 标题
        title = QLabel("🐕 狗狗设置")
        title.setFont(QFont("Microsoft YaHei", 15, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Tab 页
        self._tabs = QTabWidget()

        # Tab 1: 名字设置
        self._names_tab = self._create_names_tab()
        self._tabs.addTab(self._names_tab, "👤 名字设置")

        # Tab 2: 文案编辑
        self._phrases_tab = self._create_phrases_tab()
        self._tabs.addTab(self._phrases_tab, "💬 文案编辑")

        layout.addWidget(self._tabs, 1)

        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("💾 保存")
        save_btn.setObjectName("saveBtn")
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    # ==================== Tab 1: 名字设置 ====================

    def _create_names_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(14)

        tip = QLabel("修改主人和狗狗的名字，所有文案中的称呼会自动更新。")
        tip.setWordWrap(True)
        tip.setStyleSheet("color: #666; font-size: 12px; margin-bottom: 8px;")
        layout.addWidget(tip)

        # 主人名字
        owner_group = self._make_form_group("主人名字（在文案中替代「小主人」）")
        form = owner_group.findChild(QFormLayout)
        self._owner_input = QLineEdit()
        self._owner_input.setPlaceholderText("例如：小宝")
        self._owner_input.setText(self._pet_config.get("owner_name", "小宝"))
        self._owner_input.setMinimumHeight(32)
        form.addRow("主人:", self._owner_input)
        layout.addWidget(owner_group)

        # 狗狗名字
        dog_group = self._make_form_group("狗狗名字（在文案中替代「狗狗名」）")
        form = dog_group.findChild(QFormLayout)
        self._dog_input = QLineEdit()
        self._dog_input.setPlaceholderText("例如：小柴")
        self._dog_input.setText(self._pet_config.get("dog_name", "旺财"))
        self._dog_input.setMinimumHeight(32)
        form.addRow("狗狗:", self._dog_input)
        layout.addWidget(dog_group)

        # 说明
        note = QLabel(
            "💡 提示：保存后会自动替换所有文案中的「小主人」和「狗狗名」\n"
            "   如果已在文案中写死名字（如「小宝」），则不会被替换。"
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #777; font-size: 11px; background: #f8f5f0; "
                           "border-radius: 6px; padding: 10px;")
        layout.addWidget(note)

        layout.addStretch()
        return widget

    def _make_form_group(self, title: str) -> QGroupBox:
        group = QGroupBox(title)
        group.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
        layout = QFormLayout(group)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 16, 12, 12)
        return group

    # ==================== Tab 2: 文案编辑 ====================

    def _create_phrases_tab(self) -> QWidget:
        widget = QWidget()
        outer = QVBoxLayout(widget)
        outer.setContentsMargins(0, 0, 0, 0)

        tip = QLabel("编辑狗狗的各种对话文案，一行一条，保存后即时生效。")
        tip.setWordWrap(True)
        tip.setStyleSheet("color: #666; font-size: 12px; margin-bottom: 4px;")
        outer.addWidget(tip)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setSpacing(10)
        layout.setContentsMargins(4, 4, 12, 4)

        # 1. 正常摸头俏皮话
        layout.addWidget(self._make_text_group(
            "摸摸俏皮话（正常）", "pet_phrases_normal",
            self._pet_config.get("pet_phrases_normal", [])
        ))

        # 2. 时间短语
        time_phrases = self._pet_config.get("pet_phrases_time", {})
        times = ["morning", "noon", "afternoon", "evening"]
        time_labels = {"morning": "早上", "noon": "中午", "afternoon": "下午", "evening": "晚上"}
        for t in times:
            layout.addWidget(self._make_text_group(
                f"时间问候 - {time_labels[t]}", f"pet_phrases_time.{t}",
                time_phrases.get(t, [])
            ))

        # 3. 讨厌话
        layout.addWidget(self._make_text_group(
            "摸烦了的话", "pet_phrases_annoyed",
            self._pet_config.get("pet_phrases_annoyed", [])
        ))

        # 4. 整点情话
        layout.addWidget(self._make_text_group(
            "整点撒娇情话", "love_phrases",
            self._pet_config.get("love_phrases", [])
        ))

        # 5. 喝水提醒
        layout.addWidget(self._make_text_group(
            "喝水提醒", "water_reminders",
            self._pet_config.get("water_reminders", [])
        ))

        # 6. 特殊日期祝福
        special = self._pet_config.get("special_dates", {})
        special_text = ""
        for date_key, phrases in special.items():
            special_text += f"[{date_key}]\n"
            for p in phrases:
                special_text += p + "\n"
            special_text += "\n"
        layout.addWidget(self._make_text_group(
            "特殊日期祝福（格式：[月-日] -> 一行一条文案）", "special_dates",
            [], extra_text=special_text.strip()
        ))

        # 阈值参数
        params_group = QGroupBox("摸摸阈值参数")
        params_group.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        params_layout = QFormLayout(params_group)
        params_layout.setSpacing(6)

        self._threshold_input = QLineEdit()
        self._threshold_input.setText(str(self._pet_config.get("pet_annoy_threshold", 7)))
        params_layout.addRow("烦人阈值(摸几次后说讨厌话):", self._threshold_input)

        self._cooldown_input = QLineEdit()
        self._cooldown_input.setText(str(self._pet_config.get("pet_cooldown", 300)))
        params_layout.addRow("冷却时间(帧数):", self._cooldown_input)

        layout.addWidget(params_group)
        layout.addStretch()

        scroll.setWidget(inner)
        outer.addWidget(scroll, 1)
        return widget

    def _make_text_group(self, title: str, key: str, default_lines: list,
                         extra_text: str = None) -> QGroupBox:
        """创建一个文案编辑分组"""
        group = QGroupBox(title)
        group.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        g_layout = QVBoxLayout(group)
        g_layout.setSpacing(4)

        text_edit = QTextEdit()
        text_edit.setAcceptRichText(False)
        text_edit.setMinimumHeight(60)
        text_edit.setMaximumHeight(120)
        text_edit.setPlaceholderText("每行一条文案...")
        text_edit.setStyleSheet("font-size: 12px;")
        text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        if extra_text is not None:
            text_edit.setPlainText(extra_text)
        else:
            text_edit.setPlainText("\n".join(default_lines))

        # 保存引用以便读取
        setattr(self, f"_text_{key.replace('.', '_')}", text_edit)

        g_layout.addWidget(text_edit)
        return group

    # ==================== 保存逻辑 ====================

    def _on_save(self):
        """保存所有修改"""
        owner_name = self._owner_input.text().strip()
        dog_name = self._dog_input.text().strip()

        if not owner_name:
            QMessageBox.warning(self, "提示", "主人名字不能为空！")
            return
        if not dog_name:
            QMessageBox.warning(self, "提示", "狗狗名字不能为空！")
            return

        old_owner = self._pet_config.get("owner_name", "小主人")
        old_dog = self._pet_config.get("dog_name", "旺财")

        # 更新名字
        self._pet_config["owner_name"] = owner_name
        self._pet_config["dog_name"] = dog_name

        # 替换所有文案中的旧名字 -> 新名字
        self._pet_config = self._replace_names(
            self._pet_config, old_owner, old_dog, owner_name, dog_name
        )

        # 收集所有文案编辑框的内容
        text_fields = [
            ("pet_phrases_normal", "pet_phrases_normal"),
            ("pet_phrases_time.morning", "pet_phrases_time.morning"),
            ("pet_phrases_time.noon", "pet_phrases_time.noon"),
            ("pet_phrases_time.afternoon", "pet_phrases_time.afternoon"),
            ("pet_phrases_time.evening", "pet_phrases_time.evening"),
            ("pet_phrases_annoyed", "pet_phrases_annoyed"),
            ("love_phrases", "love_phrases"),
            ("water_reminders", "water_reminders"),
        ]

        for field_name, config_key in text_fields:
            attr_name = f"_text_{field_name.replace('.', '_')}"
            text_edit = getattr(self, attr_name, None)
            if text_edit:
                lines = [l.strip() for l in text_edit.toPlainText().split("\n") if l.strip()]
                keys = config_key.split(".")
                target = self._pet_config
                for k in keys[:-1]:
                    if k not in target:
                        target[k] = {}
                    target = target[k]
                target[keys[-1]] = lines

        # 特殊日期
        special_edit = getattr(self, "_text_special_dates", None)
        if special_edit:
            special = self._parse_special_dates(special_edit.toPlainText())
            self._pet_config["special_dates"] = special

        # 阈值参数
        try:
            self._pet_config["pet_annoy_threshold"] = int(self._threshold_input.text())
        except ValueError:
            self._pet_config["pet_annoy_threshold"] = 7

        try:
            self._pet_config["pet_cooldown"] = int(self._cooldown_input.text())
        except ValueError:
            self._pet_config["pet_cooldown"] = 300

        # 写入文件
        pet_path = _get_config_path("pet_config.json")
        _save_json(pet_path, self._pet_config)

        # 更新 system_prompt 中的名字
        self._update_system_prompt(owner_name, dog_name)

        QMessageBox.information(
            self, "保存成功",
            f"设置已保存！\n\n主人: {owner_name}\n狗狗: {dog_name}\n\n"
            "文案更改已即时生效，无需重启应用。"
        )
        self.accept()

    @staticmethod
    def _replace_names(config: dict, old_owner: str, old_dog: str,
                       new_owner: str, new_dog: str) -> dict:
        """递归替换配置中所有字符串字段的名字"""
        def _replace(value):
            if isinstance(value, str):
                # 先替换狗狗名，再替换主人名（避免交叉替换）
                s = value.replace(old_dog, new_dog)
                s = s.replace(old_owner, new_owner)
                return s
            elif isinstance(value, dict):
                return {k: _replace(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [_replace(v) for v in value]
            return value
        return _replace(deepcopy(config))

    @staticmethod
    def _parse_special_dates(text: str) -> dict:
        """解析特殊日期文本格式"""
        result = {}
        current_key = None
        for line in text.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            if line.startswith("[") and line.endswith("]"):
                current_key = line[1:-1].strip()
                if current_key not in result:
                    result[current_key] = []
            elif current_key:
                result[current_key].append(line)
        return result

    def _update_system_prompt(self, owner_name: str, dog_name: str):
        """更新 config.json 中 system_prompt 的主人和狗狗名字"""
        cfg_path = _get_config_path("config.json")
        cfg = _load_json(cfg_path)
        if "system_prompt" in cfg:
            sp = cfg["system_prompt"]
            sp = sp.replace(self._pet_config.get("owner_name", "小主人"), owner_name)
            sp = sp.replace(self._pet_config.get("dog_name", "旺财"), dog_name)
            # 也替换 {owner_name} 和 {pet_name} 占位符
            sp = sp.replace("{owner_name}", owner_name)
            sp = sp.replace("{pet_name}", dog_name)
            cfg["system_prompt"] = sp
            _save_json(cfg_path, cfg)

    def _set_style(self):
        """设置样式"""
        self.setStyleSheet("""
            QDialog {
                background-color: #fff8f0;
            }
            QLabel {
                font-family: "Microsoft YaHei";
                color: #333333;
            }
            QTabWidget::pane {
                border: 1px solid #e0d5c0;
                background: #fff8f0;
                border-radius: 6px;
            }
            QTabBar::tab {
                background: #f5efe0;
                border: 1px solid #e0d5c0;
                padding: 8px 16px;
                border-radius: 6px 6px 0 0;
                font-size: 13px;
                color: #555555;
            }
            QTabBar::tab:selected {
                background: #fff8f0;
                border-bottom: 2px solid #ff9a56;
                font-weight: bold;
                color: #d4753b;
            }
            QGroupBox {
                border: 1px solid #e8d5b0;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
                color: #333333;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: #8b6914;
            }
            QLineEdit {
                border: 1px solid #d5c5a0;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 13px;
                background: #fff;
                color: #333333;
            }
            QLineEdit:focus {
                border-color: #ff9a56;
            }
            QTextEdit {
                border: 1px solid #d5c5a0;
                border-radius: 4px;
                padding: 6px 8px;
                font-size: 12px;
                background: #fff;
                color: #333333;
                font-family: "Microsoft YaHei";
            }
            QTextEdit:focus {
                border-color: #ff9a56;
            }
            QPushButton {
                background: #ff9a56;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #ff8533;
            }
            QPushButton#cancelBtn {
                background: #e0d5c0;
                color: #555555;
            }
            QPushButton#cancelBtn:hover {
                background: #d5c5a0;
                color: #333333;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)


def open_settings_dialog(parent=None):
    """打开设置对话框"""
    dlg = SettingsDialog(parent)
    dlg.exec()
    # 返回后通知主程序重载配置
    from pet_config_loader import reload_pet_config
    reload_pet_config()