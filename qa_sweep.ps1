$ffmpeg = "C:\Users\Igland\Documents\NRK Downloader\ffmpeg.exe"
$enc = "C:\Users\Igland\Antigravity\Ghidra\atracdenc\build2\src\atracdenc.exe"
$in = "orig_benchmark.wav"

& $enc -e atrac3 -i $in -o qa_default.at3.wav --bitrate 132 | Out-Null
& $enc -e atrac3 -i $in -o qa_nogain.at3.wav --bitrate 132 --nogaincontrol | Out-Null
& $enc -e atrac3 -i $in -o qa_notonal.at3.wav --bitrate 132 --notonal | Out-Null
& $enc -e atrac3 -i $in -o qa_nogain_notonal.at3.wav --bitrate 132 --nogaincontrol --notonal | Out-Null
& $enc -e atrac3 -i $in -o qa_bfu24.at3.wav --bitrate 132 --bfuidxconst 24 | Out-Null
& $enc -e atrac3 -i $in -o qa_bfu32.at3.wav --bitrate 132 --bfuidxconst 32 | Out-Null

& $ffmpeg -y -v error -i qa_default.at3.wav qa_default_dec.wav
& $ffmpeg -y -v error -i qa_nogain.at3.wav qa_nogain_dec.wav
& $ffmpeg -y -v error -i qa_notonal.at3.wav qa_notonal_dec.wav
& $ffmpeg -y -v error -i qa_nogain_notonal.at3.wav qa_nogain_notonal_dec.wav
& $ffmpeg -y -v error -i qa_bfu24.at3.wav qa_bfu24_dec.wav
& $ffmpeg -y -v error -i qa_bfu32.at3.wav qa_bfu32_dec.wav
