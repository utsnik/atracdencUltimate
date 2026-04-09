import struct
import os

def dump_riff(filename):
    if not os.path.exists(filename):
        print(f"File not found: {filename}")
        return
    with open(filename, "rb") as f:
        data = f.read(512)
    
    fmt_idx = data.find(b'fmt ')
    if fmt_idx == -1: 
        print(f"fmt chunk not found in {filename}")
        return
    
    # format(2) channels(2) rate(4) avg(4) align(2) bps(2) cbsize(2)
    fmt_data = data[fmt_idx+8:] 
    if len(fmt_data) < 18:
        print(f"fmt data too short in {filename}")
        return
        
    format_tag, channels, rate, byte_rate, align, bps, cbSize = struct.unpack("<HHIIHHH", fmt_data[:18])
    
    extradata = fmt_data[18:18+cbSize]
    
    print(f"File: {filename}")
    print(f"  FormatTag: 0x{format_tag:04X}")
    print(f"  Channels:  {channels}")
    print(f"  Rate:      {rate}")
    print(f"  ByteRate:  {byte_rate}")
    print(f"  Align:     {align}")
    print(f"  cbSize:    {cbSize}")
    if cbSize >= 14:
        # ATRAC3 extradata (14 bytes): unknown0(2), samples_per_block(4), mode(2), mode2(2), unknown1(2), unknown2(2)
        vals = struct.unpack("<HIHHHH", extradata[:14])
        print(f"  ExtraData: {vals}")
        
    fact_idx = data.find(b'fact')
    if fact_idx != -1:
        # fact size(4) total_samples(4)
        total = struct.unpack("<I", data[fact_idx+8:fact_idx+12])[0]
        print(f"  FactTotal: {total}")

if __name__ == "__main__":
    dump_riff("audit_sony.at3")
    dump_riff("quality_verify_v2/test_no.at3")
