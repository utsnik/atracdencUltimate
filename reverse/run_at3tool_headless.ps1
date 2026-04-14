param(
  [string]$BinaryPath = "C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\windows\at3tool.exe",
  [string]$OutDir = "C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\out\at3tool",
  [string]$JavaHome = ""
)

$ErrorActionPreference = "Stop"

$ghidraRoot = "C:\Users\Igland\Antigravity\Ghidra\ghidra\build\dist\ghidra_12.2_DEV_win\ghidra_12.2_DEV"
$analyzeHeadless = Join-Path $ghidraRoot "support\analyzeHeadless.bat"
$projectDir = "C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\ghidra_projects"
$projectName = "at3tool_headless"
$scriptPath = "C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\ghidra_scripts"

if (-not (Test-Path $BinaryPath)) {
  throw "Binary not found: $BinaryPath"
}
if (-not (Test-Path $analyzeHeadless)) {
  throw "analyzeHeadless not found: $analyzeHeadless"
}

if ($JavaHome -ne "") {
  if (-not (Test-Path $JavaHome)) {
    throw "JAVA_HOME not found: $JavaHome"
  }
  $env:JAVA_HOME = $JavaHome
  $env:PATH = (Join-Path $JavaHome "bin") + ";" + $env:PATH
}

try {
  $null = Get-Command java -ErrorAction Stop
} catch {
  throw "Java not found. Install a JDK and pass -JavaHome or set JAVA_HOME."
}

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

& $analyzeHeadless $projectDir $projectName -deleteProject -import $BinaryPath -analysisTimeoutPerFile 300 -scriptPath $scriptPath -postScript At3Dump.java $OutDir

Write-Host "Done. Output in $OutDir"
