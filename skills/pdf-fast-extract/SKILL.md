---
name: pdf-fast-extract
description: >-
  高速读取 PDF 与提取重点划线批注的专用技能。适用于普通文字 PDF、扫描版图片 PDF（教材、论文、电子笔记等）
  以及带电子划线/高亮批注的 PDF。严禁将 PDF 逐页渲染为图片后喂给大模型，强制使用 PyMuPDF + RapidOCR +
  矢量批注坐标碰撞检测在本地一次性提取纯文本与重点颜色标签。
---

# PDF Fast Extract（PDF 高速提取与划线批注识别）

## 核心原则

1. **严禁逐页转图喂给大模型**：
   - 不要将多页 PDF 渲染成 PNG/JPG 后循环调用视觉读图，否则会迅速塞爆上下文、大幅拉长推理耗时甚至触发超时中断。
   - 仅当用户主动提供单张排版参考截图时，才允许读图 1 次。

2. **文字版与扫描版自动分流**：
   - 内置脚本会自动判断每一页是否包含可用文字层：文字页直接高速提取，扫描图片页自动走本地 `RapidOCR` 识别，同时基于矢量批注坐标碰撞自动标注**红线 / 黄线 / 绿线 / 蓝线 / 其他批注**。

## 依赖安装（首次使用）

```bash
pip install pymupdf rapidocr-onnxruntime
```

## 执行方式

```bash
# Windows (PowerShell)
python "$HOME\.gemini\config\skills\pdf-fast-extract\scripts\extract_pdf_with_marks.py" --pdf "<PDF路径>" --out "<输出txt路径>" --start 1 --end 0 --dpi 150

# macOS / Linux
python3 "$HOME/.gemini/config/skills/pdf-fast-extract/scripts/extract_pdf_with_marks.py" --pdf "<PDF路径>" --out "<输出txt路径>" --start 1 --end 0 --dpi 150
```

* `--start` / `--end`：页码范围（从 1 开始，`--end 0` 表示提取至最后一页）。
* `--dpi`：扫描页 OCR 渲染清晰度，默认 `150`（小字密集时可调至 `200`）。
* 输出格式：`[PDF_P{页码}|{划线颜色标签}|{native或置信度}] 文本内容`，AI 只需阅读纯文本 `.txt` 即可精准定位重点内容。
