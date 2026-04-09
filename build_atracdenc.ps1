param(
  [string]$SrcDir = "C:\Users\Igland\Antigravity\Ghidra\atracdenc",
  [string]$BuildDir = "C:\Users\Igland\Antigravity\Ghidra\atracdenc\build"
)

$ErrorActionPreference = "Stop"

$vcvars = $null
$vcvarsCandidates = @(
  "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat",
  "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
)

foreach ($p in $vcvarsCandidates) {
  if (Test-Path $p) { $vcvars = $p; break }
}

if (-not $vcvars) {
  throw "MSVC build tools not found. Install Visual Studio C++ build tools (Desktop development with C++)."
}

if (Test-Path $BuildDir) {
  Remove-Item -Recurse -Force -Path $BuildDir
}
New-Item -ItemType Directory -Force -Path $BuildDir | Out-Null

$cmd = '"' + $vcvars + '" && cd /d "' + $BuildDir + '" && cmake -G "NMake Makefiles" -DCMAKE_BUILD_TYPE=Release "' + $SrcDir + '" && cmake --build . --verbose'
cmd.exe /c $cmd
