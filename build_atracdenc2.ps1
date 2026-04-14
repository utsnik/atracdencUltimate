# ATRAC3 Definitive Build Script (build2)
$VSPath = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"

if (!(Test-Path "build2")) { New-Item -ItemType Directory -Path "build2" }

cmd /c "`"$VSPath`" && cd build2 && cmake -G `"NMake Makefiles`" -DCMAKE_BUILD_TYPE=Release .. && nmake atracdenc"

if (Test-Path "build2\src\atracdenc.exe") {
    Write-Host "SUCCESS: atracdenc.exe built."
} else {
    Write-Error "FAILURE: atracdenc.exe NOT FOUND."
}
