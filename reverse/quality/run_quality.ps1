param(
  [string]$At3Tool = "C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\windows\at3tool.exe",
  [string]$Atracdenc = "",
  [int]$Bitrate = 128,
  [switch]$Sweep
)

$ErrorActionPreference = "Stop"

$workdir = "C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\quality"
if (-not (Test-Path $At3Tool)) { throw "at3tool not found: $At3Tool" }

$cmd = @(
  "python",
  "$workdir\compare_at3_quality.py",
  "--at3tool", $At3Tool,
  "--workdir", $workdir,
  "--bitrate", $Bitrate
)

if ($Atracdenc -ne "") {
  if (-not (Test-Path $Atracdenc)) { throw "atracdenc not found: $Atracdenc" }
  $cmd += "--atracdenc"
  $cmd += $Atracdenc
}

if ($Sweep) {
  $cmd += "--ghadbg-sweep"
  $cmd += "--report"
  $cmd += "$workdir\quality_report.md"
}

& $cmd[0] $cmd[1..($cmd.Length-1)]
