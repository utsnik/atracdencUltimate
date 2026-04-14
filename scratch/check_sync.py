with open('test_baseline.at3', 'rb') as f:
    data = f.read(2048)

first_sync = data.find(b'\xA2')
second_sync = data.find(b'\xA2', first_sync + 1)

print(f"First sync byte at: {first_sync}")
print(f"Second sync byte at: {second_sync}")
print(f"Difference (Frame Size?): {second_sync - first_sync}")
print(f"Header size (First Sync - 0): {first_sync}")
