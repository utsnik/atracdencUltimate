import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.address.Address;

public class GetOffsets extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] funcs = {"FUN_00437b40", "FUN_00438e60", "FUN_00439820", "FUN_0043c5d0", "FUN_00437490"};
        for (String name : funcs) {
            Function f = getFunction(name);
            if (f != null) {
                Address addr = f.getEntryPoint();
                long offset = addr.getOffset() - currentProgram.getImageBase().getOffset();
                // For PE files, we need to map VA to File Offset
                // But for now, let's just print the VA and ImageBase
                println(name + " VA: 0x" + Long.toHexString(addr.getOffset()) + " ImageBase: 0x" + Long.toHexString(currentProgram.getImageBase().getOffset()));
            } else {
                println(name + " NOT FOUND");
            }
        }
    }

    private Function getFunction(String name) {
        for (Function f : currentProgram.getFunctionManager().getFunctions(true)) {
            if (f.getName().equals(name)) return f;
        }
        return null;
    }
}
