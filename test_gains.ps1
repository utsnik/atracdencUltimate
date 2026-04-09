# test_gains.ps1
# Sweep ATRACDENC_MDCT_GAIN to find optimal scaling for SNR.

$gains = @(0.000030517578125, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 32768.0, 65536.0)
$atracdenc = "C:\Users\Igland\Antigravity\Ghidra\atracdenc\build\src\atracdenc.exe"
$quality_dir = "C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\quality"

foreach ($g in $gains) {
    Write-Host "Testing Gain: $g"
    $env:ATRACDENC_MDCT_GAIN = $g
    
    # Run quality test for a single wav to save time
    & powershell -ExecutionPolicy Bypass -Command "& { .\run_quality.ps1 -Atracdenc $atracdenc -wavs sine_1k_24bit_44100_01s.wav }"
    
    # Read the resulting JSON and report SNR
    $json = Get-Content -Raw "$quality_dir\out\quality_report.json" | ConvertFrom-Json
    $snr = $json.sweep[0].atracdenc_metrics_aligned.snr_db
    Write-Host "Gain $g -> SNR: $snr dB"
}
