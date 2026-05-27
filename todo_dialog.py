"""待办事项对话框 - 查看、添加、删除待办事项"""

from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QListWidget, QListWidgetItem, QLineEdit,
    QDialog, QFormLayout, QDateTimeEdit, QMessageBox,
    QCheckBox, QFrame, QSizePolicy, QStyle,
)
from PySide6.QtCore import Qt, QDateTime, QSize, Signal
from PySide6.QtGui import QFont, QIcon, QColor, QPalette

from todo_manager import get_todo_manager, TodoItem


class AddTodoDialog(QDialog):
    """添加待办事项对话框"""

    def __init__(self, parent=None, default_title: str = "",
                 default_due: datetime | None = None):
        super().__init__(parent)
        self.setWindowTitle("添加待办事项 📋")
        self.setFixedSize(520, 270)
        # 确保对话框显示在最前
        self.setWindowFlags(
            Qt.Dialog | Qt.WindowStaysOnTopHint
        )
        self._setup_ui(default_title, default_due)
        self._set_style()

    def _setup_ui(self, default_title: str, default_due: datetime | None):
        layout = QFormLayout(self)
        layout.setSpacing(12)

        # 标题
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("输入待办事项内容...")
        if default_title:
            self.title_input.setText(default_title)
        self.title_input.setMinimumHeight(32)
        layout.addRow(QLabel("📝 事项："), self.title_input)

        # 时间
        self.time_input = QDateTimeEdit()
        self.time_input.setCalendarPopup(True)
        self.time_input.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.time_input.setMinimumHeight(32)
        if default_due:
            self.time_input.setDateTime(QDateTime(
                default_due.year, default_due.month, default_due.day,
                default_due.hour, default_due.minute, 0
            ))
        else:
            # 默认设为半小时后
            default = datetime.now() + timedelta(minutes=30)
            self.time_input.setDateTime(QDateTime(
                default.year, default.month, default.day,
                default.hour, default.minute, 0
            ))
        layout.addRow(QLabel("⏰ 提醒时间："), self.time_input)

        # 快捷时间按钮
        quick_layout = QHBoxLayout()
        quick_layout.setSpacing(4)
        quick_times = [
            ("+5分钟", 5),
            ("+15分钟", 15),
            ("+30分钟", 30),
            ("+1小时", 60),
            ("+2小时", 120),
            ("明天9:00", -1),
        ]
        for label, minutes in quick_times:
            btn = QPushButton(label)
            btn.setFixedSize(78, 30)
            btn.setObjectName("quickBtn")
            if minutes == -1:
                btn.clicked.connect(self._set_tomorrow_9am)
            else:
                btn.clicked.connect(
                    lambda checked, m=minutes: self._add_minutes(m)
                )
            quick_layout.addWidget(btn)
        layout.addRow(QLabel("快捷："), quick_layout)

        # 按钮
        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("✅ 添加")
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton("❌ 取消")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.ok_btn)
        layout.addRow(btn_layout)

    def _add_minutes(self, minutes: int):
        now = datetime.now()
        due = now + timedelta(minutes=minutes)
        self.time_input.setDateTime(QDateTime(
            due.year, due.month, due.day, due.hour, due.minute, 0
        ))

    def _set_tomorrow_9am(self):
        now = datetime.now()
        tomorrow = now + timedelta(days=1)
        due = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
        self.time_input.setDateTime(QDateTime(
            due.year, due.month, due.day, due.hour, due.minute, 0
        ))

    def get_values(self) -> tuple[str, datetime]:
        """返回 (标题, 到期时间)"""
        dt = self.time_input.dateTime()
        due = datetime(dt.date().year(), dt.date().month(), dt.date().day(),
                       dt.time().hour(), dt.time().minute())
        return self.title_input.text().strip(), due

    def _set_style(self):
        self.setStyleSheet("""
            AddTodoDialog {
                background-color: #fffaf5;
            }
            QLabel {
                font-size: 13px;
                font-family: "Microsoft YaHei";
                color: #555;
            }
            QLineEdit {
                background-color: #ffffff;
                border: 2px solid #f0d0a0;
                border-radius: 8px;
                padding: 6px 10px;
                font-size: 13px;
                font-family: "Microsoft YaHei";
                color: #333;
            }
            QLineEdit:focus {
                border-color: #e8a040;
            }
            QDateTimeEdit {
                background-color: #ffffff;
                border: 2px solid #f0d0a0;
                border-radius: 8px;
                padding: 6px 10px;
                font-size: 13px;
                font-family: "Microsoft YaHei";
                color: #333;
            }
            QDateTimeEdit:focus {
                border-color: #e8a040;
            }
            QPushButton#quickBtn {
                background-color: #f5c070;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 2px 6px;
                font-size: 11px;
                font-weight: bold;
                font-family: "Microsoft YaHei";
            }
            QPushButton#quickBtn:hover {
                background-color: #f0a840;
            }
            QPushButton {
                background-color: #f5a040;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: bold;
                font-family: "Microsoft YaHei";
            }
            QPushButton:hover {
                background-color: #e89030;
            }
            QPushButton:pressed {
                background-color: #d88020;
            }
        """)


class TodoItemWidget(QWidget):
    """单个待办事项的自定义 Widget，包含完成按钮"""
    completed_signal = Signal(str)  # 发出 todo_id
    delete_signal = Signal(str)     # 发出 todo_id

    def __init__(self, item: TodoItem, parent=None):
        super().__init__(parent)
        self._todo_id = item.id
        self._item = item
        self._setup_ui(item)

    def _setup_ui(self, item: TodoItem):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(6)

        # 左侧：完成按钮（像 Microsoft To Do 的圆形按钮）
        self.complete_btn = QPushButton()
        self.complete_btn.setFixedSize(24, 24)
        self.complete_btn.setCursor(Qt.PointingHandCursor)
        if item.completed:
            self.complete_btn.setText("✅")
            self.complete_btn.setToolTip("已完成")
        elif item.is_past and not item.notified:
            self.complete_btn.setText("⚠️")
            self.complete_btn.setToolTip("已过期，点击完成")
        elif item.notified:
            self.complete_btn.setText("🔔")
            self.complete_btn.setToolTip("已提醒，点击完成")
        elif item.is_past:
            self.complete_btn.setText("⏰")
            self.complete_btn.setToolTip("已过期，点击完成")
        else:
            self.complete_btn.setText("○")
            self.complete_btn.setToolTip("点击完成")
        self.complete_btn.clicked.connect(self._on_complete)
        self.complete_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 2px solid #e0c080;
                border-radius: 12px;
                font-size: 12px;
                color: #555;
            }
            QPushButton:hover {
                background-color: #e8f5e9;
                border-color: #4caf50;
                color: #4caf50;
            }
        """)
        layout.addWidget(self.complete_btn)

        # 中间：标题和时间
        text_layout = QVBoxLayout()
        text_layout.setSpacing(1)

        title_label = QLabel(item.title)
        title_label.setWordWrap(True)
        title_font = QFont("Microsoft YaHei", 12)
        if item.completed:
            title_font.setStrikeOut(True)
            title_label.setStyleSheet("color: #aaa;")
        else:
            title_label.setStyleSheet("color: #333;")
        title_label.setFont(title_font)
        text_layout.addWidget(title_label)

        due_str = item.due_time.strftime("%m/%d %H:%M")
        due_label = QLabel(f"⏰ {due_str}")
        due_label.setFont(QFont("Microsoft YaHei", 9))
        if item.completed:
            due_label.setStyleSheet("color: #bbb;")
        elif item.is_past and not item.notified:
            due_label.setStyleSheet("color: #e04040; font-weight: bold;")
        elif item.notified:
            due_label.setStyleSheet("color: #e8a040;")
        elif item.is_past:
            due_label.setStyleSheet("color: #e04040;")
        else:
            due_label.setStyleSheet("color: #888;")
        text_layout.addWidget(due_label)

        layout.addLayout(text_layout, 1)

        # 右侧：删除按钮
        self.delete_btn = QPushButton("🗑️")
        self.delete_btn.setFixedSize(28, 28)
        self.delete_btn.setCursor(Qt.PointingHandCursor)
        self.delete_btn.setToolTip("删除此待办")
        self.delete_btn.clicked.connect(self._on_delete)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #ffebee;
            }
        """)
        layout.addWidget(self.delete_btn)

    def _on_complete(self):
        self.completed_signal.emit(self._todo_id)

    def _on_delete(self):
        self.delete_signal.emit(self._todo_id)


class TodoDialog(QWidget):
    """待办事项主对话框"""

    def __init__(self, parent=None):
        super().__init__(None, Qt.Window | Qt.WindowStaysOnTopHint)
        self.setWindowTitle("待办事项 📋")
        self.setMinimumSize(440, 480)
        self.resize(460, 540)

        self._setup_window_icon()
        self._init_ui()
        self._set_style()
        self.refresh_list()

    def _setup_window_icon(self):
        """设置窗口图标"""
        try:
            from main import _create_dog_icon
            self.setWindowIcon(QIcon(_create_dog_icon(64)))
        except Exception:
            pass

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # 标题
        title = QLabel("📋 待办事项")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #555;")
        layout.addWidget(title)

        # 提示标签
        tip = QLabel("点击 ○ 按钮即可完成待办，随时管理你的任务~")
        tip.setAlignment(Qt.AlignCenter)
        tip.setStyleSheet("color: #999; font-size: 11px;")
        layout.addWidget(tip)

        # 分隔线
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #f0d0a0;")
        layout.addWidget(sep)

        # 待办列表
        self.todo_list = QListWidget()
        self.todo_list.setMinimumHeight(200)
        self.todo_list.setAlternatingRowColors(True)
        self.todo_list.setSpacing(2)
        layout.addWidget(self.todo_list, 1)

        # 按钮区域
        btn_layout = QHBoxLayout()

        self.add_btn = QPushButton("➕ 添加待办")
        self.add_btn.setMinimumHeight(36)
        self.add_btn.clicked.connect(self._add_todo)
        btn_layout.addWidget(self.add_btn, 1)

        self.complete_btn = QPushButton("✅ 完成选中")
        self.complete_btn.clicked.connect(self._complete_todo)
        btn_layout.addWidget(self.complete_btn)

        self.delete_btn = QPushButton("🗑️ 删除选中")
        self.delete_btn.clicked.connect(self._delete_todo)
        btn_layout.addWidget(self.delete_btn)

        layout.addLayout(btn_layout)

        # 底部
        bottom_layout = QHBoxLayout()

        self.refresh_btn = QPushButton("🔄 刷新")
        self.refresh_btn.clicked.connect(self.refresh_list)
        bottom_layout.addWidget(self.refresh_btn)

        self.show_done_cb = QCheckBox("显示已完成")
        self.show_done_cb.stateChanged.connect(self.refresh_list)
        bottom_layout.addWidget(self.show_done_cb)

        bottom_layout.addStretch()

        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.close)
        bottom_layout.addWidget(self.close_btn)

        layout.addLayout(bottom_layout)

    def refresh_list(self):
        """刷新待办事项列表"""
        self.todo_list.clear()
        mgr = get_todo_manager()
        items = mgr.get_all(include_completed=self.show_done_cb.isChecked())

        # 排序：未完成的在前，按到期时间排序
        active = [t for t in items if not t.completed]
        done = [t for t in items if t.completed]
        active.sort(key=lambda t: t.due_time)
        done.sort(key=lambda t: t.due_time, reverse=True)
        items = active + done

        for item in items:
            self._add_item_to_list(item)

    def _add_item_to_list(self, item: TodoItem):
        """将待办事项添加到列表控件（使用自定义 Widget）"""
        widget = TodoItemWidget(item)
        widget.completed_signal.connect(self._on_item_completed)
        widget.delete_signal.connect(self._on_item_deleted)
        # 强制布局，确保 sizeHint 正确（否则文字可能不可见）
        widget.setFixedHeight(56)
        widget.adjustSize()

        list_item = QListWidgetItem()
        list_item.setData(Qt.UserRole, item.id)
        list_item.setSizeHint(QSize(0, 56))

        self.todo_list.addItem(list_item)
        self.todo_list.setItemWidget(list_item, widget)

    def _on_item_completed(self, todo_id: str):
        """处理单项完成按钮点击"""
        mgr = get_todo_manager()
        for item in mgr.get_all():
            if item.id == todo_id:
                if item.completed:
                    QMessageBox.information(self, "提示", "该事项已经完成了~")
                else:
                    mgr.complete(todo_id)
                    self.refresh_list()
                return

    def _on_item_deleted(self, todo_id: str):
        """处理单项删除按钮点击"""
        reply = QMessageBox.question(
            self, "确认删除",
            "确定要删除这个待办事项吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            get_todo_manager().remove(todo_id)
            self.refresh_list()

    def _add_todo(self):
        """打开添加待办事项对话框"""
        dlg = AddTodoDialog(None)
        if dlg.exec() == QDialog.Accepted:
            title, due = dlg.get_values()
            if not title:
                QMessageBox.warning(self, "提示", "请输入待办事项内容！")
                return
            if due <= datetime.now():
                QMessageBox.warning(
                    self, "提示",
                    "提醒时间不能是过去的时间，请重新设置！"
                )
                return
            get_todo_manager().add(title, due)
            self.refresh_list()

    def _complete_todo(self):
        """标记选中项为完成"""
        current = self.todo_list.currentItem()
        if not current:
            QMessageBox.information(self, "提示", "请先选择一个待办事项！")
            return
        todo_id = current.data(Qt.UserRole)
        mgr = get_todo_manager()
        for item in mgr.get_all():
            if item.id == todo_id:
                if item.completed:
                    QMessageBox.information(self, "提示", "该事项已经完成了~")
                else:
                    mgr.complete(todo_id)
                    self.refresh_list()
                return

    def _delete_todo(self):
        """删除选中的待办事项"""
        current = self.todo_list.currentItem()
        if not current:
            QMessageBox.information(self, "提示", "请先选择一个待办事项！")
            return
        todo_id = current.data(Qt.UserRole)
        reply = QMessageBox.question(
            self, "确认删除",
            "确定要删除这个待办事项吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            get_todo_manager().remove(todo_id)
            self.refresh_list()

    def _set_style(self):
        self.setStyleSheet("""
            TodoDialog {
                background-color: #fffaf5;
            }
            QLabel {
                font-family: "Microsoft YaHei";
                color: #555;
            }
            QListWidget {
                background-color: #ffffff;
                border: 2px solid #f0d0a0;
                border-radius: 10px;
                padding: 4px;
                font-size: 13px;
                font-family: "Microsoft YaHei";
            }
            QListWidget::item {
                padding: 3px 6px;
                border-bottom: 1px solid #f5e8d0;
                background-color: #ffffff;
            }
            QListWidget::item:selected {
                background-color: #fff5e8;
            }
            QListWidget::item:alternate {
                background-color: #fffdf8;
            }
            QPushButton {
                background-color: #f5a040;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: bold;
                font-family: "Microsoft YaHei";
            }
            QPushButton:hover {
                background-color: #e89030;
            }
            QPushButton:pressed {
                background-color: #d88020;
            }
            QCheckBox {
                font-size: 12px;
                font-family: "Microsoft YaHei";
                color: #555;
            }
        """)


# 全局引用，防止被 GC
_todo_dialog: TodoDialog | None = None


def open_todo_dialog(parent=None) -> TodoDialog:
    """打开或显示待办事项对话框"""
    global _todo_dialog
    if _todo_dialog is None:
        _todo_dialog = TodoDialog(parent)
    if _todo_dialog.isMinimized():
        _todo_dialog.showNormal()
    else:
        _todo_dialog.show()
    _todo_dialog.raise_()
    _todo_dialog.activateWindow()
    _todo_dialog.refresh_list()
    return _todo_dialog