"""Desktop Dog - 桌面互动狗狗
一只可爱的柴犬，住在你的桌面上！
支持：摸摸头、拖动、散步、系统托盘"""

import sys
import random
import math
import ctypes
from ctypes import wintypes
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QWidget, QSystemTrayIcon, QMenu,
    QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit,
    QPushButton, QLabel,
)
from PySide6.QtCore import (
    Qt, QTimer, QPoint, QPointF, QRect, QSize,
    Signal, QThread, QEvent,
)
from PySide6.QtGui import (
    QPainter, QColor, QPen, QPainterPath,
    QPixmap, QIcon, QAction, QFont, QTextCursor,
)

from ai_chat import get_chat
from todo_manager import get_todo_manager
from todo_dialog import open_todo_dialog
from pet_config_loader import get_pet_config

from PySide6.QtWidgets import QMessageBox

# ========== 常量 ==========
WIDGET_SIZE = 260
FPS = 60
FRAME_INTERVAL = 1000 // FPS
DOG_VY = 55   # 狗整体下移，给气泡留空间
DOG_CX = 30   # 狗整体右移，使在扩大的窗口中居中（原中心100→130）

# 缩放
SCALE_DEFAULT = 1.0
SCALE_MIN = 0.3
SCALE_MAX = 3.0
SCALE_STEP = 0.1

# 狗狗颜色 - 可爱柴犬配色（软萌版）
COLOR_FUR = QColor(245, 175, 85)          # 软萌橙色（主体）
COLOR_FUR_DARK = QColor(205, 135, 45)     # 轮廓棕
COLOR_FUR_SHADOW = QColor(225, 155, 55)   # 阴影橙
COLOR_FUR_HIGHLIGHT = QColor(255, 205, 120)  # 受光面高光
COLOR_FUR_TOP = QColor(253, 200, 105)     # 头顶暖阳高光
COLOR_CREAM = QColor(255, 252, 248)       # 奶油白（肚皮/脸）
COLOR_CREAM_DARK = QColor(248, 242, 235)  # 奶油暗部
COLOR_NOSE = QColor(55, 38, 32)           # 鼻子深棕
COLOR_NOSE_HIGHLIGHT = QColor(105, 80, 65) # 鼻子高光
COLOR_EYE = QColor(38, 32, 28)            # 眼睛深棕
COLOR_EYE_HIGHLIGHT = QColor(255, 255, 255) # 眼睛主高光
COLOR_EYE_SHINE = QColor(230, 245, 255)   # 眼睛环境光反射
COLOR_EYE_SHINE2 = QColor(200, 225, 250)  # 眼睛辅助反光
COLOR_TONGUE = QColor(252, 148, 162)     # 舌头粉
COLOR_MOUTH = QColor(125, 100, 85)       # 嘴巴线条
COLOR_INNER_EAR = QColor(252, 205, 190)  # 内耳粉
COLOR_INNER_EAR_DARK = QColor(242, 185, 170) # 内耳深粉
COLOR_COLLAR = QColor(220, 60, 60)       # 项圈红
COLOR_COLLAR_DARK = QColor(175, 35, 35)  # 项圈暗红
COLOR_BELL = QColor(255, 225, 35)        # 铃铛金
COLOR_BELL_HIGHLIGHT = QColor(255, 248, 180) # 铃铛高光
COLOR_BLUSH = QColor(255, 180, 180, 100) # 腮红
COLOR_PAW_PAD = QColor(238, 160, 170)    # 爪垫粉红
COLOR_PAW_PAD_DARK = QColor(215, 135, 145) # 爪垫深粉
COLOR_BROWN_LINE = QColor(185, 130, 70)  # 分界线棕

# 状态
STATE_IDLE = 0
STATE_WALKING = 1
STATE_HAPPY = 2
STATE_SLEEPING = 3
STATE_SITTING = 4


# ========== 粒子系统 ==========
class HeartParticle:
    """爱心粒子"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-0.6, 0.6)
        self.vy = random.uniform(-2.5, -1.0)
        self.life = random.randint(40, 80)
        self.max_life = self.life
        self.size = random.uniform(8, 16)

    @property
    def alive(self):
        return self.life > 0

    @property
    def opacity(self):
        return self.life / self.max_life

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.02  # 轻微重力
        self.life -= 1


class ZParticle:
    """Z字粒子（睡觉时）"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vy = random.uniform(-1.5, -0.8)
        self.vx = random.uniform(-0.3, 0.3)
        self.life = random.randint(60, 120)
        self.max_life = self.life

    @property
    def alive(self):
        return self.life > 0

    @property
    def opacity(self):
        return self.life / self.max_life

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1


class SpeechBubble:
    """对话气泡"""
    def __init__(self, text, x, y, is_annoyed=False):
        self.text = text
        self.x = x
        self.y = y
        self.life = 300  # 5秒
        self.max_life = self.life
        self.is_annoyed = is_annoyed

    @property
    def alive(self):
        return self.life > 0

    @property
    def opacity(self):
        if self.life > 60:
            return 1.0
        else:
            return self.life / 60

    def update(self):
        self.life -= 1


# ========== 桌面狗狗 ==========
class DesktopDog(QWidget):
    """桌面狗狗主组件"""

    def __init__(self):
        super().__init__()
        self._init_window()
        self._init_state()
        self._init_timers()
        self._init_position()

    # ---------- 初始化 ----------

    def _init_window(self):
        self.scale = SCALE_DEFAULT

        # 确保尽早创建 native window，保证 DWM 属性设置时机正确
        self.setAttribute(Qt.WA_NativeWindow, True)
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.NoDropShadowWindowHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setContentsMargins(0, 0, 0, 0)
        self.setAutoFillBackground(False)

        self._update_window_size()

        p = self.palette()
        p.setColor(self.backgroundRole(), QColor(0, 0, 0, 0))
        self.setPalette(p)

    def _update_window_size(self):
        base = int(WIDGET_SIZE * self.scale)
        self.setFixedSize(base, base)

    def set_zoom(self, new_scale):
        """设置缩放，保持狗的中心位置不变"""
        if new_scale < SCALE_MIN or new_scale > SCALE_MAX:
            return
        old_center = self.geometry().center()
        self.scale = new_scale
        self._update_window_size()
        new_center = QPoint(
            old_center.x() - self.width() // 2,
            old_center.y() - self.height() // 2,
        )
        screen = QApplication.primaryScreen().availableGeometry()
        new_center.setX(max(0, min(new_center.x(), screen.width() - self.width())))
        new_center.setY(max(0, min(new_center.y(), screen.height() - self.height())))
        self.move(new_center)
        # 重新设置 DWM 属性
        QTimer.singleShot(0, self._disable_dwm_nc)

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self._disable_dwm_nc)

    def _disable_dwm_nc(self):
        """完全消除窗口边框（Win11 DWM 属性 + 样式剥离）"""
        try:
            hwnd = int(self.winId())
            # -------------------------------
            # DWM 属性常量
            # -------------------------------
            DWMWA_COLOR_NONE = 0xFFFFFFFE
            DWMWA_BORDER_COLOR = 34
            DWMWA_CAPTION_COLOR = 35
            DWMWA_TEXT_COLOR = 36
            DWMWA_WINDOW_CORNER_PREFERENCE = 33
            DWMWCP_DONOTROUND = 1
            DWMWA_NCRENDERING_POLICY = 2
            DWMNCRP_DISABLED = 1

            none_color = ctypes.c_uint(DWMWA_COLOR_NONE)

            # 1. 禁用 DWM 非客户区渲染（最彻底：连阴影/圆角一起关）
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                wintypes.HWND(hwnd),
                ctypes.c_uint(DWMWA_NCRENDERING_POLICY),
                ctypes.byref(ctypes.c_int(DWMNCRP_DISABLED)),
                ctypes.sizeof(ctypes.c_int()),
            )
            # 2. 边框颜色设为 NONE → 不绘制任何 DWM 描边
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                wintypes.HWND(hwnd),
                ctypes.c_uint(DWMWA_BORDER_COLOR),
                ctypes.byref(none_color),
                ctypes.sizeof(ctypes.c_uint()),
            )
            # 3. 标题栏/文字颜色也设为 NONE，避免某些主题残留描边
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                wintypes.HWND(hwnd),
                ctypes.c_uint(DWMWA_CAPTION_COLOR),
                ctypes.byref(none_color),
                ctypes.sizeof(ctypes.c_uint()),
            )
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                wintypes.HWND(hwnd),
                ctypes.c_uint(DWMWA_TEXT_COLOR),
                ctypes.byref(none_color),
                ctypes.sizeof(ctypes.c_uint()),
            )
            # 4. Win11 禁用圆角（圆角边缘也可能像细边框）
            corner = ctypes.c_int(DWMWCP_DONOTROUND)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                wintypes.HWND(hwnd),
                ctypes.c_uint(DWMWA_WINDOW_CORNER_PREFERENCE),
                ctypes.byref(corner),
                ctypes.sizeof(ctypes.c_int()),
            )
            # 5. 剥离 Win32 标准样式边框位
            GWL_STYLE = -16
            GWL_EXSTYLE = -20
            WS_BORDER = 0x00800000
            WS_DLGFRAME = 0x00400000
            WS_THICKFRAME = 0x00040000
            WS_EX_CLIENTEDGE = 0x00000200
            WS_EX_STATICEDGE = 0x00020000
            WS_EX_WINDOWEDGE = 0x00000100

            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_STYLE)
            style &= ~(WS_BORDER | WS_DLGFRAME | WS_THICKFRAME)
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_STYLE, style)

            ex_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            ex_style &= ~(WS_EX_CLIENTEDGE | WS_EX_STATICEDGE | WS_EX_WINDOWEDGE)
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style)

            # 6. 通知系统刷新窗口框架
            SWP_FRAMECHANGED = 0x0020
            SWP_NOMOVE = 0x0002
            SWP_NOSIZE = 0x0001
            SWP_NOZORDER = 0x0004
            SWP_NOOWNERZORDER = 0x0200
            ctypes.windll.user32.SetWindowPos(
                wintypes.HWND(hwnd), None,
                0, 0, 0, 0,
                SWP_FRAMECHANGED | SWP_NOMOVE | SWP_NOSIZE |
                SWP_NOZORDER | SWP_NOOWNERZORDER,
            )
        except Exception:
            pass

    def _init_state(self):
        self.state = STATE_IDLE
        self.frame_count = 0
        self.state_timer = 0

        # 眨眼
        self.blink_timer = 0
        self.is_blinking = False
        self.blink_duration = 8

        # 走路
        self.target_x = 0
        self.target_y = 0
        self.walk_speed = 2.5

        # 拖动
        self.dragging = False
        self.drag_offset = QPoint()
        self._drag_start_global = QPoint()

        # 粒子
        self.particles = []

        # 对话气泡
        self.speech_bubbles = []

        # 摸摸追踪
        self.pet_count = 0
        self.pet_cooldown_timer = 0
        self.is_annoyed = False

        # 随机行为计时器（帧计数）
        self.idle_action_timer = random.randint(200, 500)

        # 整点/喝水/节日追踪
        self._last_hour_triggered = -1
        self._last_water_hour = -1
        self._special_date_done = False  # 当天节日祝福是否已触发

    def _init_timers(self):
        # 动画时钟 60fps
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._update_frame)
        self.anim_timer.start(FRAME_INTERVAL)

        # 随机行为时钟
        self.behavior_timer = QTimer(self)
        self.behavior_timer.timeout.connect(self._random_behavior)
        self.behavior_timer.start(1500)

        # 整点/喝水/节日检查时钟（每5秒检查一次）
        self.hourly_timer = QTimer(self)
        self.hourly_timer.timeout.connect(self._check_timed_events)
        self.hourly_timer.start(5000)

        # 首次立即检查
        QTimer.singleShot(500, self._check_timed_events)

        # 待办事项检查时钟（每10秒检查一次）
        self.todo_timer = QTimer(self)
        self.todo_timer.timeout.connect(self._check_todos)
        self.todo_timer.start(10000)

        QTimer.singleShot(1000, self._check_todos)

    def _init_position(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(
            screen.width() - self.width() - 80,
            screen.height() - self.height() - 120,
        )

    # ---------- 帧更新 ----------

    def _update_frame(self):
        self.frame_count += 1
        self.state_timer += 1

        # 眨眼逻辑
        if self.state in (STATE_IDLE, STATE_SITTING):
            self.blink_timer += 1
            if not self.is_blinking:
                if self.blink_timer > random.randint(180, 300):
                    self.is_blinking = True
                    self.blink_timer = 0
            else:
                if self.blink_timer > self.blink_duration:
                    self.is_blinking = False
                    self.blink_timer = 0

        # 更新粒子
        for p in self.particles[:]:
            p.update()
            if not p.alive:
                self.particles.remove(p)

        # 更新对话气泡
        for b in self.speech_bubbles[:]:
            b.update()
            if not b.alive:
                self.speech_bubbles.remove(b)

        # 摸摸冷却计时
        if self.pet_cooldown_timer > 0:
            self.pet_cooldown_timer -= 1
            if self.pet_cooldown_timer <= 0:
                self.pet_count = 0
                self.is_annoyed = False

        # 状态更新
        if self.state == STATE_WALKING:
            self._update_walking()
        elif self.state == STATE_HAPPY:
            if self.state_timer > 120:
                self._set_state(STATE_IDLE)
        elif self.state == STATE_SLEEPING:
            # 偶尔冒Z
            if self.frame_count % 30 == 0 and random.random() < 0.6:
                self.particles.append(
                    ZParticle(random.uniform(115, 140),
                              random.uniform(130, 150))
                )

        # 随机空闲行为
        if self.state == STATE_IDLE:
            self.idle_action_timer -= 1
            if self.idle_action_timer <= 0:
                self._do_random_action()
                self.idle_action_timer = random.randint(300, 800)

        self.update()

    def _set_state(self, new_state):
        self.state = new_state
        self.state_timer = 0

    def _update_walking(self):
        dx = self.target_x - self.x()
        dy = self.target_y - self.y()
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < 5:
            self._set_state(STATE_IDLE)
            return
        step = min(self.walk_speed, dist)
        new_x = self.x() + (dx / dist) * step
        new_y = self.y() + (dy / dist) * step
        screen = QApplication.primaryScreen().availableGeometry()
        new_x = max(0, min(new_x, screen.width() - self.width()))
        new_y = max(0, min(new_y, screen.height() - self.height()))
        self.move(int(new_x), int(new_y))

    # ---------- 行为 ----------

    def _random_behavior(self):
        if self.state == STATE_SITTING and self.state_timer > 300:
            if random.random() < 0.3:
                self._set_state(STATE_IDLE)

    def _do_random_action(self):
        r = random.random()
        if r < 0.4:
            self._set_state(STATE_HAPPY)
        elif r < 0.55:
            self._set_state(STATE_SITTING)

    # ---------- 定时事件 ----------

    def _check_timed_events(self):
        """每15秒检查整点情话、喝水提醒、节假日祝福"""
        cfg = get_pet_config()
        now = datetime.now()
        hour = now.hour
        minute = now.minute
        month = now.month
        day = now.day

        # 1. 节日/生日祝福（每天仅触发一次，在早上9点后）
        if not self._special_date_done and hour >= 9:
            key = f"{month}-{day}"
            if key in cfg.special_dates:
                text = random.choice(cfg.special_dates[key])
                self._show_timed_bubble(text)
                self._special_date_done = True
                return  # 一次只触发一条，避免堆叠

        # 2. 整点情话（每小时整点触发一次）
        if 0 <= minute < 2 and hour != self._last_hour_triggered:
            self._last_hour_triggered = hour
            if cfg.love_phrases:
                text = random.choice(cfg.love_phrases)
                self._show_timed_bubble(text)
                return

        # 3. 喝水提醒（每3小时一次，在整点触发）
        water_interval = 3
        if hour % water_interval == 0 and 0 <= minute < 2 and hour != self._last_water_hour:
            self._last_water_hour = hour
            if 9 <= hour <= 21 and cfg.water_reminders:  # 只在白天提醒
                text = random.choice(cfg.water_reminders)
                self._show_timed_bubble(text)
                return

    def _show_timed_bubble(self, text):
        """显示定时触发的对话气泡"""
        if self.isVisible():
            self._set_state(STATE_HAPPY)
            self.speech_bubbles.clear()
            self.speech_bubbles.append(SpeechBubble(text, 100, 48, is_annoyed=False))
            # 爱心粒子
            for _ in range(8):
                self.particles.append(
                    HeartParticle(
                        random.uniform(70, 130),
                        random.uniform(60 + DOG_VY, 90 + DOG_VY)
                    )
                )

    def _check_todos(self):
        """检查待办事项，到期弹窗提醒"""
        mgr = get_todo_manager()
        due_todos = mgr.get_due_todos()
        for todo in due_todos:
            self._show_todo_notification(todo)
            mgr.mark_notified(todo.id)

    def _show_todo_notification(self, todo):
        """弹窗提醒到期待办事项"""
        from todo_manager import TodoItem
        due_str = todo.due_time.strftime("%Y-%m-%d %H:%M")
        msg = QMessageBox(self)
        msg.setWindowTitle("⏰ 待办提醒")
        msg.setText(f"<b>⏰ 待办事项时间到！</b>")
        msg.setInformativeText(
            f"📋 {todo.title}\n\n⏰ 设定时间：{due_str}"
        )
        msg.setIcon(QMessageBox.Information)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setWindowFlags(Qt.WindowStaysOnTopHint)
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #fffaf5;
                font-size: 14px;
                font-family: "Microsoft YaHei";
            }
            QPushButton {
                background-color: #f5a040;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 20px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e89030;
            }
        """)
        msg.show()

        # 同时在狗狗头顶显示气泡
        self.speech_bubbles.clear()
        self.speech_bubbles.append(
            SpeechBubble(f"⏰ 提醒：{todo.title}", 100, 48, is_annoyed=False)
        )
        self._set_state(STATE_HAPPY)
        for _ in range(6):
            self.particles.append(
                HeartParticle(
                    random.uniform(70, 130),
                    random.uniform(60 + DOG_VY, 90 + DOG_VY)
                )
            )

    def start_walking(self):
        screen = QApplication.primaryScreen().availableGeometry()
        margin = 50
        self.target_x = random.randint(
            margin, screen.width() - self.width() - margin
        )
        self.target_y = random.randint(
            margin, screen.height() - self.height() - margin
        )
        self._set_state(STATE_WALKING)

    def pet(self):
        """摸摸头"""
        self._set_state(STATE_HAPPY)
        # 爱心粒子从狗头周围冒出（painter翻译坐标系后狗中心在x=100）
        for _ in range(6):
            self.particles.append(
                HeartParticle(
                    random.uniform(70, 130),
                    random.uniform(60 + DOG_VY, 90 + DOG_VY)
                )
            )

        # 摸摸追踪
        cfg = get_pet_config()
        self.pet_count += 1
        self.pet_cooldown_timer = cfg.cooldown

        # 清除旧气泡，避免重叠
        self.speech_bubbles.clear()

        # 决定说什么
        if self.pet_count >= cfg.annoy_threshold:
            text = random.choice(cfg.phrases_annoyed)
            self.speech_bubbles.append(SpeechBubble(text, 100, 48, is_annoyed=True))
            self.is_annoyed = True
        else:
            r = random.random()
            if r < 0.3:
                text = self._get_time_phrase()
            else:
                text = random.choice(cfg.phrases_normal)
            self.speech_bubbles.append(SpeechBubble(text, 100, 48, is_annoyed=False))

    def _get_time_phrase(self):
        """根据时间获取问候语"""
        cfg = get_pet_config()
        now = datetime.now()
        hour = now.hour
        phrases = cfg.phrases_time
        if 5 <= hour < 11:
            if phrases.get("morning"):
                return random.choice(phrases["morning"])
        elif 11 <= hour < 13:
            if phrases.get("noon"):
                return random.choice(phrases["noon"])
        elif 13 <= hour < 17:
            if phrases.get("afternoon"):
                return random.choice(phrases["afternoon"])
        else:
            if phrases.get("evening"):
                return random.choice(phrases["evening"])
        if cfg.phrases_normal:
            return random.choice(cfg.phrases_normal)
        return "汪汪~"

    # ========== 绘制 ==========

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        # 彻底消除残留背景
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.fillRect(self.rect(), Qt.transparent)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

        # 应用缩放
        painter.scale(self.scale, self.scale)

        # 整体右移 DOG_CX 使狗在窗口中居中
        painter.translate(DOG_CX, 0)

        # 弹跳偏移
        bounce = 0
        if self.state == STATE_IDLE:
            bounce = math.sin(self.frame_count * 0.06) * 2.5
        elif self.state == STATE_HAPPY:
            decay = max(0, 1 - self.state_timer / 120)
            bounce = math.sin(self.frame_count * 0.25) * 8 * decay
        elif self.state == STATE_WALKING:
            bounce = math.sin(self.frame_count * 0.3) * 3
        elif self.state == STATE_SITTING:
            bounce = 0

        if self.state == STATE_SLEEPING:
            self._draw_sleeping_dog(painter)
        else:
            self._draw_shadow(painter, bounce)
            self._draw_dog(painter, int(bounce))

        self._draw_particles(painter)
        self._draw_speech_bubbles(painter)

        painter.end()

    def _draw_shadow(self, painter, bounce):
        painter.save()
        alpha = max(15, 45 - abs(bounce) * 3)
        painter.setBrush(QColor(0, 0, 0, int(alpha)))
        painter.setPen(Qt.NoPen)
        sw = 65 + abs(bounce) * 2
        sh = 10 + abs(bounce) * 0.5
        sy = 180 + DOG_VY
        painter.drawEllipse(QPoint(100, sy), int(sw), int(sh))
        painter.restore()

    def _draw_dog(self, painter, bounce):
        painter.save()
        by = bounce + DOG_VY
        self._draw_tail(painter, by)
        self._draw_body(painter, by)
        self._draw_legs(painter, by)
        self._draw_head(painter, by)
        self._draw_ears(painter, by)
        self._draw_face(painter, by)
        painter.restore()

    # --- 尾巴（蓬松大卷尾）---
    def _draw_tail(self, painter, by):
        painter.save()
        if self.state == STATE_HAPPY:
            wag = math.sin(self.frame_count * 0.35) * 30
        else:
            wag = math.sin(self.frame_count * 0.1) * 14

        tx, ty = 130, 106 + by
        painter.translate(tx, ty)
        painter.rotate(28 + wag)

        # 蓬松主尾
        tail_path = QPainterPath()
        tail_path.moveTo(0, 0)
        tail_path.cubicTo(14, -3, 26, -18, 20, -44)
        tail_path.cubicTo(16, -58, 2, -54, -4, -44)
        tail_path.cubicTo(-10, -28, -4, -10, 0, 0)
        painter.setBrush(COLOR_FUR)
        painter.setPen(QPen(COLOR_FUR_DARK, 1.5))
        painter.drawPath(tail_path)

        # 尾巴尖白色
        tip = QPainterPath()
        tip.moveTo(19, -43)
        tip.cubicTo(16, -54, 4, -54, -1, -44)
        tip.cubicTo(2, -50, 10, -50, 16, -42)
        painter.setBrush(COLOR_CREAM)
        painter.setPen(Qt.NoPen)
        painter.drawPath(tip)

        # 高光条
        hl = QPainterPath()
        hl.moveTo(-3, -16)
        hl.cubicTo(3, -24, 8, -32, 10, -28)
        hl.cubicTo(8, -22, 3, -16, -3, -16)
        painter.setBrush(COLOR_FUR_HIGHLIGHT)
        painter.setPen(Qt.NoPen)
        painter.drawPath(hl)

        painter.restore()

    # --- 身体（3D升级版）---
    def _draw_body(self, painter, by):
        painter.save()
        if self.state == STATE_SITTING:
            painter.setBrush(COLOR_FUR)
            painter.setPen(QPen(COLOR_FUR_DARK, 2))
            painter.drawEllipse(QPoint(100, 112 + by), 40, 34)

            painter.setBrush(COLOR_CREAM)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPoint(100, 120 + by), 26, 22)

            painter.setBrush(COLOR_CREAM_DARK)
            painter.drawEllipse(QPoint(100, 126 + by), 16, 10)
        else:
            body_path = QPainterPath()
            body_path.addRoundedRect(QRect(64, 98 + by, 72, 58), 28, 28)
            painter.setBrush(COLOR_FUR)
            painter.setPen(QPen(COLOR_FUR_DARK, 2))
            painter.drawPath(body_path)

            # 身体顶部高光
            hl_body = QPainterPath()
            hl_body.addRoundedRect(QRect(74, 100 + by, 52, 16), 10, 10)
            painter.setBrush(COLOR_FUR_HIGHLIGHT)
            painter.setPen(Qt.NoPen)
            painter.drawPath(hl_body)

            # 肚皮
            painter.setBrush(COLOR_CREAM)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(QRect(76, 118 + by, 48, 32), 20, 20)

            painter.setBrush(COLOR_CREAM_DARK)
            painter.drawRoundedRect(QRect(81, 132 + by, 38, 14), 12, 12)

            # 颈部奶油区域
            neck = QPainterPath()
            neck.moveTo(67, 108 + by)
            neck.cubicTo(74, 96 + by, 90, 92 + by, 100, 94 + by)
            neck.cubicTo(110, 92 + by, 126, 96 + by, 133, 108 + by)
            neck.cubicTo(122, 104 + by, 110, 102 + by, 100, 103 + by)
            neck.cubicTo(90, 102 + by, 78, 104 + by, 67, 108 + by)
            painter.setBrush(COLOR_CREAM)
            painter.drawPath(neck)

        # 项圈（双层）
        collar_y = 105 + by
        if self.state == STATE_SITTING:
            collar_y = 98 + by

        painter.setPen(QPen(COLOR_COLLAR_DARK, 6, Qt.SolidLine, Qt.RoundCap))
        painter.setBrush(Qt.NoBrush)
        painter.drawLine(70, collar_y + 1, 130, collar_y + 1)

        painter.setPen(QPen(COLOR_COLLAR, 4, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(70, collar_y, 130, collar_y)

        # 铃铛（3D版）
        bell_x, bell_y = 100, collar_y + 5
        painter.setBrush(COLOR_BELL)
        painter.setPen(QPen(QColor(200, 160, 0), 1.5))
        painter.drawEllipse(QPoint(bell_x, bell_y), 6, 6)

        painter.setPen(QPen(QColor(180, 125, 0), 1))
        painter.drawLine(bell_x - 2, bell_y + 5, bell_x + 2, bell_y + 5)
        painter.drawLine(bell_x, bell_y + 5, bell_x, bell_y + 8)

        painter.setBrush(COLOR_BELL_HIGHLIGHT)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPoint(bell_x - 1, bell_y - 2), 2, 2.5)
        painter.drawEllipse(QPoint(bell_x - 3, bell_y + 1), 1, 1)

        painter.restore()

    # --- 腿（3D升级版 + 爪垫）---
    def _draw_legs(self, painter, by):
        painter.save()
        if self.state == STATE_SITTING:
            painter.setBrush(COLOR_FUR)
            painter.setPen(QPen(COLOR_FUR_DARK, 1))
            painter.drawRoundedRect(QRect(80, 130 + by, 12, 28), 6, 6)
            painter.drawRoundedRect(QRect(108, 130 + by, 12, 28), 6, 6)

            # 腿部高光
            painter.setBrush(COLOR_FUR_HIGHLIGHT)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(QRect(82, 132 + by, 5, 8), 3, 3)
            painter.drawRoundedRect(QRect(110, 132 + by, 5, 8), 3, 3)

            # 爪子
            painter.setBrush(COLOR_CREAM)
            painter.drawRoundedRect(QRect(78, 154 + by, 16, 8), 4, 4)
            painter.drawRoundedRect(QRect(106, 154 + by, 16, 8), 4, 4)

            self._draw_paw_pads(painter, 86, 153 + by)
            self._draw_paw_pads(painter, 114, 153 + by)
        else:
            wo = 0
            if self.state == STATE_WALKING:
                wo = math.sin(self.frame_count * 0.4) * 4

            # 后腿暗部
            painter.setBrush(COLOR_FUR_DARK)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(QRect(82, 141 + by - int(wo), 12, 22 + int(abs(wo))), 6, 6)
            painter.drawRoundedRect(QRect(106, 141 + by, 12, 22), 6, 6)

            # 前腿主体
            painter.setBrush(COLOR_FUR)
            painter.setPen(QPen(COLOR_FUR_DARK, 1))
            painter.drawRoundedRect(QRect(76, 140 + by, 14, 22), 7, 7)

            painter.setBrush(COLOR_CREAM)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(QRect(74, 158 + by, 18, 8), 4, 4)
            self._draw_paw_pads(painter, 83, 157 + by)

            # 另一前腿
            painter.setBrush(COLOR_FUR)
            painter.setPen(QPen(COLOR_FUR_DARK, 1))
            rly = 140 + by + int(wo)
            rlh = max(8, 22 - int(abs(wo)))
            painter.drawRoundedRect(QRect(110, rly, 14, rlh), 7, 7)

            painter.setBrush(COLOR_CREAM)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(QRect(108, rly + rlh - 8, 18, 8), 4, 4)
            self._draw_paw_pads(painter, 117, rly + rlh - 9)

        painter.restore()

    def _draw_paw_pads(self, painter, cx, by):
        """绘制爪子肉垫"""
        pads = [(cx - 3, by - 1), (cx, by - 3), (cx + 3, by - 1)]
        painter.setBrush(COLOR_PAW_PAD)
        painter.setPen(Qt.NoPen)
        for px, py in pads:
            painter.drawEllipse(QPoint(px, py), 2, 2.5)
        painter.setBrush(COLOR_PAW_PAD_DARK)
        painter.drawEllipse(QPoint(cx, by + 3), 4, 3)

    # --- 头部（软萌chibi版）---
    def _draw_head(self, painter, by):
        painter.save()
        # 头部主体 - 大圆脸
        head_path = QPainterPath()
        head_path.moveTo(58, 45 + by)
        head_path.cubicTo(56, 14 + by, 144, 14 + by, 142, 45 + by)
        head_path.cubicTo(143, 78 + by, 130, 100 + by, 100, 100 + by)
        head_path.cubicTo(70, 100 + by, 57, 78 + by, 58, 45 + by)

        painter.setBrush(COLOR_FUR)
        painter.setPen(QPen(COLOR_FUR_DARK, 1.5))
        painter.drawPath(head_path)

        # 头顶柔和高光
        top_hl = QPainterPath()
        top_hl.moveTo(75, 24 + by)
        top_hl.cubicTo(88, 16 + by, 112, 16 + by, 125, 24 + by)
        top_hl.cubicTo(120, 22 + by, 105, 20 + by, 100, 20 + by)
        top_hl.cubicTo(95, 20 + by, 80, 22 + by, 75, 24 + by)
        painter.setBrush(COLOR_FUR_TOP)
        painter.setPen(Qt.NoPen)
        painter.drawPath(top_hl)

        # 头顶绒毛小撮
        tufts = [(85, 18), (92, 15), (100, 14), (108, 15), (115, 18)]
        painter.setPen(Qt.NoPen)
        painter.setBrush(COLOR_FUR_HIGHLIGHT)
        for tx, ty in tufts:
            painter.drawEllipse(QPoint(tx, ty + by), 4, 5)

        # 脸颊蓬松毛 - 更圆润
        painter.setPen(Qt.NoPen)
        painter.setBrush(COLOR_FUR)
        # 左脸颊毛
        cheek_l = QPainterPath()
        cheek_l.moveTo(56, 60 + by)
        cheek_l.cubicTo(40, 65 + by, 32, 82 + by, 38, 85 + by)
        cheek_l.cubicTo(42, 80 + by, 46, 74 + by, 54, 76 + by)
        cheek_l.closeSubpath()
        painter.drawPath(cheek_l)

        # 右脸颊毛
        cheek_r = QPainterPath()
        cheek_r.moveTo(144, 60 + by)
        cheek_r.cubicTo(160, 65 + by, 168, 82 + by, 162, 85 + by)
        cheek_r.cubicTo(158, 80 + by, 154, 74 + by, 146, 76 + by)
        cheek_r.closeSubpath()
        painter.drawPath(cheek_r)

        # 脸部奶油色面具 - 更大更圆润
        mask = QPainterPath()
        mask.moveTo(100, 40 + by)
        mask.cubicTo(78, 42 + by, 60, 58 + by, 62, 78 + by)
        mask.cubicTo(66, 96 + by, 86, 104 + by, 100, 104 + by)
        mask.cubicTo(114, 104 + by, 134, 96 + by, 138, 78 + by)
        mask.cubicTo(140, 58 + by, 122, 42 + by, 100, 40 + by)
        painter.setBrush(COLOR_CREAM)
        painter.drawPath(mask)

        # 脸部柔和高光
        mask_hl = QPainterPath()
        mask_hl.moveTo(100, 42 + by)
        mask_hl.cubicTo(85, 43 + by, 72, 52 + by, 74, 64 + by)
        mask_hl.cubicTo(76, 58 + by, 85, 48 + by, 100, 46 + by)
        mask_hl.cubicTo(115, 48 + by, 124, 58 + by, 126, 64 + by)
        mask_hl.cubicTo(128, 52 + by, 115, 43 + by, 100, 42 + by)
        painter.setBrush(QColor(255, 255, 255, 70))
        painter.drawPath(mask_hl)

        # 眼上眉斑 - 可爱小圆眉
        painter.setBrush(COLOR_FUR_DARK)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPoint(78, 44 + by), 9, 5)
        painter.drawEllipse(QPoint(122, 44 + by), 9, 5)

        painter.setBrush(COLOR_FUR_HIGHLIGHT)
        painter.drawEllipse(QPoint(76, 42 + by), 5, 3)
        painter.drawEllipse(QPoint(120, 42 + by), 5, 3)

        # 腮红 - 可爱圆形
        painter.setBrush(COLOR_BLUSH)
        painter.drawEllipse(QPoint(70, 72 + by), 11, 7)
        painter.drawEllipse(QPoint(130, 72 + by), 11, 7)

        painter.setBrush(QColor(255, 200, 200, 70))
        painter.drawEllipse(QPoint(70, 71 + by), 8, 5)
        painter.drawEllipse(QPoint(130, 71 + by), 8, 5)

        # 分界线 - nose bridge vertical line
        painter.setPen(QPen(COLOR_BROWN_LINE, 0.8, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(100, 42 + by, 100, 52 + by)

        # 生气时加 "井" 字符号
        if self.is_annoyed:
            painter.save()
            font = painter.font()
            font.setBold(True)
            font.setPointSize(22)
            painter.setFont(font)
            painter.setPen(QColor(200, 40, 40, 180))
            painter.drawText(36, 20 + by, "#")
            painter.drawText(142, 20 + by, "#")
            painter.restore()

        painter.restore()

    # --- 耳朵（软萌三角耳）---
    def _draw_ears(self, painter, by):
        painter.save()
        if self.state == STATE_HAPPY:
            ew = math.sin(self.frame_count * 0.3) * 5
        else:
            ew = math.sin(self.frame_count * 0.1) * 2

        annoyed_offset = -4 if self.is_annoyed else 0

        # --- 左耳 ---
        le = QPainterPath()
        le.moveTo(80, 38 + by + ew)
        le.cubicTo(70, 15 + by + ew + annoyed_offset, 55, 5 + by + ew + annoyed_offset, 52, 10 + by + ew + annoyed_offset)
        le.cubicTo(56, 22 + by + ew, 66, 35 + by + ew, 68, 38 + by + ew)
        le.closeSubpath()
        painter.setBrush(COLOR_FUR)
        painter.setPen(QPen(COLOR_FUR_DARK, 1.2))
        painter.drawPath(le)

        # 左耳高光
        le_hl = QPainterPath()
        le_hl.moveTo(78, 36 + by + ew)
        le_hl.cubicTo(70, 18 + by + ew, 58, 10 + by + ew, 56, 12 + by + ew)
        le_hl.cubicTo(60, 22 + by + ew, 68, 34 + by + ew, 70, 37 + by + ew)
        le_hl.closeSubpath()
        painter.setBrush(COLOR_FUR_HIGHLIGHT)
        painter.setPen(Qt.NoPen)
        painter.drawPath(le_hl)

        # 左耳内侧 - 更大粉色区域
        li = QPainterPath()
        li.moveTo(77, 37 + by + ew)
        li.cubicTo(68, 20 + by + ew, 58, 14 + by + ew, 56, 13 + by + ew + annoyed_offset)
        li.cubicTo(59, 24 + by + ew, 66, 35 + by + ew, 67, 37 + by + ew)
        li.closeSubpath()
        painter.setBrush(COLOR_INNER_EAR)
        painter.setPen(Qt.NoPen)
        painter.drawPath(li)

        # 左耳内侧暗部
        li_dark = QPainterPath()
        li_dark.moveTo(75, 37 + by + ew)
        li_dark.cubicTo(68, 24 + by + ew, 61, 18 + by + ew, 58, 17 + by + ew + annoyed_offset)
        li_dark.cubicTo(61, 27 + by + ew, 66, 36 + by + ew, 66, 37 + by + ew)
        li_dark.closeSubpath()
        painter.setBrush(COLOR_INNER_EAR_DARK)
        painter.setPen(Qt.NoPen)
        painter.drawPath(li_dark)

        # --- 右耳 ---
        re_ = QPainterPath()
        re_.moveTo(120, 38 + by - ew)
        re_.cubicTo(130, 15 + by - ew + annoyed_offset, 145, 5 + by - ew + annoyed_offset, 148, 10 + by - ew + annoyed_offset)
        re_.cubicTo(144, 22 + by - ew, 134, 35 + by - ew, 132, 38 + by - ew)
        re_.closeSubpath()
        painter.setBrush(COLOR_FUR)
        painter.setPen(QPen(COLOR_FUR_DARK, 1.2))
        painter.drawPath(re_)

        # 右耳高光
        re_hl = QPainterPath()
        re_hl.moveTo(122, 36 + by - ew)
        re_hl.cubicTo(130, 18 + by - ew, 142, 10 + by - ew, 144, 12 + by - ew)
        re_hl.cubicTo(140, 22 + by - ew, 132, 34 + by - ew, 130, 37 + by - ew)
        re_hl.closeSubpath()
        painter.setBrush(COLOR_FUR_HIGHLIGHT)
        painter.setPen(Qt.NoPen)
        painter.drawPath(re_hl)

        # 右耳内侧
        ri = QPainterPath()
        ri.moveTo(123, 37 + by - ew)
        ri.cubicTo(132, 20 + by - ew, 142, 14 + by - ew, 144, 13 + by - ew + annoyed_offset)
        ri.cubicTo(141, 24 + by - ew, 134, 35 + by - ew, 133, 37 + by - ew)
        ri.closeSubpath()
        painter.setBrush(COLOR_INNER_EAR)
        painter.setPen(Qt.NoPen)
        painter.drawPath(ri)

        # 右耳内侧暗部
        ri_dark = QPainterPath()
        ri_dark.moveTo(125, 37 + by - ew)
        ri_dark.cubicTo(132, 24 + by - ew, 139, 18 + by - ew, 142, 17 + by - ew + annoyed_offset)
        ri_dark.cubicTo(139, 27 + by - ew, 134, 36 + by - ew, 134, 37 + by - ew)
        ri_dark.closeSubpath()
        painter.setBrush(COLOR_INNER_EAR_DARK)
        painter.setPen(Qt.NoPen)
        painter.drawPath(ri_dark)

        painter.restore()

    # --- 脸部（Kawaii版）---
    def _draw_face(self, painter, by):
        painter.save()

        if self.is_blinking or self.state == STATE_SLEEPING:
            # 闭眼线（可爱弧形 ^ ^）
            pen = QPen(COLOR_EYE, 2.5, Qt.SolidLine, Qt.RoundCap)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            # 左闭眼
            blink_l = QPainterPath()
            blink_l.moveTo(74, 63 + by)
            blink_l.cubicTo(77, 58 + by, 87, 58 + by, 90, 63 + by)
            painter.drawPath(blink_l)
            # 右闭眼
            blink_r = QPainterPath()
            blink_r.moveTo(110, 63 + by)
            blink_r.cubicTo(113, 58 + by, 123, 58 + by, 126, 63 + by)
            painter.drawPath(blink_r)

            # 小睫毛
            painter.setPen(QPen(COLOR_EYE, 1.2, Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(76, 60 + by, 78, 57 + by)
            painter.drawLine(85, 60 + by, 86, 57 + by)
            painter.drawLine(114, 60 + by, 115, 57 + by)
            painter.drawLine(123, 60 + by, 124, 57 + by)

        elif self.is_annoyed:
            # 生气：倒八字眉 + 瞪圆眼睛
            pen = QPen(QColor(55, 25, 15), 3, Qt.SolidLine, Qt.RoundCap)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawLine(72, 50 + by, 88, 56 + by)
            painter.drawLine(128, 50 + by, 112, 56 + by)

            # 大圆眼睛（愤怒版）
            for ex, px in [(83, 85), (117, 115)]:
                painter.setBrush(QColor(255, 255, 255))
                painter.setPen(QPen(COLOR_EYE, 2.5))
                painter.drawEllipse(QPoint(ex, 63 + by), 12, 12)
                painter.setBrush(COLOR_EYE)
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(QPoint(px, 63 + by), 6, 6.5)
                painter.setBrush(COLOR_EYE_HIGHLIGHT)
                painter.drawEllipse(QPoint(ex - 1, 57 + by), 3.5, 3.5)
                painter.setBrush(COLOR_EYE_SHINE)
                painter.drawEllipse(QPoint(ex + 3, 60 + by), 2, 2)

        elif self.state == STATE_HAPPY:
            # 开心：弯弯笑眼 ^ ^
            pen = QPen(COLOR_EYE, 4, Qt.SolidLine, Qt.RoundCap)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)

            path_l = QPainterPath()
            path_l.moveTo(74, 63 + by)
            path_l.cubicTo(77, 55 + by, 87, 55 + by, 90, 63 + by)
            painter.drawPath(path_l)

            path_r = QPainterPath()
            path_r.moveTo(110, 63 + by)
            path_r.cubicTo(113, 55 + by, 123, 55 + by, 126, 63 + by)
            painter.drawPath(path_r)

        else:
            # 普通：大大圆眼睛（kawaii anime style）
            for ex, px in [(83, 85), (117, 115)]:
                # 眼白
                painter.setBrush(QColor(255, 255, 255))
                painter.setPen(QPen(COLOR_EYE, 2.2))
                painter.drawEllipse(QPoint(ex, 61 + by), 11, 13)

                # 瞳孔
                painter.setBrush(COLOR_EYE)
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(QPoint(px, 61 + by), 6, 7)

                # 三个高光点（anime sparkle）
                painter.setBrush(COLOR_EYE_HIGHLIGHT)
                painter.drawEllipse(QPoint(ex - 2, 54 + by), 3.5, 3.8)  # 主高光（左上）
                painter.drawEllipse(QPoint(ex + 3, 57 + by), 2, 2.2)   # 辅助高光

                painter.setBrush(COLOR_EYE_SHINE)
                painter.drawEllipse(QPoint(px + 2, 63 + by), 1.8, 1.5) # 底部反光

                painter.setBrush(COLOR_EYE_SHINE2)
                painter.drawEllipse(QPoint(px - 2, 59 + by), 1.2, 0.8) # 瞳孔反光

        # 鼻子（3D可爱小鼻头）
        painter.setBrush(COLOR_NOSE)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPoint(100, 73 + by), 8, 6)

        painter.setBrush(COLOR_NOSE_HIGHLIGHT)
        painter.drawEllipse(QPoint(98, 71 + by), 3.5, 2.5)

        painter.setBrush(QColor(140, 105, 90, 80))
        painter.drawEllipse(QPoint(97, 69 + by), 1.5, 1)

        # 嘴巴 - :3 可爱猫嘴
        painter.setPen(QPen(COLOR_MOUTH, 2, Qt.SolidLine, Qt.RoundCap))
        painter.setBrush(Qt.NoBrush)
        if self.is_annoyed:
            # 生气锯齿嘴
            mouth = QPainterPath()
            mouth.moveTo(86, 83 + by)
            mouth.lineTo(90, 78 + by)
            mouth.lineTo(93, 84 + by)
            mouth.lineTo(97, 79 + by)
            mouth.lineTo(100, 84 + by)
            mouth.lineTo(103, 79 + by)
            mouth.lineTo(107, 84 + by)
            mouth.lineTo(111, 78 + by)
            mouth.lineTo(114, 83 + by)
            painter.drawPath(mouth)
        else:
            # 可爱 :3 嘴（中间竖线 + 两侧弧线）
            # 左弧
            m_left = QPainterPath()
            m_left.moveTo(88, 80 + by)
            m_left.cubicTo(91, 74 + by, 97, 76 + by, 100, 79 + by)
            painter.drawPath(m_left)
            # 右弧
            m_right = QPainterPath()
            m_right.moveTo(112, 80 + by)
            m_right.cubicTo(109, 74 + by, 103, 76 + by, 100, 79 + by)
            painter.drawPath(m_right)
            # 中间小竖线（:3的3）
            painter.setPen(QPen(COLOR_MOUTH, 1.5, Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(100, 79 + by, 100, 83 + by)

        # 舌头（更可爱的粉色 ✨）
        if self.state == STATE_HAPPY and not self.is_annoyed:
            painter.setBrush(COLOR_TONGUE)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPoint(100, 86 + by), 8, 10)
            painter.setBrush(QColor(255, 170, 185, 140))
            painter.drawEllipse(QPoint(99, 84 + by), 3, 4)
            # 舌中线
            painter.setPen(QPen(QColor(235, 120, 140, 80), 0.8))
            painter.drawLine(100, 82 + by, 100, 89 + by)
        elif self.state == STATE_IDLE and self.frame_count % 150 < 25:
            painter.setBrush(COLOR_TONGUE)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPoint(100, 84 + by), 6, 7)
            painter.setPen(QPen(QColor(235, 120, 140, 70), 0.6))
            painter.drawLine(100, 81 + by, 100, 86 + by)

        painter.restore()

    # --- 睡觉状态 ---
    def _draw_sleeping_dog(self, painter):
        painter.save()
        vy = DOG_VY

        painter.setBrush(COLOR_FUR)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPoint(100, 130 + vy), 55, 45)

        painter.setBrush(COLOR_CREAM)
        painter.drawEllipse(QPoint(100, 120 + vy), 35, 25)

        painter.setBrush(COLOR_FUR)
        painter.drawEllipse(QPoint(65, 105 + vy), 14, 18)
        painter.drawEllipse(QPoint(135, 105 + vy), 14, 18)

        painter.setBrush(COLOR_INNER_EAR)
        painter.drawEllipse(QPoint(65, 105 + vy), 8, 10)
        painter.drawEllipse(QPoint(135, 105 + vy), 8, 10)

        pen = QPen(COLOR_EYE, 3, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen)
        painter.drawLine(78, 95 + vy, 92, 95 + vy)
        painter.drawLine(108, 95 + vy, 122, 95 + vy)

        painter.setBrush(COLOR_NOSE)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPoint(100, 102 + vy), 5, 4)

        breath = math.sin(self.frame_count * 0.04) * 2
        painter.setBrush(QColor(200, 200, 200, 40))
        painter.drawEllipse(QPoint(100, 170 + vy), 30 + int(breath), 6)

        painter.restore()

    # --- 粒子 ---
    def _draw_particles(self, painter):
        for p in self.particles:
            if isinstance(p, HeartParticle):
                painter.save()
                painter.setOpacity(p.opacity)
                color = QColor(255, 100, 150, int(255 * p.opacity))
                cx, cy, s = p.x, p.y, p.size
                path = QPainterPath()
                path.moveTo(cx, cy + s * 0.3)
                path.cubicTo(cx, cy - s * 0.1, cx - s * 0.5, cy - s * 0.1,
                             cx - s * 0.5, cy + s * 0.15)
                path.cubicTo(cx - s * 0.5, cy + s * 0.4, cx, cy + s * 0.7,
                             cx, cy + s * 0.7)
                path.cubicTo(cx, cy + s * 0.7, cx + s * 0.5, cy + s * 0.4,
                             cx + s * 0.5, cy + s * 0.15)
                path.cubicTo(cx + s * 0.5, cy - s * 0.1, cx, cy - s * 0.1,
                             cx, cy + s * 0.3)
                painter.setBrush(color)
                painter.setPen(Qt.NoPen)
                painter.drawPath(path)
                painter.restore()
            elif isinstance(p, ZParticle):
                painter.save()
                painter.setOpacity(p.opacity)
                font = painter.font()
                font.setPointSize(int(14 + (1 - p.opacity) * 8))
                painter.setFont(font)
                painter.setPen(QColor(100, 140, 220, int(200 * p.opacity)))
                painter.drawText(int(p.x), int(p.y), "Z")
                painter.restore()

    # --- 对话气泡 ---
    def _draw_speech_bubbles(self, painter):
        for b in self.speech_bubbles:
            if not b.alive:
                continue
            painter.save()
            painter.setOpacity(b.opacity)
            if b.is_annoyed:
                bg_color = QColor(255, 80, 80, 220)
                text_color = QColor(255, 255, 255)
                border_color = QColor(200, 30, 30, 220)
            else:
                bg_color = QColor(255, 255, 255, 220)
                text_color = QColor(60, 40, 30)
                border_color = QColor(255, 180, 130, 220)

            font = painter.font()
            font.setPointSize(10)
            font.setBold(True)
            painter.setFont(font)
            fm = painter.fontMetrics()

            # painter 翻译后坐标系中可用空间
            paint_w = WIDGET_SIZE - DOG_CX  # 约 230
            margin = 4
            # 气泡文本的最大可用宽度
            max_text_w = paint_w - margin * 2 - 24  # ~= 198

            # 计算换行后的文本矩形，需指定非零高度以正确触发换行
            text_rect = fm.boundingRect(
                QRect(0, 0, max_text_w, 500),
                Qt.AlignLeft | Qt.TextWordWrap, b.text
            )
            bw = text_rect.width() + 24
            bh = text_rect.height() + 18

            # 水平居中于狗头（b.x=100），约束不超出窗口
            bx = b.x - bw / 2
            bx = max(margin, min(bx, paint_w - bw - margin))

            # 气泡顶部：尖端上方
            by = b.y - bh
            by = max(margin, by + 2)  # 防止跑到屏幕外

            painter.setBrush(bg_color)
            painter.setPen(QPen(border_color, 1.5))
            painter.drawRoundedRect(
                QRect(int(bx), int(by), int(bw), int(bh)), 12, 12
            )

            # 三角尖端
            tip_x = max(bx + 14, min(float(b.x), bx + bw - 14))
            tri = QPainterPath()
            tri.moveTo(tip_x - 6, by + bh)
            tri.lineTo(tip_x, b.y)
            tri.lineTo(tip_x + 6, by + bh)
            tri.closeSubpath()
            painter.setPen(Qt.NoPen)
            painter.drawPath(tri)

            painter.setPen(text_color)
            painter.drawText(
                QRect(int(bx) + 12, int(by) + 8,
                      int(bw) - 24, int(bh) - 16),
                Qt.AlignLeft | Qt.TextWordWrap, b.text
            )
            painter.restore()

    # ========== 鼠标交互 ==========

    def wheelEvent(self, event):
        """Ctrl + 滚轮缩放狗狗大小"""
        if event.modifiers() & Qt.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.set_zoom(self.scale + SCALE_STEP)
            elif delta < 0:
                self.set_zoom(self.scale - SCALE_STEP)
            # 重新设置 DWM 属性
            QTimer.singleShot(0, self._disable_dwm_nc)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_offset = event.position().toPoint()
            self._drag_start_global = event.globalPosition().toPoint()
        elif event.button() == Qt.RightButton:
            self._show_context_menu(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event):
        if self.dragging:
            delta = event.globalPosition().toPoint() - self._drag_start_global
            if delta.manhattanLength() > 3:
                new_pos = event.globalPosition().toPoint() - self.drag_offset
                self.move(new_pos)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.dragging:
                total_delta = (
                    event.globalPosition().toPoint() - self._drag_start_global
                )
                if total_delta.manhattanLength() < 5:
                    self.pet()
            self.dragging = False

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            for _ in range(12):
                self.particles.append(
                    HeartParticle(
                        random.uniform(65, 135),
                        random.uniform(40 + DOG_VY, 100 + DOG_VY)
                    )
                )
            self._set_state(STATE_HAPPY)

    def _show_context_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { font-size: 14px; padding: 4px; }")

        sit_label = "站起来" if self.state == STATE_SITTING else "坐下"
        sit_action = QAction(sit_label, self)
        sit_action.triggered.connect(
            lambda: self._set_state(
                STATE_IDLE if self.state == STATE_SITTING else STATE_SITTING
            )
        )
        menu.addAction(sit_action)

        walk_action = QAction("🚶 散步", self)
        walk_action.triggered.connect(self.start_walking)
        menu.addAction(walk_action)

        pet_action = QAction("❤️ 摸摸头", self)
        pet_action.triggered.connect(self.pet)
        menu.addAction(pet_action)

        sleep_label = "醒来" if self.state == STATE_SLEEPING else "💤 睡觉"
        sleep_action = QAction(sleep_label, self)
        sleep_action.triggered.connect(
            lambda: self._set_state(
                STATE_IDLE if self.state == STATE_SLEEPING else STATE_SLEEPING
            )
        )
        menu.addAction(sleep_action)

        menu.addSeparator()

        zoom_in_action = QAction("🔍 放大 (Ctrl+滚轮↑)", self)
        zoom_in_action.triggered.connect(lambda: self.set_zoom(self.scale + SCALE_STEP))
        menu.addAction(zoom_in_action)

        zoom_out_action = QAction("🔎 缩小 (Ctrl+滚轮↓)", self)
        zoom_out_action.triggered.connect(lambda: self.set_zoom(self.scale - SCALE_STEP))
        menu.addAction(zoom_out_action)

        reset_zoom_action = QAction(f"↺ 重置大小 ({SCALE_DEFAULT:.0f}x)", self)
        reset_zoom_action.triggered.connect(lambda: self.set_zoom(SCALE_DEFAULT))
        menu.addAction(reset_zoom_action)

        menu.addSeparator()

        hide_action = QAction("👀 隐藏", self)
        hide_action.triggered.connect(self.hide)
        menu.addAction(hide_action)

        menu.addSeparator()

        settings_action = QAction("⚙️ 设置", self)
        settings_action.triggered.connect(self.open_settings_dialog)
        menu.addAction(settings_action)

        menu.addSeparator()

        chat_action = QAction("💬 和狗狗聊天 (AI)", self)
        chat_action.triggered.connect(self.open_chat_dialog)
        menu.addAction(chat_action)

        menu.addSeparator()

        todo_action = QAction("📋 待办事项", self)
        todo_action.triggered.connect(self.open_todo_dialog)
        menu.addAction(todo_action)

        menu.addSeparator()

        quit_action = QAction("❌ 退出", self)
        quit_action.triggered.connect(self._quit_app)
        menu.addAction(quit_action)

        menu.exec(pos)

    def show_ai_response(self, text: str):
        """在狗狗头顶显示 AI 回复气泡"""
        self.speech_bubbles.clear()
        self.speech_bubbles.append(
            SpeechBubble(text, 100, 48, is_annoyed=False)
        )
        self._set_state(STATE_HAPPY)
        for _ in range(6):
            self.particles.append(
                HeartParticle(
                    random.uniform(70, 130),
                    random.uniform(60 + DOG_VY, 90 + DOG_VY)
                )
            )

    def open_todo_dialog(self):
        """打开待办事项窗口"""
        if not hasattr(self, '_todo_dialog') or self._todo_dialog is None:
            self._todo_dialog = open_todo_dialog(self)
        else:
            self._todo_dialog.refresh_list()
        if self._todo_dialog.isMinimized():
            self._todo_dialog.showNormal()
        else:
            self._todo_dialog.show()
        self._todo_dialog.raise_()
        self._todo_dialog.activateWindow()

    def open_settings_dialog(self):
        """打开设置窗口"""
        from settings_dialog import open_settings_dialog
        open_settings_dialog(self)
        # 重载宠物配置，使修改即时生效
        from pet_config_loader import reload_pet_config, get_pet_config
        reload_pet_config()
        self.pet_config = get_pet_config()

    def open_chat_dialog(self):
        """打开 AI 对话窗口"""
        if not hasattr(self, '_chat_dialog') or self._chat_dialog is None:
            self._chat_dialog = ChatDialog(self)
        # 如果窗口被最小化了，先恢复
        if self._chat_dialog.isMinimized():
            self._chat_dialog.showNormal()
        else:
            self._chat_dialog.show()
        self._chat_dialog.raise_()
        self._chat_dialog.activateWindow()

    def closeEvent(self, event):
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide()
        event.accept()

    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(_create_dog_icon(32)))
        self.tray_icon.setToolTip("Desktop Dog 🐕 - 右键菜单")

        tray_menu = QMenu()

        show_action = QAction("显示狗狗", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)

        hide_action = QAction("隐藏狗狗", self)
        hide_action.triggered.connect(self.hide)
        tray_menu.addAction(hide_action)

        tray_menu.addSeparator()

        chat_action = QAction("💬 和狗狗聊天 (AI)", self)
        chat_action.triggered.connect(self.open_chat_dialog)
        tray_menu.addAction(chat_action)

        tray_menu.addSeparator()

        todo_action = QAction("📋 待办事项", self)
        todo_action.triggered.connect(self.open_todo_dialog)
        tray_menu.addAction(todo_action)

        tray_menu.addSeparator()

        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self._quit_app)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)

        self._tray_just_created = True
        self.tray_icon.show()
        self.tray_icon.activated.connect(self._on_tray_activated)
        QTimer.singleShot(1500, lambda: setattr(self, '_tray_just_created', False))

    def _quit_app(self):
        """退出整个应用"""
        # 停止所有定时器
        self.anim_timer.stop()
        self.behavior_timer.stop()
        self.hourly_timer.stop()
        self.todo_timer.stop()

        # 关闭聊天窗口
        if hasattr(self, '_chat_dialog') and self._chat_dialog is not None:
            self._chat_dialog.close()

        # 隐藏托盘图标
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide()

        # 退出应用
        QApplication.instance().quit()

    def _on_tray_activated(self, reason):
        if getattr(self, '_tray_just_created', True):
            return
        if reason == QSystemTrayIcon.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show()


# ========== AI 对话工作线程 ==========
class ChatWorker(QThread):
    """后台执行 AI 对话请求"""
    finished = Signal(str)
    error = Signal(str)
    stream_chunk = Signal(str)

    def __init__(self, message: str):
        super().__init__()
        self.message = message

    def run(self):
        chat = get_chat()
        try:
            if chat.available:
                # 流式返回
                full_text = ""
                for chunk in chat.chat_stream(self.message):
                    full_text += chunk
                    self.stream_chunk.emit(chunk)
                # 流式完成后发出 finished 信号，触发 UI 恢复
                self.finished.emit(full_text)
            else:
                # API 不可用，使用本地回复
                result = chat.chat_sync(self.message)
                if result:
                    self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


# ========== 图标绘制 ==========
def _create_dog_icon(size: int = 64) -> QPixmap:
    """绘制 chibi 柴犬头像图标，匹配桌面狗狗渲染风格"""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    p = QPainter(pixmap)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 64.0
    cx, cy = size / 2, size / 2

    # ---------- 左耳（三角耳 + 内侧粉）----------
    le = QPainterPath()
    le.moveTo(cx - 12 * s, cy - 18 * s)
    le.cubicTo(cx - 20 * s, cy - 30 * s, cx - 30 * s, cy - 28 * s, cx - 28 * s, cy - 14 * s)
    le.cubicTo(cx - 24 * s, cy - 8 * s, cx - 16 * s, cy - 8 * s, cx - 12 * s, cy - 18 * s)
    p.setBrush(COLOR_FUR)
    p.setPen(QPen(COLOR_FUR_DARK, 1.2 * s))
    p.drawPath(le)

    li = QPainterPath()
    li.moveTo(cx - 14 * s, cy - 18 * s)
    li.cubicTo(cx - 20 * s, cy - 27 * s, cx - 26 * s, cy - 26 * s, cx - 24 * s, cy - 16 * s)
    li.cubicTo(cx - 21 * s, cy - 10 * s, cx - 17 * s, cy - 10 * s, cx - 14 * s, cy - 18 * s)
    p.setBrush(COLOR_INNER_EAR)
    p.setPen(Qt.NoPen)
    p.drawPath(li)

    # ---------- 右耳 ----------
    re_ = QPainterPath()
    re_.moveTo(cx + 12 * s, cy - 18 * s)
    re_.cubicTo(cx + 20 * s, cy - 30 * s, cx + 30 * s, cy - 28 * s, cx + 28 * s, cy - 14 * s)
    re_.cubicTo(cx + 24 * s, cy - 8 * s, cx + 16 * s, cy - 8 * s, cx + 12 * s, cy - 18 * s)
    p.setBrush(COLOR_FUR)
    p.setPen(QPen(COLOR_FUR_DARK, 1.2 * s))
    p.drawPath(re_)

    ri = QPainterPath()
    ri.moveTo(cx + 14 * s, cy - 18 * s)
    ri.cubicTo(cx + 20 * s, cy - 27 * s, cx + 26 * s, cy - 26 * s, cx + 24 * s, cy - 16 * s)
    ri.cubicTo(cx + 21 * s, cy - 10 * s, cx + 17 * s, cy - 10 * s, cx + 14 * s, cy - 18 * s)
    p.setBrush(COLOR_INNER_EAR)
    p.setPen(Qt.NoPen)
    p.drawPath(ri)

    # ---------- 大圆脸（chibi 比例）----------
    head = QPainterPath()
    head.moveTo(cx - 22 * s, cy - 8 * s)
    head.cubicTo(cx - 24 * s, cy - 24 * s, cx + 24 * s, cy - 24 * s, cx + 22 * s, cy - 8 * s)
    head.cubicTo(cx + 24 * s, cy + 12 * s, cx + 14 * s, cy + 22 * s, cx, cy + 22 * s)
    head.cubicTo(cx - 14 * s, cy + 22 * s, cx - 24 * s, cy + 12 * s, cx - 22 * s, cy - 8 * s)
    p.setBrush(COLOR_FUR)
    p.setPen(QPen(COLOR_FUR_DARK, 1.5 * s))
    p.drawPath(head)

    # 头顶高光
    hl = QPainterPath()
    hl.moveTo(cx - 12 * s, cy - 22 * s)
    hl.cubicTo(cx - 4 * s, cy - 26 * s, cx + 4 * s, cy - 26 * s, cx + 12 * s, cy - 22 * s)
    hl.cubicTo(cx + 8 * s, cy - 23 * s, cx - 8 * s, cy - 23 * s, cx - 12 * s, cy - 22 * s)
    p.setBrush(COLOR_FUR_HIGHLIGHT)
    p.setPen(Qt.NoPen)
    p.drawPath(hl)

    # ---------- 脸部奶油色面具 ----------
    mask = QPainterPath()
    mask.moveTo(cx, cy - 6 * s)
    mask.cubicTo(cx - 14 * s, cy - 5 * s, cx - 18 * s, cy + 4 * s, cx - 17 * s, cy + 12 * s)
    mask.cubicTo(cx - 16 * s, cy + 20 * s, cx - 6 * s, cy + 22 * s, cx, cy + 22 * s)
    mask.cubicTo(cx + 6 * s, cy + 22 * s, cx + 16 * s, cy + 20 * s, cx + 17 * s, cy + 12 * s)
    mask.cubicTo(cx + 18 * s, cy + 4 * s, cx + 14 * s, cy - 5 * s, cx, cy - 6 * s)
    p.setBrush(COLOR_CREAM)
    p.setPen(Qt.NoPen)
    p.drawPath(mask)

    # ---------- 眉斑 ----------
    p.setBrush(COLOR_FUR_DARK)
    p.drawEllipse(QPointF(cx - 14 * s, cy - 9 * s), 4.5 * s, 2.5 * s)
    p.drawEllipse(QPointF(cx + 14 * s, cy - 9 * s), 4.5 * s, 2.5 * s)

    # ---------- 大眼睛（anime sparkle）----------
    for sign in (-1, 1):
        eex, epx = cx + sign * 12 * s, cx + sign * 13 * s
        # 眼白
        p.setBrush(QColor(255, 255, 255))
        p.setPen(QPen(COLOR_EYE, 1.4 * s))
        p.drawEllipse(QPointF(eex, cy - 3 * s), 5.5 * s, 6.5 * s)
        # 瞳孔
        p.setBrush(COLOR_EYE)
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(epx, cy - 2.5 * s), 3 * s, 3.5 * s)
        # 主高光（左上）
        p.setBrush(COLOR_EYE_HIGHLIGHT)
        p.drawEllipse(QPointF(eex - 1.5 * s, cy - 6 * s), 2 * s, 2.2 * s)
        # 辅助高光
        p.drawEllipse(QPointF(eex + 2 * s, cy - 5 * s), 1.2 * s, 1.3 * s)
        # 底部反光
        p.setBrush(COLOR_EYE_SHINE)
        p.drawEllipse(QPointF(epx + 1.5 * s, cy + 1 * s), 1.2 * s, 1 * s)

    # ---------- 鼻子 ----------
    p.setBrush(COLOR_NOSE)
    p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(cx, cy + 5 * s), 4 * s, 3 * s)
    p.setBrush(COLOR_NOSE_HIGHLIGHT)
    p.drawEllipse(QPointF(cx - 0.8 * s, cy + 3.8 * s), 1.8 * s, 1.2 * s)

    # ---------- :3 嘴巴 ----------
    p.setPen(QPen(COLOR_MOUTH, 1 * s, Qt.SolidLine, Qt.RoundCap))
    p.setBrush(Qt.NoBrush)
    ml = QPainterPath()
    ml.moveTo(cx - 6 * s, cy + 10 * s)
    ml.cubicTo(cx - 5 * s, cy + 6 * s, cx - 1 * s, cy + 8 * s, cx, cy + 11 * s)
    p.drawPath(ml)
    mr = QPainterPath()
    mr.moveTo(cx + 6 * s, cy + 10 * s)
    mr.cubicTo(cx + 5 * s, cy + 6 * s, cx + 1 * s, cy + 8 * s, cx, cy + 11 * s)
    p.drawPath(mr)
    p.setPen(QPen(COLOR_MOUTH, 0.8 * s, Qt.SolidLine, Qt.RoundCap))
    p.drawLine(QPointF(cx, cy + 9 * s), QPointF(cx, cy + 13 * s))

    # ---------- 舌头 ----------
    p.setBrush(COLOR_TONGUE)
    p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(cx, cy + 14 * s), 4 * s, 5 * s)

    # ---------- 腮红 ----------
    p.setBrush(COLOR_BLUSH)
    p.drawEllipse(QPointF(cx - 15 * s, cy + 6 * s), 5 * s, 3.2 * s)
    p.drawEllipse(QPointF(cx + 15 * s, cy + 6 * s), 5 * s, 3.2 * s)

    p.end()
    return pixmap


# ========== AI 对话窗口 ==========
class ChatDialog(QWidget):
    """AI 对话窗口 - 和狗狗聊天"""

    def __init__(self, parent=None):
        super().__init__(None, Qt.Window | Qt.WindowStaysOnTopHint)
        self._dog_parent = parent  # 保存父窗口引用用于生命周期管理
        self.setWindowTitle("和狗狗聊天 💬")
        self.setMinimumSize(360, 480)
        self.resize(380, 520)

        # 设置任务栏图标
        self._setup_window_icon()
        self._init_ui()
        self._init_worker()
        self._set_style()

    def _setup_window_icon(self):
        """为聊天窗口设置独立的程序图标（任务栏显示用）"""
        self.setWindowIcon(QIcon(_create_dog_icon(64)))

    def closeEvent(self, event):
        """X 按钮关闭聊天窗口"""
        if self._dog_parent:
            self._dog_parent._chat_dialog = None
        event.accept()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # 标题
        title = QLabel("💬 和狗狗聊天")
        title.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 提示标签
        tip = QLabel("问狗狗任何问题，它会用大模型回复你~")
        tip.setAlignment(Qt.AlignCenter)
        tip.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(tip)

        # 聊天记录区域
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setPlaceholderText("对话记录...")
        layout.addWidget(self.chat_display, 1)

        # 输入区域
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("输入你想对狗狗说的话...")
        self.input_field.returnPressed.connect(self._send_message)
        input_layout.addWidget(self.input_field, 1)

        self.send_btn = QPushButton("发送")
        self.send_btn.clicked.connect(self._send_message)
        input_layout.addWidget(self.send_btn)
        layout.addLayout(input_layout)

        # 底部按钮
        btn_layout = QHBoxLayout()
        self.clear_btn = QPushButton("清空对话")
        self.clear_btn.clicked.connect(self._clear_chat)
        btn_layout.addWidget(self.clear_btn)

        self.reset_btn = QPushButton("重置记忆")
        self.reset_btn.clicked.connect(self._reset_memory)
        btn_layout.addWidget(self.reset_btn)
        layout.addLayout(btn_layout)

        # 加载欢迎消息
        self._append_message("狗狗", "汪汪~ 主人好呀！想和我说什么都可以哦！💕❤️",
                             is_bot=True)

    def _init_worker(self):
        self._worker: ChatWorker | None = None
        self._is_waiting = False
        self._bot_response_buffer = ""

    def _set_style(self):
        self.setStyleSheet("""
            ChatDialog {
                background-color: #fff8f0;
            }
            QTextEdit {
                background-color: #ffffff;
                border: 2px solid #f0d0a0;
                border-radius: 10px;
                padding: 8px;
                font-size: 13px;
                font-family: "Microsoft YaHei";
            }
            QLineEdit {
                background-color: #ffffff;
                color: #333333;
                border: 2px solid #f0d0a0;
                border-radius: 8px;
                padding: 6px 10px;
                font-size: 13px;
                font-family: "Microsoft YaHei";
            }
            QLineEdit:focus {
                border-color: #e8a040;
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
            QPushButton:disabled {
                background-color: #ccc;
            }
            QLabel {
                font-family: "Microsoft YaHei";
            }
        """)

    def _send_message(self):
        text = self.input_field.text().strip()
        if not text or self._is_waiting:
            return

        self._is_waiting = True
        self.send_btn.setEnabled(False)
        self.input_field.setEnabled(False)
        self.send_btn.setText("思考中...")

        # 显示用户消息
        self._append_message("你", text, is_bot=False)
        self.input_field.clear()

        # 启动后台线程
        self._current_bot_text = ""
        self._stream_buffer = ""
        self._stream_display_lock = False  # 防抖：控制刷新频率

        self._worker = ChatWorker(text)
        self._worker.stream_chunk.connect(self._on_stream_chunk)
        self._worker.finished.connect(self._on_response_finished)
        self._worker.error.connect(self._on_response_error)
        self._worker.start()

    def _on_response_finished(self, text: str):
        """回复完成，处理 TODO 标签并替换流式标签为最终标签"""
        if text:
            # 解析 TODO 标签
            clean_text, todos = self._parse_todo_tags(text)
            self._current_bot_text = clean_text

            # 创建待办事项
            for todo_title, todo_time in todos:
                self._create_todo_from_ai(todo_title, todo_time)

            # 替换流式显示中的 "（回复中）" 标签为最终标签
            scrollbar = self.chat_display.verticalScrollBar()
            was_at_bottom = scrollbar.value() >= scrollbar.maximum() - 10

            cursor = self.chat_display.textCursor()
            cursor.movePosition(QTextCursor.End)
            block = cursor.block()
            found = False
            while block.isValid() and not found:
                block_text = block.text()
                if "💬 狗狗（回复中）：" in block_text:
                    cursor.setPosition(block.position(), QTextCursor.MoveAnchor)
                    cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
                    found = True
                else:
                    block = block.previous()

            if found:
                cursor.insertHtml(
                    f"<span style='color:#c06030;font-weight:bold;'>💬 狗狗：</span>"
                    f"<span style='color:#333;'>{clean_text}</span>"
                )
            else:
                # 非流式路径（如非流式API返回）
                self._append_message("狗狗", clean_text, is_bot=True)

            if was_at_bottom:
                scrollbar.setValue(scrollbar.maximum())

        self._finalize_response()

    def _parse_todo_tags(self, text: str) -> tuple[str, list[tuple[str, str]]]:
        """解析 AI 回复中的 [[TODO:标题|时间]] 标签
        返回 (清除标签后的文本, [(标题, 时间), ...])
        """
        import re
        todos = []
        pattern = r'\[\[TODO:(.+?)\|(.+?)\]\]'
        matches = re.findall(pattern, text)
        for title, time_str in matches:
            todos.append((title.strip(), time_str.strip()))
        clean_text = re.sub(pattern, '', text).strip()
        return clean_text, todos

    def _create_todo_from_ai(self, title: str, time_str: str):
        """从 AI 解析结果创建待办事项"""
        mgr = get_todo_manager()
        item = mgr.parse_and_add(title, time_str)
        if item:
            due_str = item.due_time.strftime("%Y-%m-%d %H:%M")
            self._append_message(
                "系统",
                f"✅ 已添加待办：{title}\n⏰ 提醒时间：{due_str}",
                is_bot=False,
            )
            # 通知主窗口刷新待办列表
            if self._dog_parent and hasattr(self._dog_parent, '_todo_dialog') and self._dog_parent._todo_dialog is not None:
                self._dog_parent._todo_dialog.refresh_list()
        else:
            self._append_message(
                "系统",
                f"❌ 无法解析时间\"{time_str}\"，请手动添加待办",
                is_bot=False,
            )

    def _on_stream_chunk(self, chunk: str):
        """流式接收回复片段，实时追加到聊天显示"""
        self._current_bot_text += chunk
        # 每收到约100字符或首个chunk时更新一次显示，避免频繁刷新
        if len(self._current_bot_text) < 40 or len(self._current_bot_text) % 80 < len(chunk):
            self._update_streaming_display(self._current_bot_text)

    def _update_streaming_display(self, text: str):
        """更新流式输出中的狗狗回复（替换最后一条流式消息）"""
        scrollbar = self.chat_display.verticalScrollBar()
        was_at_bottom = scrollbar.value() >= scrollbar.maximum() - 10

        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)

        # 尝试反向查找"💬 狗狗（回复中）"标签位置
        block = cursor.block()
        found = False
        while block.isValid() and not found:
            block_text = block.text()
            if "💬 狗狗（回复中）：" in block_text:
                # 找到流式消息的起始行，选中从此行到末尾
                cursor.setPosition(block.position(), QTextCursor.MoveAnchor)
                cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
                found = True
            else:
                block = block.previous()

        if found:
            cursor.insertHtml(
                f"<span style='color:#c06030;font-weight:bold;'>💬 狗狗（回复中）：</span>"
                f"<span style='color:#333;'>{text}</span>"
            )
        else:
            # 如果没找到，追加新行
            self.chat_display.append(
                f"<span style='color:#c06030;font-weight:bold;'>💬 狗狗（回复中）：</span>"
                f"<span style='color:#333;'>{text}</span>"
            )

        # 保持滚动位置
        if was_at_bottom:
            scrollbar.setValue(scrollbar.maximum())

    def _on_response_error(self, error: str):
        self._append_message("狗狗", f"汪汪~ 出错了：{error}", is_bot=True)
        self._finalize_response()

    def _finalize_response(self):
        self._is_waiting = False
        self.send_btn.setEnabled(True)
        self.input_field.setEnabled(True)
        self.send_btn.setText("发送")
        self.input_field.setFocus()

        # 通知主窗口显示对话气泡
        if self._current_bot_text and self._dog_parent:
            self._dog_parent.show_ai_response(self._current_bot_text)

    def _append_message(self, sender: str, text: str, is_bot: bool = False,
                        is_streaming: bool = False):
        if is_bot:
            if is_streaming and not text:
                return
            prefix = "💬 狗狗（回复中）：" if is_streaming else "💬 狗狗："
            color = "#c06030"
        else:
            prefix = "👤 你："
            color = "#4080c0"

        self.chat_display.append(
            f"<span style='color:{color};font-weight:bold;'>{prefix}</span>"
            f"<span style='color:#333;'>{text}</span>"
        )
        # 滚动到底部
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _clear_chat(self):
        self.chat_display.clear()
        self._append_message("狗狗", "汪汪~ 主人好呀！想和我说什么都可以哦！💕❤️",
                             is_bot=True)

    def _reset_memory(self):
        chat = get_chat()
        chat.reset_chat()
        self._append_message("系统", "✨ 对话记忆已重置，狗狗忘了刚才聊的内容~",
                             is_bot=False)


# ========== 入口 ==========
def main():
    import json
    import os

    app = QApplication(sys.argv)
    app.setApplicationName("Desktop Dog")
    app.setWindowIcon(QIcon(_create_dog_icon(64)))
    app.setQuitOnLastWindowClosed(False)

    # 检查是否需要首次设置
    from setup_dialog import needs_setup, run_setup
    if needs_setup():
        api_config, pet_config, api_skipped = run_setup()
        if api_config is None:
            # 用户点击退出
            sys.exit(0)

        # 保存 API 配置到 config.json
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                old_config = json.load(f)
        else:
            old_config = {}

        # 合并配置：保留 system_prompt 等
        if "system_prompt" not in api_config and "system_prompt" in old_config:
            api_config["system_prompt"] = old_config["system_prompt"]
        if "remember_history" not in api_config and "remember_history" in old_config:
            api_config["remember_history"] = old_config.get("remember_history", True)
        if "max_history" not in api_config and "max_history" in old_config:
            api_config["max_history"] = old_config.get("max_history", 20)
        api_config["setup_complete"] = True

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(api_config, f, ensure_ascii=False, indent=2)

        # 保存宠物配置到 pet_config.json
        pet_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pet_config.json")
        with open(pet_config_path, "w", encoding="utf-8") as f:
            json.dump(pet_config, f, ensure_ascii=False, indent=2)

    dog = DesktopDog()
    dog.setup_tray()
    dog.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()