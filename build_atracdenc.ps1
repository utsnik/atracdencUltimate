# ATRAC3 Definitive Build Script
$VSPath = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"

if (!(Test-Path "build")) { New-Item -ItemType Directory -Path "build" }

# Execute the entire build process inside a single CMD instance to preserve MSVC environment
cmd /c "`"$VSPath`" && cd build && cmake -G `"NMake Makefiles`" -DCMAKE_BUILD_TYPE=Release .. && nmake atracdenc"

if (Test-Path "build\src\atracdenc.exe") {
    Write-Host "SUCCESS: atracdenc.exe built."
} else {
    Write-Error "FAILURE: atracdenc.exe NOT FOUND."
}
