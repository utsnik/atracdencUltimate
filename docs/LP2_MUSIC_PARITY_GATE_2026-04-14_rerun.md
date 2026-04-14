# LP2 Music Parity Gate

Candidate mode: `quality-v10-stable`; baseline mode: `quality-v10-native`.

## Safety Gate

- Fast corpus gate: `PASS`
- Long YOUtopia242 gate: `PASS`
- YOUtopia242 worst hotspot: `-0.057` dB
- YOUtopia full/HF delta vs native: `+0.001` / `+0.001` dB
- Safety status: `PASS`

## Music Targets

- YOUtopia Sony distance: `1.022` (target `<= 0.90`)
- Badlands Sony distance: `1.239` (target `<= 1.00`)
- Music target status: `PENDING`
- Consecutive music-target passes: `0`

## Reports

- Fast markdown: `docs\LP2_FAST_MUSIC_GATE.md`
- Fast json: `docs\LP2_FAST_MUSIC_GATE.json`
- Long markdown: `docs\LP2_LONG_YOUTOPIA242_GATE.md`
- Long json: `docs\LP2_LONG_YOUTOPIA242_GATE.json`
