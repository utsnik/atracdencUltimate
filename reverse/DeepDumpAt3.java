import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.listing.Function;
import ghidra.program.model.address.Address;
import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.HashSet;
import java.util.Set;
import java.util.Stack;

public class DeepDumpAt3 extends GhidraScript {

    private static final String OUTPUT_PATH = "C:\\Users\\Igland\\at3_deep_logic.c";
    private static final String START_FUNC = "FUN_004049f0"; // atrac_encode

    @Override
    public void run() throws Exception {
        println("DEEP_DUMP: Starting...");
        
        DecompInterface decompInterface = new DecompInterface();
        decompInterface.openProgram(currentProgram);
        
        Set<Function> processed = new HashSet<>();
        Stack<Function> toProcess = new Stack<>();
        
        Function startFunc = null;
        for (Function f : currentProgram.getFunctionManager().getFunctions(true)) {
            if (f.getName().equals(START_FUNC)) {
                startFunc = f;
                break;
            }
        }
        
        if (startFunc == null) {
            println("DEEP_DUMP: Could not find " + START_FUNC);
            return;
        }
        
        toProcess.push(startFunc);
        
        try (PrintWriter writer = new PrintWriter(new FileWriter(new File(OUTPUT_PATH)))) {
            writer.println("/* DEEP AT3 ENCODE DUMP */");
            
            while (!toProcess.isEmpty() && processed.size() < 100) { // Limit to 100 functions to avoid giant files
                Function func = toProcess.pop();
                if (processed.contains(func)) continue;
                processed.add(func);
                
                DecompileResults results = decompInterface.decompileFunction(func, 0, monitor);
                if (results != null && results.decompileCompleted()) {
                    String code = results.getDecompiledFunction().getC();
                    writer.println("/* FUNCTION: " + func.getName() + " at " + func.getEntryPoint() + " */");
                    writer.println(code);
                    writer.println("\n\n");
                    
                    // Add called functions to queue
                    Set<Function> called = func.getCalledFunctions(monitor);
                    for (Function cf : called) {
                        if (!processed.contains(cf)) {
                            toProcess.push(cf);
                        }
                    }
                }
            }
        } finally {
            decompInterface.dispose();
        }
        println("DEEP_DUMP: Finished. Processed " + processed.size() + " functions.");
    }
}
