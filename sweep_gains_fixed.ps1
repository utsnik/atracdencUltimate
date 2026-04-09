$atracdenc = "C:\Users\Igland\Antigravity\Ghidra\atracdenc\build\src\atracdenc.exe"
$at3tool = "C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\windows\at3tool.exe"
$input_wav = "C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\quality\input\sine_1k_5s.wav"
$workdir = "C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\quality\sweep"
if (-not (Test-Path $workdir)) { mkdir $workdir }

$gains = @(1.0, 0.01, 0.00390625, 0.0014, 0.001, 0.0001, 0.00001)

foreach ($g in $gains) {
    Write-Host "Testing Gain: $g"
    $env:ATRACDENC_MDCT_GAIN = $g
    $output_oma = "$workdir\gain_$g.oma"
    $decoded_wav = "$workdir\gain_$g.wav"
    
    # Encode
    & $atracdenc -e atrac3plus -i $input_wav -o $output_oma 2>$null
    
    # Decode with at3tool
    & $at3tool -d $output_oma $decoded_wav 2>$null
    
    if (Test-Path $decoded_wav) {
        # Calculate SNR (using a simple python snippet)
        $snr = python -c "import numpy as np; import soundfile as sf; x, sr = sf.read(r'$input_wav'); y, sr2 = sf.read(r'$decoded_wav'); y = y[:len(x)]; x = x[:len(y)]; noise = x - y; snr = 10 * np.log10(np.sum(x**2)/np.sum(noise**2)); print(snr)"
        Write-Host "Gain: $g -> SNR: $snr dB"
    } else {
        Write-Host "Gain: $g -> FAILED to decode"
    }
}
