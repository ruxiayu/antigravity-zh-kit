# Antigravity ZH Kit（Antigravity 中文开箱即用套件）

> **一句话介绍**：让你手里的 Google Antigravity **更懂中文、更好管历史对话、不乱跑进度、读扫描版 PDF 不卡死**。  
> **零代码基础也能 1 分钟装好**，直接把下面那句话发给 Antigravity，让它自己装就行！

---

## 装完有什么变化？

| 没装之前（常见痛点） | 装完之后（真实体验） |
| :--- | :--- |
| 左侧历史会话全是英文默认标题，找旧对话像大海捞针 | **每次开新对话自动变成 4~10 字中文标题**（如 `Docker网络排查`） |
| 对话越积越多，重复/中断的碎片占满左侧列表和硬盘 | **说一句“帮我整理左侧会话”**，自动合并同类对话、生成摘要并释放空间 |
| 让 AI 读扫描版教材或带划线的 PDF，经常卡十几分钟超时 | **本地几秒提取纯文本 + 自动标出红/黄/绿/蓝划线重点**，不卡不爆上下文 |
| AI 经常“蒙头干活”，半天不说话最后吐一堆看不懂 | **先列计划、每步汇报进度、遇到报错立刻说清楚**，再也不用干等 |

---

## 怎么安装？（三选一，推荐方式一）

### 方式一：最省事 · 让 Antigravity 自己装（强烈推荐 ⭐）

打开你的 Antigravity，新建一个对话，**直接复制下面这句话发给它**：

```text
请帮我下载并安装 https://github.com/ruxiayu/antigravity-zh-kit 这个仓库里的 3 个技能和 AGENTS.template.md 规则模板（如果我本地已经有 AGENTS.md，不要覆盖我原来的，帮我把新规则安全合并进去即可）。
```

发完等几十秒，AI 就会自动帮你下载、放好位置并提示你装好了，全程不用敲一行命令。

---

### 方式二：不会用命令行 · 网页下载 ZIP 手动复制

1. 点击本页面右上角绿色的 **`<> Code`** 按钮 → 选择 **`Download ZIP`**，下载后解压。
2. 打开你电脑的技能目录（如果文件夹不存在就新建一个）：
   * **Windows**：打开文件资源管理器，在地址栏输入 `%USERPROFILE%\.gemini\config\skills` 回车
   * **macOS / Linux**：`~/.gemini/config/skills`
3. 把解压出来的 `skills` 文件夹里面的 **3 个子文件夹**（`chinese-summary`、`session-organizer`、`pdf-fast-extract`）全部复制进去。
4. （可选）把 `rules/AGENTS.template.md` 复制到上一级目录（`~/.gemini/config/`）并改名为 `AGENTS.md`（如果你原来就有 `AGENTS.md`，打开把里面的内容粘贴到末尾即可）。
5. **开启一个新对话**，马上生效！

---

### 方式三：开发者命令行一键安装

<details>
<summary>点击展开 Windows / macOS / Linux 命令行安装步骤</summary>

```bash
git clone https://github.com/ruxiayu/antigravity-zh-kit.git
cd antigravity-zh-kit
```

* **Windows (PowerShell)**：
```powershell
.\install.ps1 -WithRules
```
* **macOS / Linux**：
```bash
chmod +x install.sh
./install.sh --with-rules
```
> 注：脚本很安全，检测到你本地已有 `AGENTS.md` 时会自动跳过，绝不覆盖原有规则。

</details>

---

## 装完怎么用？（直接说人话就行）

* **自动中文标题（`chinese-summary`）**：不用管它！装完规则后，以后每开一个新对话都会自动起中文名。
* **整理左侧会话（`session-organizer`）**：直接对 Antigravity 说：
  * `帮我给左侧会话做一次体检`
  * `帮我找出重复或续接的碎片会话并整合清理`
  * （放心，默认都会先列清单给你看，**不会擅自删你的对话**；如果硬盘紧张不需要备份，告诉它“跳过备份直接清理”即可）
* **高速读 PDF / 提取划线重点（`pdf-fast-extract`）**：直接把 PDF 路径发给它说 `帮我提取这份 PDF 的文字和划线重点`。
  * *小提示*：只有这个功能首次使用时需要装两个 Python 插件，可以直接让 Antigravity 帮你跑一句：`pip install pymupdf rapidocr-onnxruntime`。

---

## 我实测顺手的第三方 Skills 推荐清单

除了本仓库自研的 3 个工具，日常高频搭配下面这些开源社区的优秀技能，组合起来体验更好（本仓库不含第三方源码，点击直达原作者仓库安装）：

| 类别 | 技能名称 | 适合干什么 | 原仓库直链 |
| :--- | :--- | :--- | :--- |
| **配图与排版** | **Baoyu Skills（宝玉套件）** | 做文章封面、配图、信息图、小红书卡片、Markdown 转公众号排版 | [JimLiu/baoyu-skills](https://github.com/JimLiu/baoyu-skills) |
| **自媒体写作** | **Viral Writer** | 写公众号、小红书、抖音文案和爆款备选标题 | [nashsu/Viral_Writer_Skill](https://github.com/nashsu/Viral_Writer_Skill) |
| **去除 AI 味** | **Humanizer-zh** | 润色中文文章，去掉空话、套话和翻译腔 | [op7418/Humanizer-zh](https://github.com/op7418/Humanizer-zh) |
| **省 Token** | **Caveman** | 极简精炼回复模式 + 压缩记忆文件，省 Token 利器 | [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) |
| **视频剪辑** | **FFmpeg Skill** | 本地自动剪辑、加字幕、去静音、调画幅和响度 | [kajisho5/ffmpeg-skill](https://github.com/kajisho5/ffmpeg-skill) |

> 更多推荐与安装说明见 [docs/recommended-skills.md](docs/recommended-skills.md)。

---

<details>
<summary>进阶说明：仓库目录结构 & 自定义环境变量</summary>

```text
antigravity-zh-kit/
├── install.ps1 / install.sh      # 一键安装脚本
├── rules/AGENTS.template.md      # 全局规则模板（可按需删减）
├── skills/
│   ├── chinese-summary/          # 会话自动中文命名（纯 Python 标准库）
│   ├── session-organizer/        # 左侧会话聚类整理与瘦身（纯 Python 标准库）
│   └── pdf-fast-extract/         # PDF 高速 OCR + 划线批注识别
└── docs/recommended-skills.md    # 第三方 Skills 推荐清单
```

如果你自定义了 Antigravity 的数据目录或备份路径，可设置以下环境变量（不设则自动使用默认路径）：
* `ANTIGRAVITY_HOME`：默认 `~/.gemini/antigravity`
* `ANTIGRAVITY_BACKUP_DIR`：默认 `~/.gemini/antigravity/backups`

</details>

---

## 开源协议

基于 [MIT License](LICENSE) 开源，欢迎 Star、Fork 和分享给身边的朋友！
