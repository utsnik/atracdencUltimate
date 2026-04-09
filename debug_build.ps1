$vcvars = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
if (-not (Test-Path $vcvars)) {
    $vcvars = "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
}

$cmd = "`"$vcvars`" && cl /c /EHsc /std:c++17 /I src /I src/atrac/at3 src/atrac/at3/atrac3.cpp 2> build_error.txt"
cmd.exe /c $cmd
Get-Content build_error.txt
