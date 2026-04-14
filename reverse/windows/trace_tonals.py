"""
trace_tonals.py
Diagnostic script to verify if tonal candidate finder (0x3f110) is ever returning >0.
"""
import frida
import time
import os

AT3TOOL = r"C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\windows\at3tool.exe"
WAV = r"C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\quality\input\chirp_20_20k_5s.wav"

hook_code = r"""
var module_base = Process.mainModule.base;
var RVA_3F110 = 0x3f110;
var hit_count = 0;
var non_zero_count = 0;

Interceptor.attach(module_base.add(RVA_3F110), {
    onLeave: function(retval) {
        hit_count++;
        var val = retval.toInt32();
        if (val > 0) {
            non_zero_count++;
            if (non_zero_count < 10) {
                send({type: 'hit', val: val});
            }
        }
    }
});

Process.setExceptionHandler(function(details) {
    send({type: 'error', msg: details});
});
"""

def run_trace():
    pid = frida.spawn([AT3TOOL, "-e", "-br", "132", WAV, "debug.at3"])
    session = frida.attach(pid)
    
    script = session.create_script(hook_code)
    
    def on_message(message, data):
        if message['type'] == 'send':
            print(f"  [Frida] {message['payload']}")
            
    script.on('message', on_message)
    script.load()
    frida.resume(pid)
    
    while True:
        try:
            os.kill(pid, 0)
            time.sleep(1)
        except OSError:
            break
            
    print("\nTrace finished.")

if __name__ == "__main__":
    run_trace()
