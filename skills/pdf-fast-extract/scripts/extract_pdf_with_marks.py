#!/usr/bin/env python3
"""Fast PDF text & annotation color extractor using PyMuPDF + RapidOCR.

Outputs pure text lines tagged with page number, highlight/underline color, and
OCR confidence so AI agents never need to render PDF pages as images into context.
"""

import argparse
import os
import sys

try:
    import pymupdf
except ImportError:
    print("ERROR: Missing dependency 'pymupdf'. Install via: pip install pymupdf rapidocr-onnxruntime", file=sys.stderr)
    sys.exit(1)

try:
    from rapidocr_onnxruntime import RapidOCR
except ImportError:
    print("ERROR: Missing dependency 'rapidocr-onnxruntime'. Install via: pip install pymupdf rapidocr-onnxruntime", file=sys.stderr)
    sys.exit(1)


def classify_rgb(color):
    if not color or len(color) < 3:
        return None
    r, g, b = color[0], color[1], color[2]
    if max(r, g, b) > 1.0:
        r, g, b = r / 255.0, g / 255.0, b / 255.0
    if r > 0.6 and g < 0.4 and b < 0.4:
        return "红线"
    if r > 0.7 and g > 0.6 and b < 0.4:
        return "黄线"
    if g > 0.5 and r < 0.5 and b < 0.6:
        return "绿线"
    if b > 0.5 and r < 0.5:
        return "蓝线"
    return "其他批注"


def collect_mark_rects(page):
    marks = []
    for annot in page.annots() or []:
        color = annot.colors.get("stroke") or annot.colors.get("fill")
        label = classify_rgb(color)
        if label:
            marks.append((annot.rect, label))
    for d in page.get_drawings() or []:
        color = d.get("color") or d.get("fill")
        label = classify_rgb(color)
        rect = d.get("rect")
        if label and rect:
            marks.append((pymupdf.Rect(rect), label))
    return marks


def rects_overlap(r1, r2, pad=4.0):
    expanded = pymupdf.Rect(r1.x0 - pad, r1.y0 - pad, r1.x1 + pad, r1.y1 + pad)
    return expanded.intersects(r2)


def main():
    parser = argparse.ArgumentParser(description="Fast PDF OCR + annotation color extractor")
    parser.add_argument("--pdf", required=True, help="Path to PDF file")
    parser.add_argument("--out", required=True, help="Output .txt path")
    parser.add_argument("--start", type=int, default=1, help="Start page (1-based)")
    parser.add_argument("--end", type=int, default=0, help="End page (1-based, 0 = last)")
    parser.add_argument("--dpi", type=int, default=150, help="Render DPI for OCR")
    args = parser.parse_args()

    doc = pymupdf.open(args.pdf)
    total = len(doc)
    start_idx = max(0, args.start - 1)
    end_idx = total if args.end <= 0 else min(total, args.end)

    ocr = RapidOCR()
    scale = args.dpi / 72.0
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)

    with open(args.out, "w", encoding="utf-8") as f:
        for i in range(start_idx, end_idx):
            page = doc[i]
            marks = collect_mark_rects(page)
            f.write(f"=== {os.path.basename(args.pdf)} PDF_P{i + 1} ===\n")

            native_text = page.get_text("text").strip()
            if len(native_text) > 30:
                for blk in page.get_text("blocks"):
                    if len(blk) >= 5 and isinstance(blk[4], str) and blk[4].strip():
                        brect = pymupdf.Rect(blk[:4])
                        hit = sorted({lbl for mrect, lbl in marks if rects_overlap(brect, mrect)})
                        tag = ",".join(hit) if hit else "无"
                        line = blk[4].strip().replace("\n", " ")
                        f.write(f"[PDF_P{i + 1}|{tag}|native] {line}\n")
            else:
                pix = page.get_pixmap(dpi=args.dpi)
                res, _ = ocr(pix.tobytes("png"))
                if res:
                    for box, text, score in res:
                        xs = [pt[0] / scale for pt in box]
                        ys = [pt[1] / scale for pt in box]
                        trect = pymupdf.Rect(min(xs), min(ys), max(xs), max(ys))
                        hit = sorted({lbl for mrect, lbl in marks if rects_overlap(trect, mrect)})
                        tag = ",".join(hit) if hit else "无"
                        f.write(f"[PDF_P{i + 1}|{tag}|{score:.2f}] {text}\n")
            f.write("\n")

    print(f"DONE: extracted pages {start_idx + 1}-{end_idx} -> {args.out}")


if __name__ == "__main__":
    main()
