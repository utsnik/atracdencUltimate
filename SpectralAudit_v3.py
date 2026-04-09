import os

def to_bits(byte_data):
    return "".join(f"{b:08b}" for b in byte_data)

class BitReader:
    def __init__(self, bits):
        self.bits = bits
        self.pos = 0
    def read(self, n):
        res = self.bits[self.pos:self.pos+n]
        self.pos += n
        return res
    def val(self, n):
        return int(self.read(n), 2)

def decode_su0(bits):
    r = BitReader(bits)
    sync = r.val(6)
    bands = r.val(2)
    print(f"Header: Sync={sync:02x} (+3={bands+1} bands)")
    
    for b in range(bands + 1):
        num_gp = r.val(3)
        print(f" Band {b}: {num_gp} GainPoints")
        for _ in range(num_gp):
            level = r.val(4)
            loc = r.val(5)
            print(f"  GP: Level={level} Loc={loc}")
    
    # After gain, Tonal then Specs
    # This is complex, but let's see codedBlocks
    tonal_presence = r.val(1)
    print(f" Tonal Presence: {tonal_presence}")
    # ... assuming 0 tonal for now to find codedBlocks ...
    
    # Wait, in atrac3_bitstream.cpp:
    # EncodeTonalComponents writes 1 bit for presence? 
    # NO, it writes 3 bits for codedValues if any.
    
    # Let's just dump the next 16 bits raw
    print(f" Next 24 bits: {r.read(24)}")

def spectral_audit():
    sony_file = "tone_sony.at3"
    mine_file = "tone_mine.at3"
    
    with open(sony_file, "rb") as f:
        sony_data = f.read()
    with open(mine_file, "rb") as f:
        mine_data = f.read()

    # Offset 80 is start of data
    offsets = [80, 80 + 192, 80 + 384, 80 + 384 + 192]
    
    for i, off in enumerate(offsets):
        s_su = sony_data[off:off+96]
        m_su = mine_data[off:off+96]
        
        print(f"=== Frame {i} (Offset {off}) ===")
        s_bits = to_bits(s_su)
        m_bits = to_bits(m_su)
        
        print("SONY:")
        decode_su0(s_bits)
        print("MINE:")
        decode_su0(m_bits)
        print()

if __name__ == "__main__":
    spectral_audit()
