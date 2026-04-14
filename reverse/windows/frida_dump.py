import frida
import sys

def on_message(message, data):
    if message['type'] == 'send':
        print(message['payload'])
    else:
        print(f"[{message['type']}] {message}")

# Spawn the process
pid = frida.spawn(["at3tool.exe", "-e", "-br", "132", "C:\\Users\\Igland\\Antigravity\\Ghidra\\atracdenc\\YOUtopia_source.wav", "C:\\Users\\Igland\\Antigravity\\Ghidra\\ghidra\\reverse\\windows\\out.at3"])
session = frida.attach(pid)

script_code = """
var baseAddr = Process.enumerateModules()[0].base;

// FUN_00437b40 - Allocator
var allocAddr = baseAddr.add(0x37b40);
// Address just before return in allocator (ADD ESP, 0x520)
var allocEndAddr = baseAddr.add(0x385ab);

var current_frame = 0;

Interceptor.attach(allocEndAddr, function (args) {
    var esp = this.context.esp;
    var iStack_510 = esp.add(0x510).readU32();
    send("FRAME " + current_frame + " COMPLEXITY: " + iStack_510);
    current_frame++;
});

// FUN_00437670 - Bitstream write bits (val, num_bits, ptr, bit_offset)
var writeBitsAddr = baseAddr.add(0x37670);
Interceptor.attach(writeBitsAddr, function (args) {
    var val = args[0].toInt32();
    var num_bits = args[1].toInt32();
    // send("WRITE_BITS val=" + val + " bits=" + num_bits);
});

// FUN_0043ebd0 - Gain Table Decoder
var gainDecodeAddr = baseAddr.add(0x3ebd0);
Interceptor.attach(gainDecodeAddr, function (args) {
    var p1 = args[0].toInt32();
    var p2 = args[1].toInt32();
    send("GAIN_DECODE p1=" + p1 + " p2=" + p2);
});
"""

script = session.create_script(script_code)
script.on('message', on_message)
script.load()

print("[*] Running at3tool.exe...")
frida.resume(pid)

# Wait for process to exit
import threading
event = threading.Event()
session.on('detached', lambda reason: event.set())
event.wait()
print("[*] Process exited.")
