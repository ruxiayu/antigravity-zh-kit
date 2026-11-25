# 我实测顺手的第三方 Skills 推荐清单

> 说明：本清单仅整理作者在 Antigravity 日常使用中**实测顺手的优秀开源技能**，均指向原作者仓库或官方项目，**本仓库不包含任何第三方技能源码**，请前往原项目按其开源协议自行安装使用。

## 1. 自媒体排版、配图与信息图创作

| 技能名称 | 核心用途 | 原仓库链接 |
| :--- | :--- | :--- |
| **Baoyu Skills（宝玉技能套件）** | 覆盖文章封面（`baoyu-cover-image`）、文章配图（`baoyu-article-illustrator`）、信息图（`baoyu-infographic`）、小红书/图文卡片（`baoyu-xhs-images`）、Markdown 转微信公众号 HTML（`baoyu-markdown-to-html`）与公众号发布（`baoyu-post-to-wechat`） | [JimLiu/baoyu-skills](https://github.com/JimLiu/baoyu-skills) |
| **Viral Writer** | 基于 11 个内容洞见维度的自媒体爆款文案创作，支持公众号、小红书、抖音风格 | [nashsu/Viral_Writer_Skill](https://github.com/nashsu/Viral_Writer_Skill) |
| **Humanizer-zh** | 去除中文文章中的 AI 味、空话与模板化表达，让行文更自然 | [op7418/Humanizer-zh](https://github.com/op7418/Humanizer-zh)（基于 [blader/humanizer](https://github.com/blader/humanizer)） |

## 2. 省 Token 与上下文效率优化

| 技能名称 | 核心用途 | 原仓库链接 |
| :--- | :--- | :--- |
| **Caveman / Caveman-Compress** | 极简“穴居人”精炼回复模式与记忆文件压缩，大幅减少无意义废话与输入/输出 Token 消耗 | [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) |
| **Planning with Files / Token Optimizer / Skill Creator** | 多步骤文件持久化规划、上下文浪费审计、以及从零构建与评测自定义 Skill 的元技能 | 可在各大 Agent Skills 市场或 GitHub 搜索对应项目名获取最新版 |

## 3. 音视频与后期剪辑工作流

| 技能名称 | 核心用途 | 原仓库链接 |
| :--- | :--- | :--- |
| **FFmpeg Skill** | 纯本地 FFmpeg 音视频剪辑、画幅重构、字幕、静音切除、响度标准化与平台导出检测 | [kajisho5/ffmpeg-skill](https://github.com/kajisho5/ffmpeg-skill) |
| **ClipSkills** | 面向 AI Agent 的剪辑方法论知识库（口播精剪、卡点、B-roll、调色、转场等软件无关决策规则） | 社区开源项目（作者 `appergb`，MIT 协议） |

---

### 安装提示
下载任意第三方 Skill 后，只需将其包含 `SKILL.md` 的文件夹放入 `~/.gemini/config/skills/<skill-name>/`，重启或开启新会话即可在 Antigravity 中自动识别触发。
