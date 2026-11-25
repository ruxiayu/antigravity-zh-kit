---
name: chinese-summary
description: >-
  【全局自动执行】为 Antigravity 所有新建会话自动完成规范中文命名与总结（4~10 个汉字）。
  在新会话建立的第 1~2 轮交互中（或发现标题为默认英文/未命名时），智能体应主动调用内置脚本
  scripts/set_title.py，将当前会话标题同步更新为精炼中文（如“Docker网络排查”、“PDF划线提取”），无需用户提醒。
---

# Chinese Summary（Antigravity 会话自动中文命名）

本技能负责同步更新 Antigravity 三层本地存储（`annotations/*.pbtxt`、`agyhub_summaries_proto.pb`、`conversation_summaries.db`），让侧边栏历史会话标题即时呈现清晰、规范的中文，彻底告别难以检索的英文默认标题。

## 核心规则

1. **开局自动触发**：在新会话第 1~2 轮交互中，主动依据用户诉求生成中文标题并调用脚本写入，无需等待用户提醒。
2. **标题长度**：控制在 **4 ~ 10 个汉字**，言简意赅。
3. **中英专有名词融合**：遇到技术名词或品牌名（如 Docker、Git、Cloudflare、PDF）时，与中文动作自然组合（如 `Git分支冲突排查`、`PDF重点划线提取`），避免纯英文标题。

## 执行方式

```bash
# Windows (PowerShell)
python "$HOME\.gemini\config\skills\chinese-summary\scripts\set_title.py" --cid "<Conversation-ID>" --title "<中文标题>"

# macOS / Linux
python3 "$HOME/.gemini/config/skills/chinese-summary/scripts/set_title.py" --cid "<Conversation-ID>" --title "<中文标题>"
```

* `--cid`：从系统提示词 `<user_information>` 中的 `Conversation ID` 获取。
* `--title`：4~10 字中文标题。
* `--home`（可选）：脚本会自动探测当前 Antigravity 数据目录（无论安装或迁移在哪个磁盘）；如确需手动指定，可传入 `<user_information>` 中的 `App Data Directory` 或设置环境变量 `ANTIGRAVITY_HOME`。
* **路径定位**：调用时优先使用本 `SKILL.md` 同级目录下的 `scripts/set_title.py`，兼容任意自定义安装路径。
* 脚本仅依赖 Python 3 标准库，写入后无需重启客户端即可生效。
