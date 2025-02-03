import os
import glob
import numpy as np
import soundfile as sf
import matplotlib.pyplot as plt

from audio_filter import filter_audio

def list_recordings(directory='recordings'):
    """
    List all WAV files in the specified directory.
    
    Args:
        directory (str): Path to the directory containing recordings
    
    Returns:
        List of full paths to WAV files
    """
    if not os.path.exists(directory):
        raise FileNotFoundError(f"Directory {directory} does not exist")
    
    wav_files = glob.glob(os.path.join(directory, '*.wav'))
    
    if not wav_files:
        raise FileNotFoundError(f"No WAV files found in {directory}")
    
    return sorted(wav_files)

def load_audio(file_path):
    """
    Load audio file.
    
    Args:
        file_path (str): Path to the WAV file
    
    Returns:
        Tuple of (audio_data, sample_rate)
    """
    audio_data, sample_rate = sf.read(file_path)
    
    # Ensure 1D array for mono audio
    if audio_data.ndim > 1:
        audio_data = audio_data.mean(axis=1)
    
    return audio_data, sample_rate

def save_filtered_audio(original_path, filtered_audio, filter_name, output_dir='filtered_recordings'):
    """
    Save filtered audio to a new file.
    
    Args:
        original_path (str): Path of the original audio file
        filtered_audio (np.ndarray): Filtered audio data
        filter_name (str): Name of the filter used
        output_dir (str): Directory to save filtered recordings
    
    Returns:
        Path of the saved filtered audio file
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename
    filename = os.path.basename(original_path)
    base, ext = os.path.splitext(filename)
    filtered_filename = f"{base}_{filter_name}_filtered{ext}"
    filtered_path = os.path.join(output_dir, filtered_filename)
    
    # Save filtered audio
    sf.write(filtered_path, filtered_audio, 44100)  # Using standard 44.1kHz
    return filtered_path

def plot_audio_comparison(original, filtered_dict, sample_rate, title):
    """
    Create a comprehensive plot comparing original and filtered audio.
    
    Args:
        original (np.ndarray): Original audio signal
        filtered_dict (dict): Dictionary of filtered audio signals
        sample_rate (int): Audio sample rate
        title (str): Plot title
    """
    # Determine number of subplots
    num_filters = len(filtered_dict)
    plot_rows = (num_filters + 1) // 2  # Ceiling division
    
    # Create figure
    plt.figure(figsize=(15, 4 * plot_rows))
    plt.suptitle(title, fontsize=16)
    
    # Compute time axis
    def compute_time_axis(signal):
        return np.linspace(0, len(signal) / sample_rate, num=len(signal))
    
    # Original signal plot
    plt.subplot(plot_rows, 2, 1)
    time_original = compute_time_axis(original)
    plt.plot(time_original, original)
    plt.title('Original Signal')
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude')
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Filtered signals plots
    for i, (filter_name, filtered_audio) in enumerate(filtered_dict.items(), start=2):
        plt.subplot(plot_rows, 2, i)
        time_filtered = compute_time_axis(filtered_audio)
        plt.plot(time_filtered, filtered_audio)
        plt.title(f'{filter_name.capitalize()} Filtered Signal')
        plt.xlabel('Time (s)')
        plt.ylabel('Amplitude')
        plt.grid(True, linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.show()

def main():
    """
    Main function to test audio filters.
    """
    try:
        # List available recordings
        recordings = list_recordings()
        
        # Print available recordings
        print("Available recordings:")
        for i, recording in enumerate(recordings, 1):
            print(f"{i}. {os.path.basename(recording)}")
        
        # Select recording
        while True:
            try:
                selection = int(input("Enter the number of the recording to filter: ")) - 1
                
                # Validate index
                if 0 <= selection < len(recordings):
                    selected_recording = recordings[selection]
                    break
                else:
                    print("Invalid selection. Please try again.")
            except ValueError:
                print("Please enter a valid number.")
        
        # Load audio
        original_audio, sample_rate = load_audio(selected_recording)
        
        # Apply filters
        filtered_audios = {
            'basic': filter_audio(original_audio, filter_name='basic', noise_threshold=0.6),
            'deepfilternet': filter_audio(original_audio, filter_name='deepfilternet')
        }
        
        # Save filtered audio files
        for filter_name, filtered_audio in filtered_audios.items():
            save_path = save_filtered_audio(selected_recording, filtered_audio, filter_name)
            print(f"Saved {filter_name} filtered audio to: {save_path}")
        
        # Plot comparison
        plot_audio_comparison(
            original_audio, 
            filtered_audios, 
            sample_rate, 
            f'Audio Filter Comparison: {os.path.basename(selected_recording)}'
        )
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
