import frida, time, os

AT3 = r"C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\windows\at3tool.exe"
WAV = r"C:\Users\Igland\Antigravity\Ghidra\atracdenc\YOUtopia_source.wav"

def test_br(br):
    print(f"\nTesting Bitrate: {br} kbps")
    pid = frida.spawn([AT3, "-e", "-br", br, WAV, "test.at3"])
    session = frida.attach(pid)
    
    script_source = r"""
    var base = Process.mainModule.base;
    Interceptor.attach(base.add(0x36d40), { onEnter: function() { send("HIT 36d40"); } });
    Interceptor.attach(base.add(0x3d1f0), { onEnter: function() { send("HIT 3d1f0"); } });
    """
    
    script = session.create_script(script_source)
    def on_message(message, data):
        if message['type'] == 'send':
            print(f"  [HIT] {message['payload']}")
    script.on('message', on_message)
    script.load()
    frida.resume(pid)
    
    time.sleep(2)
    frida.kill(pid)

if __name__ == "__main__":
    for br in ["66", "105", "132"]:
        test_br(br)
