import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;

public class DumpAt3Logic extends GhidraScript {

    private static final String[] KEYWORDS = {
        "tonal", "residual", "budget", "complexity", "stereo", "gain", "BFU", "quant", "frame", "allocation"
    };
    private static final String OUTPUT_PATH = "C:\\Users\\Igland\\at3_decompiled_logic.c";

    @Override
    public void run() throws Exception {
        println("DUMP_SCRIPT: Starting Java extraction...");
        
        DecompInterface decompInterface = new DecompInterface();
        decompInterface.openProgram(currentProgram);
        
        int matchCount = 0;
        try (PrintWriter writer = new PrintWriter(new FileWriter(new File(OUTPUT_PATH)))) {
            writer.println("/* AT3 LOGIC DUMP (JAVA) */");
            
            FunctionIterator functions = currentProgram.getFunctionManager().getFunctions(true);
            while (functions.hasNext() && !monitor.isCancelled()) {
                Function func = functions.next();
                DecompileResults results = decompInterface.decompileFunction(func, 0, monitor);
                
                if (results != null && results.decompileCompleted()) {
                    String decompiledCode = results.getDecompiledFunction().getC();
                    if (containsKeywords(decompiledCode)) {
                        println("DUMP_SCRIPT: Match found in " + func.getName());
                        writer.println("/* FUNCTION: " + func.getName() + " at " + func.getEntryPoint() + " */");
                        writer.println(decompiledCode);
                        writer.println("\n\n");
                        matchCount++;
                    }
                }
            }
            println("DUMP_SCRIPT: Finished. Total matches: " + matchCount);
        } catch (Exception e) {
            println("DUMP_SCRIPT: ERROR - " + e.getMessage());
        } finally {
            decompInterface.dispose();
        }
    }

    private boolean containsKeywords(String code) {
        String lowerCode = code.toLowerCase();
        for (String kw : KEYWORDS) {
            if (lowerCode.contains(kw.toLowerCase())) {
                return true;
            }
        }
        return false;
    }
}
