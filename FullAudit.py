def b_to_s(b): 
    return format(b, '08b')

def load_u(f, off):
    with open(f, 'rb') as fp:
        fp.seek(off)
        return fp.read(96)

def compare():
    s_file = 'audit_sony.at3'
    m_file = 'quality_verify_v2/encoded_atracdenc.at3'
    
    s0 = load_u(s_file, 80)
    m0 = load_u(m_file, 80)
    s1 = load_u(s_file, 176)
    m1 = load_u(m_file, 176)
    
    print('SU0 S:', ' '.join(b_to_s(x) for x in s0[:8]))
    print('SU0 M:', ' '.join(b_to_s(x) for x in m0[:8]))
    print('SU1 S:', ' '.join(b_to_s(x) for x in s1[:8]))
    print('SU1 M:', ' '.join(b_to_s(x) for x in m1[:8]))

if __name__ == "__main__":
    compare()
