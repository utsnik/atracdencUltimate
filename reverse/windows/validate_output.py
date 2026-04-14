import csv, collections, statistics

with open("deep_metrics_YOUtopia_source.csv") as f:
    rows = list(csv.DictReader(f))

print(f"Total rows: {len(rows)}")
print(f"Expected:   10452 frames x 2 channels = 20904")

tonal   = [int(r["tonal_bits"])    for r in rows]
gain    = [int(r["gain_bits"])     for r in rows]
sideinfo = [int(r["sideinfo_bits"]) for r in rows]
transient = [r["transient_triggered"] for r in rows]

print(f"tonal_bits:    min={min(tonal)} max={max(tonal)} mean={statistics.mean(tonal):.1f}")
print(f"gain_bits:     min={min(gain)} max={max(gain)} mean={statistics.mean(gain):.1f}")
print(f"sideinfo_bits: min={min(sideinfo)} max={max(sideinfo)} mean={statistics.mean(sideinfo):.1f}")
print(f"transient counts: {dict(collections.Counter(transient))}")

print(f"\nCSV columns: {list(rows[0].keys())}")

# Sample 5 rows
print("\nFirst 5 rows:")
for r in rows[:5]:
    print(r)
