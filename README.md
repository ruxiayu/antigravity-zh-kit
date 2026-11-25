# Antigravity ZH Kit（Antigravity 中文效率套件）

一套开箱即用的 **Google Antigravity 中文实战技能（Skills）+ 全局规则（`AGENTS.md`）模板**，解决中文用户在日常使用 Antigravity 时最常见的四大痛点：

1. **新会话全是难找的英文默认标题** -> `chinese-summary` 自动同步三层存储，秒变 4~10 字规范中文标题
2. **左侧会话越积越多、重复碎片占满磁盘** -> `session-organizer` 一键体检、相似会话聚类、去噪提炼接力档并安全瘦身
3. **让 AI 读扫描版/划线 PDF 经常转图超时爆上下文** -> `pdf-fast-extract` 本地 PyMuPDF + RapidOCR 一次提取纯文本与红/黄/绿/蓝划线标签
4. **AI 蒙头干活不报进度、容易静默覆盖文件** -> `AGENTS.template.md` 开箱即用的中文过程透明化与安全边界规范

---

## 目录结构

```text
antigravity-zh-kit/
├── README.md
├── LICENSE                          # MIT License
├── install.ps1                      # Windows 一键部署脚本
├── install.sh                       # macOS / Linux 一键部署脚本
├── rules/
│   └── AGENTS.template.md           # 模块化脱敏全局规则模板（可按需删减）
├── skills/
│   ├── chinese-summary/             # 会话自动中文命名（纯 Python 标准库）
│   ├── session-organizer/           # 左侧会话聚类整理与空间瘦身（纯 Python 标准库）
│   └── pdf-fast-extract/            # PDF 高速 OCR + 矢量划线颜色提取
└── docs/
    └── recommended-skills.md        # 实测顺手的第三方 Skills 推荐清单
```

---

## 快速安装

### 1. 克隆仓库
```bash
git clone https://github.com/ruxiayu/antigravity-zh-kit.git
cd antigravity-zh-kit
```

### 2. 一键部署技能

* **Windows (PowerShell)**：
```powershell
# 仅安装 3 个自研技能
.\install.ps1

# 同时部署全局规则模板（若本机已有 AGENTS.md，会自动跳过不覆盖）
.\install.ps1 -WithRules
```

* **macOS / Linux**：
```bash
chmod +x install.sh
./install.sh --with-rules
```

### 3. 安装可选依赖（仅 `pdf-fast-extract` 需要）
`chinese-summary` 和 `session-organizer` 均为**纯 Python 3 标准库实现，零额外依赖**；仅当你需要使用扫描版 PDF OCR 功能时，安装一次：
```bash
pip install -r skills/pdf-fast-extract/requirements.txt
```

---

## 核心技能速览

### 1. `chinese-summary`：会话自动中文命名
* 同步更新 Antigravity 三层本地存储（`annotations/*.pbtxt`、`agyhub_summaries_proto.pb`、`conversation_summaries.db`），无需重启客户端即可在左侧边栏生效。
* 搭配 `AGENTS.template.md` 后，每次开启新会话第 1~2 轮会自动将标题改为 4~10 字中文。

### 2. `session-organizer`：左侧会话聚类整理与空间瘦身
* **只读体检**：直接对 Antigravity 说“帮我做一次会话体检”或“聚类重复会话”，自动找出空会话、长期闲置会话与碎片续接组。
* **无损整合**：提取同主题碎片会话的关键结论，由 AI 压缩成一份 3~5 KB 的接力文档，随后安全移出冗余侧边栏条目并可选清理 `brain/` 缓存释放磁盘空间。
* **灵活备份**：所有清理操作默认先预演（dry-run），需显式 `--confirm` 才执行；默认会先在 `~/.gemini/antigravity/backups/` 做备份，如磁盘空间紧张可加 `--no-backup` 跳过。

### 3. `pdf-fast-extract`：PDF 高速 OCR + 划线批注识别
* 自动区分文字页与扫描图片页，扫描页在本地跑 RapidOCR，并通过坐标碰撞检测自动标注**红线 / 黄线 / 绿线 / 蓝线**等电子划线与高亮批注。
* 杜绝大模型逐页读图爆上下文、耗时 10 分钟超时的问题（同时兼容 Antigravity、Claude Code、Cursor 等其他 Agent）。

### 环境变量自定义（可选）
如果你自定义了 Antigravity 数据目录或备份位置，可通过以下环境变量覆盖默认路径：
* `ANTIGRAVITY_HOME`：默认 `~/.gemini/antigravity`
* `ANTIGRAVITY_BACKUP_DIR`：默认 `~/.gemini/antigravity/backups`

---

## 我实测顺手的第三方 Skills 推荐清单

除了本仓库自研的 3 个工具，作者在日常使用中还高频搭配以下优秀开源技能（仅提供原项目链接，本仓库不包含其源码，欢迎去原仓 Star 支持原作者）：

| 类别 | 技能名称 | 一句话推荐理由 | 原仓库 |
| :--- | :--- | :--- | :--- |
| **排版与配图** | **Baoyu Skills（宝玉套件）** | 封面图、文章配图、信息图、小红书卡片、Markdown 转公众号 HTML 一站式搞定 | [JimLiu/baoyu-skills](https://github.com/JimLiu/baoyu-skills) |
| **自媒体写作** | **Viral Writer** | 基于 11 个内容洞见维度写公众号/小红书/抖音文案与备选标题 | [nashsu/Viral_Writer_Skill](https://github.com/nashsu/Viral_Writer_Skill) |
| **中文去 AI 味** | **Humanizer-zh** | 消除中文文档里的空话、套话与模板化表达，保留真实语气 | [op7418/Humanizer-zh](https://github.com/op7418/Humanizer-zh) |
| **省 Token** | **Caveman** | 极简精炼回复模式 + 记忆文件压缩，大幅节省 Token 消耗 | [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) |
| **音视频剪辑** | **FFmpeg Skill** | 纯本地 FFmpeg 剪辑、字幕、静音切除、响度标准化与各平台导出 | [kajisho5/ffmpeg-skill](https://github.com/kajisho5/ffmpeg-skill) |

> 完整清单与安装提示见 [docs/recommended-skills.md](docs/recommended-skills.md)。

---

## 许可协议

本项目基于 [MIT License](LICENSE) 开源，欢迎自由修改、二次分发与提交 PR。
