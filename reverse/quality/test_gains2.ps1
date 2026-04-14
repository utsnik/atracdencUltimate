$gains = @("0.0625", "0.25", "0.5", "1.0", "1.414", "2.0", "4.0", "16.0")
$out_csv = "C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\quality\out\gain_sweep2.csv"
Set-Content $out_csv "Gain,SNR"

foreach ($g in $gains) {
    [Environment]::SetEnvironmentVariable("ATRACDENC_MDCT_GAIN", $g, "Process")
    $cmd = "python C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\quality\compare_at3_quality.py --at3tool C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\windows\at3tool.exe --atracdenc C:\Users\Igland\Antigravity\Ghidra\atracdenc\build\src\atracdenc.exe --workdir C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\quality --ghadbg-sweep"
    Invoke-Expression $cmd | Out-Null
    $report = Get-Content -Raw "C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\quality\out\quality_report.json" | ConvertFrom-Json
    
    $sine_snr = 0
    foreach ($item in $report.sweep[0].items) {
        if ($item.input -match "sine_1k_5s.wav") {
            $sine_snr = $item.atracdenc_metrics_aligned.snr_db
        }
    }
    
    $line = "$g,$sine_snr"
    Add-Content $out_csv $line
    Write-Host "Gain: $g -> SNR: $sine_snr"
}
