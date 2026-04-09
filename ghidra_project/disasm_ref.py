# Ghidra Python script to disassemble refs to a specific address
from ghidra.program.model.address import Address
from ghidra.program.model.listing import Instruction

def run():
    # Sony MDCT window table address
    table_addr_val = 0x452340
    table_addr = currentProgram.getAddressFactory().getAddress(hex(table_addr_val))
    
    print("Searching for references to {}".format(table_addr))
    
    refs = getReferencesTo(table_addr)
    for ref in refs:
        ref_addr = ref.getFromAddress()
        print("Reference found at: {}".format(ref_addr))
        
        instr = getInstructionAt(ref_addr)
        if instr:
            print("Instruction: {}".format(instr))
            # Print 30 instructions to capture the loop
            curr = instr.getNext()
            for i in range(30):
                if not curr:
                    break
                print("  {}: {}".format(curr.getAddress(), curr))
                curr = curr.getNext()

if __name__ == "__main__":
    run()
