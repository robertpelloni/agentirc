import wave
import struct
import math

def generate_beep(filename="public/sounds/beep.wav", duration_ms=100, freq=800):
    sample_rate = 44100
    num_samples = int(sample_rate * (duration_ms / 1000.0))

    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2) # 16-bit
        wav_file.setframerate(sample_rate)

        for i in range(num_samples):
            # Generate a simple sine wave
            value = int(32767.0 * math.sin(2.0 * math.pi * freq * i / sample_rate))
            data = struct.pack('<h', value)
            wav_file.writeframesraw(data)

generate_beep()
print("Generated beep.wav")
