# 🐕 Desktop Dog - 你的桌面小柴犬

一只住在你桌面上的可爱柴犬！她会走路、会睡觉、会撒娇、会生气，还能提醒你喝水、庆祝节日、管理待办事项，甚至还能用 AI 大模型和你聊天！

> 💝 专为「小宝」打造，但首次启动时可自定义主人名字和狗狗名字，让她成为你专属的桌面陪伴~

---

## ✨ 功能一览

- 🐕 **桌面宠物**：可爱的柴犬在你的桌面上自由活动
- 🐾 **摸摸互动**：点击狗狗摸摸头，她会冒出爱心和俏皮话
- 🕐 **时间感知**：早上说早安、中午提醒吃饭、晚上道晚安
- 💝 **整点情话**：每小时整点都会说一句温馨的话
- 💧 **喝水提醒**：每3小时提醒你喝一次水（仅在9:00-21:00）
- 🎉 **节日祝福**：支持生日、元旦、儿童节、国庆、圣诞、跨年等特殊日期
- 📋 **待办事项**：内置待办管理，支持 AI 智能解析 `[[TODO:标题|时间]]` 一键添加
- ✨ **AI 聊天**：接入大模型 API，可以和狗狗自由对话（可选功能）
- 🔍 **缩放支持**：`Ctrl + 滚轮` 调整狗狗大小
- 📌 **系统托盘**：最小化到托盘，右键菜单快速操作
- 🎨 **可定制的俏皮话**：所有文案都在 JSON 配置文件中，随时修改

---

## 🚀 快速开始

### 环境要求

- Windows 10 / Windows 11
- Python 3.10+
- 已安装 `PySide6`

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行

```bash
python main.py
```

首次启动时会弹出 **配置向导**，引导你设置：
- 主人名字（如：小宝）
- 狗狗名字（如：小柴）
- AI 聊天的大模型 API 配置（可跳过）

> ⚠️ 如果你选择不配置 AI 大模型，对话聊天功能将不可用，但其他所有功能（摸摸、情话、喝水提醒、待办等）都正常使用。你可以在 `config.json` 中随时补充配置。

---

## 📁 配置说明

### 1. API + 基础配置 (`config.json`)

首次启动通过配置向导填写 API 信息，或手动编辑此文件：

```json
{
  "api_key": "sk-xxx",
  "model": "deepseek-chat",
  "base_url": "https://api.deepseek.com",
  "system_prompt": "你是一只可爱的桌面柴犬宠物...",
  "remember_history": true,
  "max_history": 20,
  "setup_complete": true
}
```

- `api_key`：大模型 API 密钥（不填则 AI 聊天不可用）
- `model`：模型名称（如 `deepseek-chat`、`gpt-3.5-turbo`）
- `base_url`：API 接口地址（兼容 OpenAI 格式）
- `system_prompt`：AI 人设 prompt（设置向导会自动替换主人名和狗狗名）

### 2. 狗狗文案配置 (`pet_config.json`)

**这是最有趣的部分！** 所有狗狗说的话都在这个文件里，你可以随时修改：

```json
{
  "phrases_normal": [
    "小主人干嘛呀~",
    "小主人我在呢！",
    "小主人想我了吗？"
  ],
  "phrases_time": {
    "morning": ["小主人早上好！☀️"],
    "noon": ["小主人吃饭了吗？"],
    "afternoon": ["小主人下午好呀~"],
    "evening": ["小主人晚上好！🌙"]
  },
  "phrases_annoyed": [
    "干嘛呀狗狗名！",
    "狗狗名你讨厌！",
    "别摸啦！毛都掉了！"
  ],
  "annoy_threshold": 7,
  "cooldown": 300,
  "love_phrases": [
    "小主人，陪你一起成长是最幸福的事~ ❤️",
    "狗狗名，你是最棒的小主人！💪"
  ],
  "special_dates": {
    "11,13": ["狗狗名生日快乐！🎂🎉"],
    "1,1": ["小主人新年快乐！🎉🎊"]
  },
  "water_reminders": [
    "小主人，该喝水啦！💧",
    "狗狗名喝水时间到！💧"
  ]
}
```

**💡 文案自动替换说明：**
- 首次配置时输入的主人名字（如「小宝」）会自动替换模板文案中的 `小主人` 和 `狗狗名`
- 你也可以随时手动编辑 `pet_config.json`，把所有「小主人」全文替换成「小宝」或任何你喜欢的称呼
- 同样可以随时修改狗狗名字

> 💡 **修改后无需重启**：修改 `pet_config.json` 后，下次触发对应事件时就会自动使用新文案（由 `PetConfigLoader` 按需加载）。

### 3. 配置文件位置

```
DesktopDog/
├── config.json             ← API 配置 + system_prompt
├── pet_config.json         ← 狗狗文案配置（俏皮话、情话、提醒等）
├── todos.json              ← 待办事项数据
├── main.py
├── ai_chat.py
├── setup_dialog.py
├── pet_config_loader.py
└── ...
```

---

## 🤖 AI 聊天功能

### 支持的 API 提供商

任何兼容 OpenAI API 格式的接口都支持，包括但不限于：
- **DeepSeek**：`https://api.deepseek.com`
- **OpenAI**：`https://api.openai.com/v1`
- **通义千问 (Qwen)**：`https://dashscope.aliyuncs.com/compatible-mode/v1`
- **智谱 GLM**：`https://open.bigmodel.cn/api/paas/v4`
- **Moonshot / Kimi**：`https://api.moonshot.cn/v1`
- **本地模型（Ollama）**：`http://localhost:11434/v1`

### 如何配置

在首次启动的配置向导中填写，或手动编辑 `config.json` 文件。

### 智能待办解析

在 AI 对话中，使用以下格式即可自动创建待办：

```
[[TODO:看牙医|2025-06-15 14:30]]
```

AI 会自动解析并添加到待办列表中。

---

## 📦 打包成 EXE

推荐使用 **PyInstaller** 打包成独立的 `.exe` 文件。

### 打包步骤

1. **安装 PyInstaller**

```bash
pip install pyinstaller
```

2. **打包（单文件模式）**

```bash
pyinstaller --onefile --windowed --name "DesktopDog" --icon=dog.ico main.py
```

3. **打包（文件夹模式，推荐）**

```bash
pyinstaller --noconsole --windowed --name "DesktopDog" --icon=dog.ico main.py
```

参数说明：
- `--onefile`：打包成单个 exe（启动稍慢）
- `--windowed` / `--noconsole`：不显示命令行窗口
- `--icon=dog.ico`：设置 exe 图标
- `--name "DesktopDog"`：输出文件名

4. **配置隐藏导入**

如果打包后运行报错，在 `.spec` 文件中添加隐式导入：

```python
hiddenimports=['PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets']
```

然后运行：

```bash
pyinstaller DesktopDog.spec
```

5. **添加配置文件到打包目录**

打包完成后，将以下文件复制到 exe 同目录下：
- `config.json`（API 配置 + system_prompt）
- `pet_config.json`（狗狗文案配置）
- `todos.json`（待办数据，可复制空文件）

### 开机自启动

将打包好的 `.exe` 或快捷方式放入 Windows 启动文件夹：

```
C:\Users\你的用户名\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup
```

---

## 📂 项目结构

```
DesktopDog/
├── main.py                 # 主程序入口 + 桌面狗狗渲染 + AI 对话窗口
├── ai_chat.py              # AI 大模型聊天模块
├── setup_dialog.py         # 首次启动配置向导（主人/狗狗名字 + API 配置）
├── settings_dialog.py      # 运行时设置窗口（名字、API、文案配置一个界面搞定）
├── pet_config_loader.py    # 文案配置加载器（从 pet_config.json 读取）
├── todo_manager.py         # 待办事项管理
├── todo_dialog.py          # 待办事项界面
├── config.json             # API 配置 + system_prompt
├── pet_config.json         # 狗狗文案配置（俏皮话、情话、提醒等）
├── todos.json              # 待办数据
├── requirements.txt        # Python 依赖
├── DesktopDog.spec         # PyInstaller 打包配置
└── README.md               # 本文件
```

---

## 🎮 操作指南

| 操作 | 方式 |
|------|------|
| 摸摸头 | 单击狗狗 |
| 拖动狗狗 | 按住左键拖动 |
| 爱心雨 | 双击狗狗 |
| 缩放 | `Ctrl + 滚轮` |
| 右键菜单 | 右键点击狗狗 |
| 隐藏/显示 | 系统托盘单击图标 |
| AI 聊天 | 右键菜单 → 💬 和狗狗聊天 |
| 待办事项 | 右键菜单 → 📋 待办事项 |

---

## 🛠 技术栈

- **Python 3.10+**
- **PySide6**（Qt for Python）：GUI 框架
- **OpenAI 兼容 API**：AI 对话（可选）
- **PyInstaller**：打包

---

## 📝 开发说明

### 自定义文案

编辑 `pet_config.json`，修改任意文案项即可实时生效，无需重启程序。

### 自定义 Prompt

编辑 `config.json` 中的 `system_prompt` 字段，可以调整 AI 狗狗的人设和回复风格。`{owner_name}` 和 `{pet_name}` 会自动替换为配置中的名字。

---

## ⚠️ 注意事项

1. **首次启动**会弹出配置向导，必须设置主人名字和狗狗名字；API 配置可选，不填则 AI 对话功能不可用
2. **AI 聊天功能**需要配置大模型 API Key（兼容 OpenAI 格式），不配置不影响桌面陪伴等其他所有功能
3. 桌面狗狗使用透明窗口技术（Win32 DWM API），可能与某些全屏应用或录屏软件有冲突
4. 修改 `pet_config.json` 时注意 JSON 格式正确，建议使用 VS Code 等编辑器

---

## 📄 开源协议

MIT License

---

## 💝 致谢

这只小柴犬献给所有需要桌面陪伴的人 🐕❤️