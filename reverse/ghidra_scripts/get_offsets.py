from ghidra.program.model.listing import FunctionManager

funcs = ["FUN_00437b40", "FUN_00438e60", "FUN_00439820", "FUN_0043c5d0", "FUN_00437490"]
fm = currentProgram.getFunctionManager()
base = currentProgram.getImageBase().getOffset()

for name in funcs:
    found = False
    for f in fm.getFunctions(True):
        if f.getName() == name:
            addr = f.getEntryPoint().getOffset()
            print("%s VA: 0x%x ImageBase: 0x%x" % (name, addr, base))
            found = True
            break
    if not found:
        print("%s NOT FOUND" % name)
