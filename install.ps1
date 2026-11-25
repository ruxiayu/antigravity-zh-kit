<#
.SYNOPSIS
  一键将 antigravity-zh-kit 的自研技能部署到本机 Antigravity 配置目录（安全增量，不覆盖已有规则）。
.PARAMETER WithRules
  如果本机尚无 ~/.gemini/config/AGENTS.md，则自动复制模板；若已存在则不覆盖并给出手动合并提示。
#>
param(
    [switch]$WithRules
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ConfigDir = Join-Path $HOME ".gemini\config"
$TargetSkillsDir = Join-Path $ConfigDir "skills"

Write-Host "=== Antigravity 中文效率套件安装向导 (Windows) ===" -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path $TargetSkillsDir | Out-Null

$Skills = @("chinese-summary", "session-organizer", "pdf-fast-extract")
foreach ($skill in $Skills) {
    $src = Join-Path $RepoRoot "skills\$skill"
    $dst = Join-Path $TargetSkillsDir $skill
    if (Test-Path $dst) {
        Write-Host "[更新] 同步技能: $skill -> $dst" -ForegroundColor Yellow
    } else {
        Write-Host "[安装] 复制技能: $skill -> $dst" -ForegroundColor Green
    }
    Copy-Item -Path $src -Destination $TargetSkillsDir -Recurse -Force
}

if ($WithRules) {
    $srcRule = Join-Path $RepoRoot "rules\AGENTS.template.md"
    $dstRule = Join-Path $ConfigDir "AGENTS.md"
    if (Test-Path $dstRule) {
        Write-Host "[跳过] 检测到已有全局规则 $dstRule，为保护您的个人配置未覆盖。" -ForegroundColor Yellow
        Write-Host "       请手动参考 $srcRule 按需合并条款。" -ForegroundColor Yellow
    } else {
        Copy-Item -Path $srcRule -Destination $dstRule
        Write-Host "[安装] 已部署全局规则模板 -> $dstRule" -ForegroundColor Green
    }
}

Write-Host "`n安装完成！可选下一步：" -ForegroundColor Cyan
Write-Host "1. 如需使用 pdf-fast-extract（扫描版 PDF OCR），请执行："
Write-Host "   pip install -r `"$TargetSkillsDir\pdf-fast-extract\requirements.txt`""
Write-Host "2. 如未加 -WithRules，可手动查看 rules\AGENTS.template.md 并复制到 $ConfigDir\AGENTS.md"
