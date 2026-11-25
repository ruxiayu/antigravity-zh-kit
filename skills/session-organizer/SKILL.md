---
name: session-organizer
description: >-
  Antigravity 左侧会话列表智能整理、体检、重复/续接会话聚类融合、上下文压缩归档与释放磁盘空间工具。
  当用户提到“整理左侧会话”、“合并重复会话”、“整合相似会话”、“清理会话列表”、“会话体检”、
  “批量改会话标题”、“归档旧会话”、“导出历史对话”、“删除空会话”或释放 brain 缓存空间时触发。
---

# 左侧会话整理与融合助手（Session Organizer）

本技能用于安全、高效地管理 Antigravity 左侧会话列表，直接对接本地三层存储（`annotations/*.pbtxt`、`agyhub_summaries_proto.pb`、`conversation_summaries.db`）与 `brain/` / `conversations/` 产物目录，支持将“中途卡住新开窗口续接”或“同主题高度重复”的多条碎片会话**融合压缩为高密度接力文档并释放本地磁盘空间**。

## 核心安全原则

1. **先只读体检/聚类，后动手**：严禁未经用户确认擅自删除或合并任何会话；写入操作默认先预演（dry-run），需显式加 `--confirm` 才会落地。
2. **绝不篡改私有二进制轨迹**：采用“跨会话提炼融合接力档 + 保留主会话/归档移出碎片 + 可选清理旧缓存”的无损方案，绝不强行拼接 `conversations/<cid>.db`。
3. **灵活的备份策略（不强求额外磁盘空间）**：
   - 默认在删除/合并前自动将相关索引打包备份至 `~/.gemini/antigravity/backups/`（可通过环境变量 `ANTIGRAVITY_BACKUP_DIR` 自定义路径）。
   - 如果本地磁盘空间紧张，可显式加上 `--no-backup` 跳过打包直接清理。

## 核心命令速查

默认脚本路径：`~/.gemini/config/skills/session-organizer/scripts/organize_sessions.py`（纯 Python 3 标准库，支持通过环境变量 `ANTIGRAVITY_HOME` 自定义数据目录）。

### 1. 智能聚类发现重复/续接碎片组（只读）
```bash
python "$HOME/.gemini/config/skills/session-organizer/scripts/organize_sessions.py" cluster
# 可选：--threshold 0.35（调低更宽松、调高更严格），--json（输出完整 ID 结构）
```

### 2. 跨会话去噪提取素材（供 AI 提炼 3~5 KB 整合接力文档）
```bash
python "$HOME/.gemini/config/skills/session-organizer/scripts/organize_sessions.py" extract-group --cids "<id1>,<id2>,<id3>" --out "<输出路径>"
```
AI 通读提取结果后，剔除中途报错死循环与重复试错，按具体任务主题撰写精炼的 **`<任务中文主题>_接力档.md`**，包含：任务背景、已解决事项、关键文件路径、避坑记录、未完成待办。

### 3. 左侧瘦身与释放磁盘空间
```bash
# 第一步：先预演（dry-run）
python "$HOME/.gemini/config/skills/session-organizer/scripts/organize_sessions.py" merge-finalize \
  --keep-cid "<保留的主会话ID>" \
  --drop-cids "<移出的碎片ID1,ID2>" \
  --new-title "<整合后中文标题>" \
  --purge-brain

# 第二步：用户确认后加 --confirm 正式执行（空间紧张可再加 --no-backup）
python "$HOME/.gemini/config/skills/session-organizer/scripts/organize_sessions.py" merge-finalize \
  --keep-cid "<保留的主会话ID>" \
  --drop-cids "<移出的碎片ID1,ID2>" \
  --new-title "<整合后中文标题>" \
  --purge-brain --confirm
```

### 4. 基础体检 / 批量改名 / 导出 / 清理空会话
* `audit`：全局只读体检（总数、工作区分布、空会话、磁盘大户）
* `rename --cid <id> --title <新标题>` 或 `--map <json>`：三层同步安全改名（需配合 `chinese-summary` 技能）
* `export --cid <id> --out <md路径>`：导出单条会话为 Markdown
* `clean --cids <id1,id2> --confirm`：清理确认后的僵尸/空会话（可选 `--no-backup`）
