import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;

class DisasmRef extends GhidraScript {
    @Override
    public void run() throws Exception {
        // Offset found was 0x178FD. 
        // Image base is likely 0x400000. 
        // PE headers usually 0x400... let's try to find it by file offset logic if possible.
        // Or just use the address we searched: 0x452340.
        
        Address tableAddr = toAddr(0x452340);
        println("Searching for references to " + tableAddr);
        
        for (Address ref : getReferencesTo(tableAddr)) {
            println("Reference found at: " + ref);
            Instruction instr = getInstructionAt(ref);
            if (instr != null) {
                println("Instruction: " + instr.toString());
                // Print a few more instructions after
                Instruction next = instr.getNext();
                for (int i = 0; i < 20 && next != null; i++) {
                    println("  " + next.getAddress() + ": " + next.toString());
                    next = next.getNext();
                }
            }
        }
    }
}
