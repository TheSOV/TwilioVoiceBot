import os
import wave
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
import audioop
import glob

def list_audio_files(directory='recordings', extensions=('.wav', '.ul')):
    """
    List all audio files in the specified directory.
    
    Args:
        directory (str): Directory to search
        extensions (tuple): File extensions to include
    
    Returns:
        dict: Dictionary of files grouped by extension
    """
    if not os.path.exists(directory):
        raise FileNotFoundError(f"Directory {directory} does not exist")
    
    files = {}
    for ext in extensions:
        files[ext] = glob.glob(os.path.join(directory, f'*{ext}'))
        files[ext].sort(key=os.path.getmtime, reverse=True)  # Sort by newest first
    
    return files

def load_audio_file(file_path):
    """
    Load audio file (WAV or ULAW).
    
    Args:
        file_path (str): Path to audio file
    
    Returns:
        tuple: (audio_data, sample_rate)
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.wav':
        with wave.open(file_path, 'rb') as wav_file:
            # Get audio properties
            sample_rate = wav_file.getframerate()
            n_frames = wav_file.getnframes()
            
            # Read audio data
            audio_data = wav_file.readframes(n_frames)
            audio_np = np.frombuffer(audio_data, dtype=np.int16)
            
            return audio_np, sample_rate
            
    elif ext == '.ul':
        # Read raw ulaw data
        with open(file_path, 'rb') as ul_file:
            ulaw_data = ul_file.read()
            
        # Convert to PCM
        pcm_data = audioop.ulaw2lin(ulaw_data, 2)  # 2 bytes per sample
        audio_np = np.frombuffer(pcm_data, dtype=np.int16)
        
        return audio_np, 8000  # g711 is always 8kHz
    
    else:
        raise ValueError(f"Unsupported file format: {ext}")

def analyze_audio(audio_data, sample_rate):
    """
    Analyze audio data.
    
    Args:
        audio_data (np.ndarray): Audio data
        sample_rate (int): Sample rate in Hz
    """
    duration = len(audio_data) / sample_rate
    
    # Create time axis
    time = np.linspace(0, duration, len(audio_data))
    
    # Compute spectrogram
    f, t, Sxx = signal.spectrogram(audio_data, fs=sample_rate, nperseg=1024)
    
    # Compute statistics
    rms = np.sqrt(np.mean(np.square(audio_data)))
    peak = np.max(np.abs(audio_data))
    zero_crossings = np.sum(np.diff(np.signbit(audio_data)))
    
    # Plot analysis
    plt.figure(figsize=(15, 10))
    plt.suptitle('Audio Analysis', fontsize=16)
    
    # Waveform
    plt.subplot(2, 1, 1)
    plt.plot(time, audio_data)
    plt.title('Waveform')
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude')
    plt.grid(True)
    
    # Spectrogram
    plt.subplot(2, 1, 2)
    plt.pcolormesh(t, f, 10 * np.log10(Sxx + 1e-10), shading='gouraud')
    plt.title('Spectrogram')
    plt.ylabel('Frequency [Hz]')
    plt.xlabel('Time [sec]')
    plt.colorbar(label='Intensity [dB]')
    
    plt.tight_layout()
    
    # Print statistics
    print("\nAudio Statistics:")
    print(f"Duration: {duration:.2f} seconds")
    print(f"Sample Rate: {sample_rate} Hz")
    print(f"RMS Value: {rms:.2f}")
    print(f"Peak Value: {peak}")
    print(f"Zero Crossings: {zero_crossings}")
    
    plt.show()

def main():
    try:
        # List available audio files
        files = list_audio_files()
        
        # Display available files
        print("\nAvailable audio files:")
        for ext, file_list in files.items():
            if file_list:
                print(f"\n{ext.upper()} files:")
                for i, file in enumerate(file_list, 1):
                    filename = os.path.basename(file)
                    mtime = os.path.getmtime(file)
                    size = os.path.getsize(file)
                    print(f"{i}. {filename} ({size/1024:.1f}KB, modified: {mtime})")
        
        # Get user selection
        while True:
            try:
                ext_choice = input("\nSelect file type (wav/ul): ").lower()
                if ext_choice not in ['wav', 'ul']:
                    print("Invalid file type. Please enter 'wav' or 'ul'")
                    continue
                
                ext = f'.{ext_choice}'
                if not files[ext]:
                    print(f"No {ext} files found")
                    continue
                
                file_num = int(input(f"Enter file number (1-{len(files[ext])}): "))
                if 1 <= file_num <= len(files[ext]):
                    selected_file = files[ext][file_num - 1]
                    break
                else:
                    print("Invalid file number")
            except ValueError:
                print("Please enter a valid number")
        
        # Load and analyze selected file
        print(f"\nAnalyzing: {os.path.basename(selected_file)}")
        audio_data, sample_rate = load_audio_file(selected_file)
        analyze_audio(audio_data, sample_rate)
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()