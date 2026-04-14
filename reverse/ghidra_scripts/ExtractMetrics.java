import ghidra.app.emulator.EmulatorHelper;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Instruction;
import java.util.Map;

public class ExtractMetrics extends GhidraScript {
    @Override
    public void run() throws Exception {
        // Use the RVAs from the checklist
        long base = currentProgram.getImageBase().getOffset();
        Address frameEntry = addr(base + 0x36d40);
        Address allocEntry = addr(base + 0x37b40);
        Address tonalEntry = addr(base + 0x38e60);
        
        println("Probing RVAs:");
        println("  Frame: " + frameEntry);
        println("  Alloc: " + allocEntry);
        println("  Tonal: " + tonalEntry);

        // Since I can't effectively run the full binary with dependencies in headless,
        // I will instead use the script to FIND the branch signatures the user requested.
        
        findSignatures();
    }

    private void findSignatures() {
        // 1. Find the JS mode gate near 0x37490 (FUN_00437490)
        long base = currentProgram.getImageBase().getOffset();
        Address writeStart = addr(base + 0x37490);
        Instruction inst = getInstructionAt(writeStart);
        println("\nSearching for JS Matrix signatures at " + writeStart);
        for (int i = 0; i < 500; i++) {
            if (inst == null) break;
            String dis = inst.toString();
            // Look for the 2-bit matrix selector index math
            if (dis.contains("SHL") && dis.contains("0x2")) {
                println("POTENTIAL Matrix Math at " + inst.getAddress() + ": " + dis);
            }
            // Look for tight loops (4 iterations)
            if (dis.contains("CMP") && (dis.contains("0x4") || dis.contains("4"))) {
                println("POTENTIAL JS subband loop at " + inst.getAddress() + ": " + dis);
            }
            inst = inst.getNext();
        }
    }

    private Address addr(long offset) {
        return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(offset);
    }
}
