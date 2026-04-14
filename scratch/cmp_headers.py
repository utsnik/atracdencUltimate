def dump_hex(filename, count=128):
    try:
        with open(filename, 'rb') as f:
            data = f.read(count)
            return ' '.join(f'{b:02X}' for b in data)
    except Exception as e:
        return str(e)

ref = dump_hex('ref_lp2.at3')
mine = dump_hex('test_baseline.at3')

print(f'REF:  {ref}')
print(f'MINE: {mine}')
