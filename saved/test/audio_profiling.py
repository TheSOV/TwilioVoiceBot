import os
import numpy as np
import matplotlib.pyplot as plt
import wave
import glob

def find_latest_recording():
    """Find the most recent WAV file in the recordings directory."""
    recordings_dir = 'recordings'
    if not os.path.exists(recordings_dir):
        raise FileNotFoundError("No recordings directory found")
    
    # Get all WAV files and sort by modification time
    wav_files = glob.glob(os.path.join(recordings_dir, '*.wav'))
    if not wav_files:
        raise FileNotFoundError("No WAV files found in recordings directory")
    
    return max(wav_files, key=os.path.getmtime)

def read_wav_file(filename):
    """Read WAV file and return audio data and parameters."""
    with wave.open(filename, 'rb') as wav_file:
        # Extract Raw Audio from Wav File
        signal = wav_file.readframes(-1)
        signal = np.frombuffer(signal, dtype=np.int16)
        
        # Get file parameters
        n_channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        framerate = wav_file.getframerate()
        n_frames = wav_file.getnframes()
        
        return signal, n_channels, sample_width, framerate, n_frames

def plot_audio_characteristics(signal, framerate):
    """Create multiple plots to visualize audio characteristics."""
    # Create a figure with multiple subplots
    plt.figure(figsize=(15, 10))
    plt.suptitle('Audio Recording Analysis', fontsize=16)

    # 1. Time Domain Signal
    plt.subplot(2, 2, 1)
    time = np.linspace(0, len(signal) / framerate, num=len(signal))
    plt.plot(time, signal)
    plt.title('Time Domain Signal')
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude')

    # 2. Amplitude Histogram
    plt.subplot(2, 2, 2)
    plt.hist(signal, bins=50, density=True)
    plt.title('Amplitude Distribution')
    plt.xlabel('Amplitude')
    plt.ylabel('Frequency')

    # 3. Power Spectrum (FFT)
    plt.subplot(2, 2, 3)
    fft_signal = np.fft.fft(signal)
    frequencies = np.fft.fftfreq(len(signal), 1/framerate)
    plt.plot(frequencies[:len(frequencies)//2], np.abs(fft_signal)[:len(frequencies)//2])
    plt.title('Power Spectrum')
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Magnitude')
    plt.xlim(0, framerate/2)  # Nyquist frequency

    # 4. Spectrogram
    plt.subplot(2, 2, 4)
    plt.specgram(signal, Fs=framerate, cmap='viridis')
    plt.title('Spectrogram')
    plt.xlabel('Time (s)')
    plt.ylabel('Frequency (Hz)')

    plt.tight_layout()
    plt.show()

def analyze_recording():
    """Main function to analyze the latest recording."""
    try:
        # Find and read the latest recording
        latest_recording = find_latest_recording()
        print(f"Analyzing recording: {latest_recording}")
        
        # Read the WAV file
        signal, n_channels, sample_width, framerate, n_frames = read_wav_file(latest_recording)
        
        # Print basic audio information
        print(f"Channels: {n_channels}")
        print(f"Sample Width: {sample_width} bytes")
        print(f"Frame Rate: {framerate} Hz")
        print(f"Total Frames: {n_frames}")
        print(f"Duration: {n_frames/framerate:.2f} seconds")
        
        # Compute and print additional statistics
        print(f"Signal Min: {np.min(signal)}")
        print(f"Signal Max: {np.max(signal)}")
        print(f"Signal Mean: {np.mean(signal)}")
        print(f"Signal Standard Deviation: {np.std(signal)}")
        
        # Plot audio characteristics
        plot_audio_characteristics(signal, framerate)
    
    except Exception as e:
        print(f"Error analyzing recording: {e}")

if __name__ == "__main__":
    analyze_recording()