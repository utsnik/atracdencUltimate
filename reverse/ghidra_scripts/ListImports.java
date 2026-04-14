import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Symbol;
import java.util.Iterator;

public class ListImports extends GhidraScript {
    @Override
    public void run() throws Exception {
        println("External Functions (Imports):");
        for (Function f : currentProgram.getFunctionManager().getExternalFunctions()) {
            println(f.getName() + " at " + f.getEntryPoint());
        }
    }
}
