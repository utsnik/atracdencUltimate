import sys

def splice(ref_file, mine_file, out_file):
    # Read first 80 bytes from REF (Sony Header)
    with open(ref_file, 'rb') as f:
        ref_header = f.read(80)
    
    # Read payload from MINE (from first syncword A2)
    with open(mine_file, 'rb') as f:
        mine_data = f.read()
    
    sync_pos = mine_data.find(b'\xA2')
    if sync_pos == -1:
        print("No sync word in MINE")
        return
        
    mine_payload = mine_data[sync_pos:]
    
    with open(out_file, 'wb') as f:
        f.write(ref_header)
        f.write(mine_payload)
    print(f"Spliced {len(ref_header)} header bytes with {len(mine_payload)} payload bytes to {out_file}")

if __name__ == "__main__":
    splice(sys.argv[1], sys.argv[2], sys.argv[3])
