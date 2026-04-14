
import wave
import numpy as np
import sys

def analyze(filename):
    try:
        with wave.open(filename, 'rb') as w:
            frames = w.readframes(w.getnframes())
            data = np.frombuffer(frames, dtype=np.int16)
            
            # Remove silence
            rms = np.sqrt(np.mean(data.astype(np.float32)**2))
            peak = np.max(np.abs(data))
            
            print(f"File: {filename}")
            print(f"RMS Volume: {rms:.2f}")
            print(f"Peak Amplitude: {peak}")
            
            if peak > 100:
                print("STATUS: AUDIO DETECTED")
            else:
                print("STATUS: SILENCE DETECTED")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze(sys.argv[1])
