from ghidra.util.task import ConsoleTaskMonitor
import struct

def find_sequence(pattern_vals, is_double=False):
    fm = currentProgram.getMemory()
    fmt = '<d' if is_double else '<f'
    size = 8 if is_double else 4
    
    print("Searching for %s sequence: %s" % ("double" if is_double else "float", pattern_vals))
    
    blocks = fm.getBlocks()
    for block in blocks:
        if not block.isInitialized(): continue
        addr = block.getStart()
        while addr < block.getEnd():
            try:
                # Read sequence
                match = True
                for i, target in enumerate(pattern_vals):
                    val = getDouble(addr.add(i*size)) if is_double else getFloat(addr.add(i*size))
                    if abs(val - target) > 0.00001:
                        match = False
                        break
                
                if match:
                    print("MATCH FOUND at %s (%s)" % (addr, "double" if is_double else "float"))
                    # Dump first 8 values
                    dump = []
                    for i in range(8):
                        v = getDouble(addr.add(i*size)) if is_double else getFloat(addr.add(i*size))
                        dump.append(v)
                    print("  Data: %s" % dump)
            except:
                pass
            addr = addr.add(size)

if __name__ == "__main__":
    # ATRAC3 Sine Window (256 points)
    # sin((i+0.5)*pi/512) for MDCT 256->512? No, ATRAC3 uses 256-point window for 512-point MDCT or something?
    # Standard: sin((i + 0.5) * PI / 2N) where N is transform size. 
    # ATRAC3 N=256, so window is 512 points? Or 256?
    
    # Let's check common ATRAC3 window starts
    # If N=256: sin((0.5)*pi/512) = 0.00306796
    # If N=128: sin((0.5)*pi/256) = 0.00613588
    
    targets_256 = [0.00613588, 0.01840623, 0.03067336]
    targets_512 = [0.00306796, 0.00920371, 0.01533816]
    
    print("--- Searching for N=128 (256-point) window ---")
    find_sequence(targets_256, False)
    find_sequence(targets_256, True)
    
    print("--- Searching for N=256 (512-point) window ---")
    find_sequence(targets_512, False)
    find_sequence(targets_512, True)
    
    # Also search for 1/sqrt(2)
    print("--- Searching for 1/sqrt(2) ---")
    find_sequence([0.70710678], False)
    find_sequence([0.70710678], True)
