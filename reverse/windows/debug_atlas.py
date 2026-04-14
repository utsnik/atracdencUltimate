import frida
import sys
import time

def on_message(message, data):
    if message['type'] == 'send':
        print(message['payload'])

# at3tool.exe path
at3tool = r"C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\windows\at3tool.exe"
wav_file = r"C:\Users\Igland\Antigravity\Ghidra\atracdenc\YOUtopia_source.wav"
out_at3 = r"C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\windows\out.at3"

pid = frida.spawn([at3tool, "-e", "-br", "132", wav_file, out_at3])
session = frida.attach(pid)

script_code = """
send("LISTING MODULES:");
Process.enumerateModules().forEach(function(m) {
    send(m.name + " at " + m.base + " (size: " + m.size + ")");
});

send("TRACING INVOCATIONS ON MAIN MODULE:");
var main = Process.mainModule;
// Hook the entry point to see if it triggers
Interceptor.attach(main.base.add(Process.mainModule.entryPoint), function() {
    send("MAIN ENTRY POINT HIT!");
});

// Hook 0x37a0 (the match we found earlier)
Interceptor.attach(main.base.add(0x37a0), function() {
    send("RVA 0x37a0 HIT!");
});
"""

script = session.create_script(script_code)
script.on('message', on_message)
script.load()

frida.resume(pid)
time.sleep(5)
session.detach()
