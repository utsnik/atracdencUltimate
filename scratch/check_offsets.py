with open('ref_lp2.at3', 'rb') as f:
    data = f.read(1024)

print("fmt  at: %d" % data.find(b'fmt '))
print("fact at: %d" % data.find(b'fact'))
print("data at: %d" % data.find(b'data'))
print("sync at: %d" % data.find(b'\xA2'))
