from ghidra.app.decompiler import DecompInterface
from ghidra.util.task import ConsoleTaskMonitor
import os

# Keywords to look for in decompiled code
KEYWORDS = ["tonal", "residual", "budget", "complexity", "stereo", "gain", "BFU", "quant", "frame", "allocation"]
# Simpler output path
OUTPUT_FILE = r"C:\Users\Igland\at3_decompiled_logic.c"

def run():
    print("DUMP_SCRIPT: Starting extraction...")
    program = currentProgram
    print("DUMP_SCRIPT: Analyzing program: " + program.getName())
    
    decomp_interface = DecompInterface()
    decomp_interface.openProgram(program)
    
    match_count = 0
    try:
        with open(OUTPUT_FILE, "w") as f:
            f.write("/* AT3 LOGIC DUMP */\n")
            functions = program.getFunctionManager().getFunctions(True)
            for func in functions:
                monitor = ConsoleTaskMonitor()
                results = decomp_interface.decompileFunction(func, 0, monitor)
                if results and results.decompileCompleted():
                    df = results.getDecompiledFunction()
                    if df:
                        decompiled_code = df.getC()
                        if any(kw.lower() in decompiled_code.lower() for kw in KEYWORDS):
                            print("DUMP_SCRIPT: Match found in " + func.getName())
                            f.write(f"/* FUNCTION: {func.getName()} at {func.getEntryPoint()} */\n")
                            f.write(decompiled_code)
                            f.write("\n\n")
                            match_count += 1
        print("DUMP_SCRIPT: Finished. Total matches: " + str(match_count))
    except Exception as e:
        print("DUMP_SCRIPT: ERROR - " + str(e))

if __name__ == "__main__":
    run()
