import pyaudio
import numpy as np
from audio_filter import filter_audio

# Audio stream configuration
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 8000


def audio_callback(in_data, frame_count, time_info, status):
    """Real-time audio callback for both input and output"""
    try:
        # Convert input bytes to numpy array
        audio_data = np.frombuffer(in_data, dtype=np.int16)
        
        # Apply noise reduction filter
        # filtered_audio = filter_audio(audio_data, noise_threshold=NOISE_THRESHOLD)
        
        # Convert back to bytes for output
        out_data = audio_data.tobytes()
        
        return (out_data, pyaudio.paContinue)
    except Exception as e:
        print(f"Error in audio callback: {e}")
        return (in_data, pyaudio.paContinue)

def main():
    # Initialize PyAudio
    p = pyaudio.PyAudio()
    
    try:
        # List available input devices
        print("\nAvailable Input Devices:")
        for i in range(p.get_device_count()):
            dev_info = p.get_device_info_by_index(i)
            if dev_info.get('maxInputChannels') > 0:  # Only show input devices
                print(f"Device {i}: {dev_info.get('name')}")
        
        # Get user's device selection
        device_index = int(input("\nSelect input device number: "))
        
        # Open bidirectional stream
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            output=True,
            input_device_index=device_index,
            frames_per_buffer=CHUNK,
            stream_callback=audio_callback
        )
        
        print("\nStreaming audio... Press Ctrl+C to stop")
        stream.start_stream()
        
        # Keep the stream running
        while stream.is_active():
            pass
            
    except KeyboardInterrupt:
        print("\nStopping stream...")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        if 'stream' in locals():
            stream.stop_stream()
            stream.close()
        p.terminate()
        print("Audio streaming stopped")

if __name__ == "__main__":
    main()