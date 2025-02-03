import os
import glob
import numpy as np
import soundfile as sf
import matplotlib.pyplot as plt
import torch
from df import enhance, init_df

def list_recordings():
    """List all WAV files in the recordings directory."""
    recordings_dir = 'recordings'
    if not os.path.exists(recordings_dir):
        raise FileNotFoundError("No recordings directory found")
    
    wav_files = glob.glob(os.path.join(recordings_dir, '*.wav'))
    if not wav_files:
        raise FileNotFoundError("No WAV files found in recordings directory")
    
    return wav_files

def select_recording(recordings):
    """
    Allow user to select a recording from the list.
    
    Args:
        recordings (list): List of WAV file paths
    
    Returns:
        str: Selected WAV file path
    """
    print("Available recordings:")
    for i, recording in enumerate(recordings, 1):
        print(f"{i}. {os.path.basename(recording)}")
    
    while True:
        try:
            selection = int(input("Enter the number of the recording you want to enhance: ")) - 1
            if 0 <= selection < len(recordings):
                return recordings[selection]
            else:
                print("Invalid selection. Please try again.")
        except ValueError:
            print("Please enter a valid number.")

def load_audio(file_path):
    """
    Load audio file using soundfile.
    
    Args:
        file_path (str): Path to the WAV file
    
    Returns:
        tuple: (audio_data, sample_rate)
    """
    audio_data, sample_rate = sf.read(file_path)
    return audio_data, sample_rate

def plot_audio_comparison(original, enhanced, sample_rate, title):
    """
    Plot comparison of original and enhanced audio signals.
    
    Args:
        original (np.ndarray): Original audio signal
        enhanced (np.ndarray): Enhanced audio signal
        sample_rate (int): Audio sample rate
        title (str): Plot title
    """
    plt.figure(figsize=(15, 6))
    plt.suptitle(title, fontsize=16)
    
    # Time axis for plotting
    time_original = np.linspace(0, len(original) / sample_rate, num=len(original))
    time_enhanced = np.linspace(0, len(enhanced) / sample_rate, num=len(enhanced))
    
    # Original Signal
    plt.subplot(1, 2, 1)
    plt.plot(time_original, original)
    plt.title('Original Signal')
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude')
    
    # Enhanced Signal
    plt.subplot(1, 2, 2)
    plt.plot(time_enhanced, enhanced)
    plt.title('Enhanced Signal')
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude')
    
    plt.tight_layout()
    plt.show()

def save_enhanced_audio(enhanced_audio, original_path, sample_rate):
    """
    Save the enhanced audio to a new file.
    
    Args:
        enhanced_audio (np.ndarray): Enhanced audio signal
        original_path (str): Path of the original audio file
        sample_rate (int): Audio sample rate
    
    Returns:
        str: Path of the saved enhanced audio file
    """
    # Create enhanced recordings directory if it doesn't exist
    enhanced_dir = 'enhanced_recordings'
    os.makedirs(enhanced_dir, exist_ok=True)
    
    # Generate filename
    filename = os.path.basename(original_path)
    base, ext = os.path.splitext(filename)
    enhanced_filename = f"{base}_enhanced{ext}"
    enhanced_path = os.path.join(enhanced_dir, enhanced_filename)
    
    # Save enhanced audio
    sf.write(enhanced_path, enhanced_audio, sample_rate)
    print(f"Enhanced audio saved to: {enhanced_path}")
    
    return enhanced_path

def main():
    """
    Main function to select and enhance an audio recording using DeepFilterNet.
    """
    try:
        # Initialize DeepFilterNet model
        model, df_state, _ = init_df()
        
        # List and select recording
        recordings = list_recordings()
        selected_recording = select_recording(recordings)
        
        # Load audio
        original_audio, sample_rate = load_audio(selected_recording)
        
        # Convert to PyTorch tensor
        # Reshape to (1, samples) for mono audio
        audio_tensor = torch.from_numpy(original_audio.astype(np.float32)).unsqueeze(0)
        
        # Apply DeepFilterNet noise reduction
        enhanced_audio = enhance(model, df_state, audio_tensor)
        
        # Convert back to NumPy array
        enhanced_audio = enhanced_audio.squeeze().numpy()
        
        # Plot comparison
        plot_audio_comparison(
            original_audio, 
            enhanced_audio, 
            sample_rate, 
            f'Audio Enhancement: {os.path.basename(selected_recording)}'
        )
        
        # Save enhanced audio
        save_enhanced_audio(enhanced_audio, selected_recording, sample_rate)
    
    except Exception as e:
        print(f"Error processing audio: {e}")

if __name__ == "__main__":
    main()