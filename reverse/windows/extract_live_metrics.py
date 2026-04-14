import frida
import sys
import threading
import time

out_csv = open("per_frame_metrics.csv", "w")
out_csv.write("frame_idx,complexity,target_bits,differential_gain_indices\n")

def on_message(message, data):
    if message['type'] == 'send':
        payload = message['payload']
        # Payload comes as "FRAME;idx;complexity;loc,lvl|loc,lvl"
        parts = payload.split(";")
        if parts[0] == "FRAME":
            out_csv.write(f"{parts[1]},{parts[2]},{parts[3]},{parts[4]}\n")
            out_csv.flush()
    elif message['type'] == 'error':
        print("[!] ERROR:", message)

# Standard entry parameters
pid = frida.spawn(["at3tool.exe", "-e", "-br", "132", "C:\\Users\\Igland\\Antigravity\\Ghidra\\atracdenc\\YOUtopia_source.wav", "C:\\Users\\Igland\\Antigravity\\Ghidra\\ghidra\\reverse\\windows\\out.at3"])
session = frida.attach(pid)

script_code = """
var baseAddr = Process.enumerateModules()[0].base;
var current_frame = 0;
var current_complexity = 0;
var diff_gains = [];

// Hook Bit Allocator Return (captures complexity)
Interceptor.attach(baseAddr.add(0x385ab), function (args) {
    try {
        var esp = this.context.esp;
        current_complexity = esp.add(0x510).readU32();
        
        var d_str = "";
        for(var i=0; i<diff_gains.length; i++) {
            d_str += diff_gains[i] + "|";
        }
        
        send("FRAME;" + current_frame + ";" + current_complexity + ";0;" + d_str);
        
        // Reset for next frame
        current_frame++;
        diff_gains = [];
    } catch (e) {
        send("ERR: " + e.message);
    }
});

// Hook Gain Serialization (Differential Indices)
Interceptor.attach(baseAddr.add(0x37670), function (args) {
    try {
        var val = args[0].toInt32();
        var num_bits = args[1].toInt32();
        
        // Differential gains are serialized as 9-bit chunks!
        if (num_bits === 9) {
            var location = val & 0x1F;
            var level = (val >> 5) & 0xF;
            diff_gains.push(location + "-" + level);
        }
    } catch (e) {
        send("ERR: " + e.message);
    }
});
"""

script = session.create_script(script_code)
script.on('message', on_message)
script.load()

print("[*] Harvesting Live Runtime Metrics via Frida...")
frida.resume(pid)

event = threading.Event()
session.on('detached', lambda reason: event.set())

# Wait maximum 10 seconds for completion, then exit
event.wait(10)
time.sleep(1) # Flush message queue

out_csv.close()
print("[*] Extraction Complete. Saved to per_frame_metrics.csv")
