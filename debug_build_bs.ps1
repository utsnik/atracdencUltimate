$vcvars = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
if (-not (Test-Path $vcvars)) {
    $vcvars = "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
}

$cmd = "`"$vcvars`" && cl /c /EHsc /std:c++17 /I src /I src/atrac/at1 /I src/atrac/at3 /I src/lib/bitstream /I src/lib/liboma/include /I src/lib/fft/kissfft_impl /I build/src src/atrac/at3/atrac3_bitstream.cpp 2> build_error_bs.txt"
cmd.exe /c $cmd
Get-Content build_error_bs.txt
