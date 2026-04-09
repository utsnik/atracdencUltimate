@echo off
set "VCVARS=C:\PROGRA~2\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
if not exist "%VCVARS%" set "VCVARS=C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
echo Using VCVARS: %VCVARS%
call "%VCVARS%"
cd /d "c:\Users\Igland\Antigravity\Ghidra\atracdenc\build"
cmake --build . --config Release
