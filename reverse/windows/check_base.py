import frida
import sys

at3tool = r"C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\windows\at3tool.exe"
pid = frida.spawn([at3tool])
session = frida.attach(pid)

script_code = """
var main = Process.mainModule;
console.log("Base: " + main.base);
console.log("Size: " + main.size);
console.log("Path: " + main.path);

var imports = main.enumerateImports();
console.log("Imports count: " + imports.length);

var exports = main.enumerateExports();
console.log("Exports count: " + exports.length);
"""

script = session.create_script(script_code)
script.on('message', lambda msg, data: print(msg))
script.load()
frida.resume(pid)
session.detach()
