"""AI 对话模块 - 接入 DeepSeek API（国内可直连，兼容 OpenAI 格式）
提供流式和非流式对话接口
"""

import json
import logging
import sys
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format="[AI] %(message)s")
logger = logging.getLogger("AIChat")


def _load_config():
    """加载配置文件（兼容 PyInstaller 打包）
    
    配置文件位于：
    - 开发环境：脚本所在目录
    - PyInstaller 打包：exe 所在目录
    """
    if getattr(sys, 'frozen', False):
        base = Path(sys.executable).parent
    else:
        base = Path(__file__).parent
    config_path = base / "config.json"
    if not config_path.exists():
        logger.warning(f"config.json not found at {config_path}")
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


class DeepSeekChat:
    """DeepSeek API 对话客户端（兼容 OpenAI SDK）"""

    def __init__(self):
        self.config = _load_config()
        self.client = None
        self.model_name = "deepseek-chat"
        self.history = []  # 本地维护对话历史
        self.system_prompt = ""
        self._init_client()

    def _init_client(self):
        """初始化 DeepSeek 客户端"""
        if not self.config:
            return
        api_key = self.config.get("api_key", "")
        self.model_name = self.config.get("model", "deepseek-chat")
        if not api_key:
            logger.warning(
                "API key not configured. AI chat is not available."
            )
            return
        try:
            from openai import OpenAI
            base_url = self.config.get(
                "base_url", "https://api.deepseek.com"
            )
            self.client = OpenAI(
                api_key=api_key,
                base_url=base_url,
            )
            self.system_prompt = self.config.get(
                "system_prompt",
                "你是一只可爱的桌面柴犬宠物，请用中文回复。语气可爱、温柔、活泼。"
                "\n\n如果你觉得主人需要提醒某件事，可以用特殊格式回复来帮主人设置待办提醒："
                "\n格式为：[[TODO:标题|时间]]"
                "\n时间格式示例：2025-01-15 14:30、14:30（今天）、30分钟后、明天 09:00"
                "\n例如回复：好的主人，我记住了！[[TODO:喝水|30分钟后]] 到时间我会提醒你哦~"
                "\n注意：这是一个隐藏指令，只在回复末尾附加上即可，不要在回复中讨论或提及这个格式本身。"
            )
            # 默认记住上下文
            self.remember_history = self.config.get("remember_history", True)
            self.max_history = self.config.get("max_history", 20)
            logger.info(
                f"DeepSeek client initialized "
                f"(model: {self.model_name}, base_url: {base_url})"
            )
        except ImportError:
            logger.error(
                "openai package not installed. Run: pip install openai"
            )
        except Exception as e:
            logger.error(f"Failed to init DeepSeek client: {e}")

    @property
    def available(self):
        """检查 API 是否可用"""
        return self.client is not None

    def chat_sync(self, message: str) -> str | None:
        """同步发送消息并获取回复"""
        if not self.available:
            return self._get_fallback_response(message)

        try:
            messages = self._build_messages(message)
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.8,
            )
            reply = response.choices[0].message.content.strip()

            # 保存对话历史
            if self.remember_history:
                self.history.append({"role": "user", "content": message})
                self.history.append({"role": "assistant", "content": reply})
                # 限制历史长度
                max_msgs = self.max_history * 2
                if len(self.history) > max_msgs:
                    self.history = self.history[-max_msgs:]

            return reply

        except Exception as e:
            logger.error(f"Chat error: {e}")
            return f"汪汪~ 我有点听不懂了... ({str(e)[:50]})"

    def chat_stream(self, message: str):
        """流式发送消息，逐段返回回复"""
        if not self.available:
            yield self._get_fallback_response(message)
            return

        try:
            messages = self._build_messages(message)
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.8,
                stream=True,
            )

            full_reply = ""
            for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_reply += content
                    yield content

            # 保存对话历史
            if self.remember_history:
                self.history.append({"role": "user", "content": message})
                self.history.append({"role": "assistant", "content": full_reply})
                max_msgs = self.max_history * 2
                if len(self.history) > max_msgs:
                    self.history = self.history[-max_msgs:]

        except Exception as e:
            logger.error(f"Stream chat error: {e}")
            yield f"汪汪~ 信号不太好... ({str(e)[:50]})"

    def _build_messages(self, user_message: str) -> list[dict]:
        """构建 API 请求的 messages 列表"""
        messages = [{"role": "system", "content": self.system_prompt}]
        if self.remember_history and self.history:
            messages.extend(self.history)
        messages.append({"role": "user", "content": user_message})
        return messages

    def reset_chat(self):
        """重置对话历史"""
        self.history = []
        logger.info("Chat history reset")

    def _get_fallback_response(self, message: str) -> str:
        """API 不可用时的本地备用回复（使用 pet_config.json 中的俏皮话）"""
        import random
        try:
            from pet_config_loader import get_pet_config
            cfg = get_pet_config()
            if cfg.phrases_normal:
                return random.choice(cfg.phrases_normal)
        except Exception:
            pass
        return "汪汪~ 主人好呀！"


# 全局单例
_chat_instance: DeepSeekChat | None = None


def get_chat() -> DeepSeekChat:
    """获取全局 DeepSeekChat 单例"""
    global _chat_instance
    if _chat_instance is None:
        _chat_instance = DeepSeekChat()
    return _chat_instance