# Ghidra Jython script: dump analysis artifacts to JSON for AI ingestion
# Usage (headless): -postScript At3Dump.py <output_dir>

import os
import json

from ghidra.program.model.data import StringDataInstance
from ghidra.program.model.symbol import SymbolType
from ghidra.app.decompiler import DecompInterface


def write_json(out_dir, filename, obj):
    path = os.path.join(out_dir, filename)
    f = open(path, "w")
    try:
        json.dump(obj, f, indent=2)
    finally:
        f.close()


def dump_overview(program, out_dir):
    info = {
        "name": program.getName(),
        "language": str(program.getLanguageID()),
        "compiler": str(program.getCompilerSpec().getCompilerSpecID()),
        "image_base": str(program.getImageBase()),
        "entry_point": str(program.getEntryPoint()),
    }
    write_json(out_dir, "overview.json", info)


def dump_strings(program, out_dir):
    listing = program.getListing()
    strings = []
    max_strings = 5000
    it = listing.getDefinedData(True)
    while it.hasNext() and len(strings) < max_strings:
        data = it.next()
        try:
            sdi = StringDataInstance(data)
            value = sdi.getStringValue()
            if value is None:
                continue
            strings.append({
                "address": str(data.getAddress()),
                "value": value,
                "length": sdi.getStringLength(),
            })
        except Exception:
            continue
    write_json(out_dir, "strings.json", strings)


def dump_functions(program, out_dir):
    fm = program.getFunctionManager()
    funcs = []
    it = fm.getFunctions(True)
    while it.hasNext():
        f = it.next()
        body = f.getBody()
        funcs.append({
            "name": f.getName(),
            "entry": str(f.getEntryPoint()),
            "signature": str(f.getSignature()),
            "param_count": f.getParameterCount(),
            "return_type": str(f.getReturnType()),
            "is_external": f.isExternal(),
            "is_thunk": f.isThunk(),
            "size": body.getNumAddresses() if body is not None else 0,
        })
    write_json(out_dir, "functions.json", funcs)


def dump_imports_exports(program, out_dir):
    symtab = program.getSymbolTable()
    imports = []
    exports = []

    # Imports: external symbols
    ext_it = symtab.getExternalSymbols()
    while ext_it.hasNext():
        sym = ext_it.next()
        imports.append({
            "name": sym.getName(),
            "address": str(sym.getAddress()),
            "source": str(sym.getSource()),
            "library": sym.getLibraryName() if hasattr(sym, "getLibraryName") else None,
        })

    # Exports: primary, non-external functions
    sym_it = symtab.getAllSymbols(True)
    while sym_it.hasNext():
        sym = sym_it.next()
        if sym.getSymbolType() != SymbolType.FUNCTION:
            continue
        if sym.isExternal():
            continue
        if not sym.isPrimary():
            continue
        exports.append({
            "name": sym.getName(),
            "address": str(sym.getAddress()),
            "source": str(sym.getSource()),
        })

    write_json(out_dir, "imports.json", imports)
    write_json(out_dir, "exports.json", exports)


def dump_decompilation(program, out_dir):
    fm = program.getFunctionManager()
    funcs = []
    it = fm.getFunctions(True)
    while it.hasNext():
        f = it.next()
        if f.isExternal():
            continue
        body = f.getBody()
        size = body.getNumAddresses() if body is not None else 0
        funcs.append((size, f))

    funcs.sort(key=lambda x: x[0], reverse=True)
    top_n = 30
    target = [f for (_, f) in funcs[:top_n]]

    if len(target) == 0:
        write_json(out_dir, "decompilation.json", [])
        return

    iface = DecompInterface()
    iface.openProgram(program)
    iface.setTimeout(30)

    out = []
    for f in target:
        res = iface.decompileFunction(f, 30, monitor)
        if res is None or not res.decompileCompleted():
            code = None
        else:
            code = res.getDecompiledFunction().getC()
        out.append({
            "name": f.getName(),
            "entry": str(f.getEntryPoint()),
            "size": f.getBody().getNumAddresses() if f.getBody() is not None else 0,
            "c": code,
        })

    write_json(out_dir, "decompilation.json", out)


args = getScriptArgs()
if args is None or len(args) < 1:
    printerr("At3Dump.py requires output_dir argument")
else:
    out_dir = args[0]
    if not os.path.isabs(out_dir):
        out_dir = os.path.abspath(out_dir)
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    if currentProgram is None:
        printerr("No program loaded")
    else:
        dump_overview(currentProgram, out_dir)
        dump_strings(currentProgram, out_dir)
        dump_functions(currentProgram, out_dir)
        dump_imports_exports(currentProgram, out_dir)
        dump_decompilation(currentProgram, out_dir)
