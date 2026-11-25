#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="${HOME}/.gemini/config"
TARGET_SKILLS_DIR="${CONFIG_DIR}/skills"
WITH_RULES=0

for arg in "$@"; do
  if [ "$arg" = "--with-rules" ]; then
    WITH_RULES=1
  fi
done

echo "=== Antigravity 中文效率套件安装向导 (macOS / Linux) ==="
mkdir -p "${TARGET_SKILLS_DIR}"

for skill in chinese-summary session-organizer pdf-fast-extract; do
  src="${REPO_ROOT}/skills/${skill}"
  dst="${TARGET_SKILLS_DIR}/${skill}"
  if [ -d "${dst}" ]; then
    echo "[更新] 同步技能: ${skill} -> ${dst}"
  else
    echo "[安装] 复制技能: ${skill} -> ${dst}"
  fi
  rm -rf "${dst}"
  cp -R "${src}" "${dst}"
done

if [ "${WITH_RULES}" -eq 1 ]; then
  SRC_RULE="${REPO_ROOT}/rules/AGENTS.template.md"
  DST_RULE="${CONFIG_DIR}/AGENTS.md"
  if [ -f "${DST_RULE}" ]; then
    echo "[跳过] 检测到已有全局规则 ${DST_RULE}，为保护您的个人配置未覆盖。"
    echo "       请手动参考 ${SRC_RULE} 按需合并条款。"
  else
    cp "${SRC_RULE}" "${DST_RULE}"
    echo "[安装] 已部署全局规则模板 -> ${DST_RULE}"
  fi
fi

echo ""
echo "安装完成！可选下一步："
echo "1. 如需使用 pdf-fast-extract（扫描版 PDF OCR），请执行："
echo "   pip install -r \"${TARGET_SKILLS_DIR}/pdf-fast-extract/requirements.txt\""
echo "2. 如未加 --with-rules，可手动查看 rules/AGENTS.template.md 并复制到 ${CONFIG_DIR}/AGENTS.md"
