import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;

public class DumpTables extends GhidraScript {
    @Override
    public void run() throws Exception {
        // Range where we saw DAT_0048...
        long start = 0x48b000;
        long end = 0x48d000;
        Address startAddr = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(start);
        
        println("Dumping tables from " + startAddr);
        for (long i = start; i < end; i += 16) {
            Address addr = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(i);
            byte[] bytes = new byte[16];
            currentProgram.getMemory().getBytes(addr, bytes);
            StringBuilder sb = new StringBuilder();
            sb.append(String.format("%08X: ", i));
            for (byte b : bytes) {
                sb.append(String.format("%02X ", b));
            }
            println(sb.toString());
        }
    }
}
