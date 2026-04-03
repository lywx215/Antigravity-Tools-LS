# dev.ps1 - Antigravity-Tools-LS 部署工具
param(
    [switch]$DryRun,   # 仅打包预检，不上传
    [switch]$Deploy,   # 部署到 Zeabur
    [string]$Services = "ts",  # 目标服务 (逗号分隔)
    [int]$Parallel = 5
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

if ($DryRun) {
    Write-Host "`n  🔍 Dry-Run 预检模式" -ForegroundColor Cyan
    Write-Host "  ===================" -ForegroundColor DarkGray
    python "$scriptDir\zeabeucli\deploy.py" --services $Services --dry-run
}
elseif ($Deploy) {
    Write-Host "`n  📤 部署到 Zeabur" -ForegroundColor Cyan
    Write-Host "  ===================" -ForegroundColor DarkGray
    python "$scriptDir\zeabeucli\deploy.py" --services $Services --parallel $Parallel
}
else {
    Write-Host ""
    Write-Host "  Antigravity-Tools-LS 部署工具" -ForegroundColor Cyan
    Write-Host "  =============================" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  .\dev.ps1 -DryRun                    # 仅打包预检 (不上传)"
    Write-Host "  .\dev.ps1 -Deploy                    # 部署到 ts"
    Write-Host "  .\dev.ps1 -Deploy -Services 'ts'     # 指定服务"
    Write-Host "  .\dev.ps1 -Deploy -Parallel 10       # 并行部署"
    Write-Host ""
}
