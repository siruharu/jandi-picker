# Windows counterpart of install.sh: registers a Task Scheduler job that runs
# publish_til.py every day (launchd + pmset equivalent).
# Kept ASCII-only on purpose: Windows PowerShell 5.1 reads BOM-less scripts as ANSI.
param(
    [string]$Time = "16:30",
    [string]$TaskName = "jandi-picker"
)

$ErrorActionPreference = "Stop"

$RepoDir = Split-Path -Parent $PSScriptRoot
$Script = Join-Path $RepoDir "scripts\publish_til.py"
$LogDir = Join-Path $RepoDir "logs"

# The Microsoft Store alias under WindowsApps is a stub that only opens the Store.
$Python = Get-Command python -All -ErrorAction SilentlyContinue |
    Where-Object { $_.Source -notlike "*\WindowsApps\*" } |
    Select-Object -First 1 -ExpandProperty Source
if (-not $Python) {
    Write-Host "x python not found. Install it first:  winget install Python.Python.3.12"
    exit 1
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "x git not found on PATH."
    exit 1
}

New-Item -ItemType Directory -Force $LogDir | Out-Null

$Command = "`"$Python`" `"$Script`" >> `"$LogDir\stdout.log`" 2>> `"$LogDir\stderr.log`""
$Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$Command`"" -WorkingDirectory $RepoDir
$Trigger = New-ScheduledTaskTrigger -Daily -At $Time
# WakeToRun replaces `pmset repeat wakeorpoweron`; StartWhenAvailable catches up
# after the PC was off at the scheduled time.
$Settings = New-ScheduledTaskSettingsSet -WakeToRun -StartWhenAvailable `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10)

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger `
    -Settings $Settings -Force | Out-Null

Write-Host "v Scheduled task registered: $TaskName (daily $Time)"
Write-Host ""

$Email = git -C $RepoDir config user.email
if (-not $Email) {
    Write-Host "! git user.name / user.email are not set - commits will fail. Set them for this repo:"
    Write-Host "    git -C `"$RepoDir`" config user.name  <github-username>"
    Write-Host "    git -C `"$RepoDir`" config user.email <email-registered-on-github>"
    Write-Host ""
}

Write-Host "Check:"
Write-Host "    Get-ScheduledTask $TaskName | Get-ScheduledTaskInfo"
Write-Host "    Get-Content `"$LogDir\stdout.log`" -Tail 20 -Encoding UTF8"
Write-Host ""
Write-Host "Manual run:"
Write-Host "    Start-ScheduledTask $TaskName"
Write-Host "    & `"$Python`" `"$Script`""
Write-Host ""
Write-Host "Uninstall:"
Write-Host "    Unregister-ScheduledTask $TaskName -Confirm:`$false"
