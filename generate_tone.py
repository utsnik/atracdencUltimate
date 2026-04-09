import wave
import numpy as np

def generate_tone():
    # 1000 Hz Sine Wave, 44100 Hz Sample Rate, 16-bit PCM, Stereo
    sample_rate = 44100
    duration = 5.0
    frequency = 1000.0
    amplitude = 0.5 # 50% amplitude to avoid clipping and allow clean MDCT spectral peaks

    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    tone = (amplitude * 32767 * np.sin(2 * np.pi * frequency * t)).astype(np.int16)
    
    # Stereo
    stereo_tone = np.stack((tone, tone), axis=-1)

    with wave.open("tone.wav", "wb") as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        f.writeframes(stereo_tone.tobytes())
    
    print("Generated tone.wav (1000Hz, 5s)")

if __name__ == "__main__":
    generate_tone()
