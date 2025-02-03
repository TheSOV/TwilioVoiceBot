import numpy as np
import torch
from df.enhance import enhance, init_df, load_audio, save_audio

# Global variables to store DeepFilterNet model and state
_df_model = None
_df_state = None

def initialize_deepfilternet():
    """
    Initialize DeepFilterNet model globally to avoid repeated initialization.
    
    Returns:
        tuple: Initialized model and state
    """
    global _df_model, _df_state
    
    # Initialize only if not already initialized
    if _df_model is None or _df_state is None:
        try:
            _df_model, _df_state, _ = init_df()
            print("DeepFilterNet model initialized globally")
        except Exception as e:
            print(f"DeepFilterNet initialization error: {e}")
            raise
    
    return _df_model, _df_state

def filter_audio(audio_np, filter_name='basic', **kwargs):
    """
    Apply noise reduction to audio data using the specified filter.
    
    Args:
        audio_np (np.ndarray): Input audio data as a NumPy array
        filter_name (str): Name of the filter to apply
        kwargs: Additional arguments for the filter
    
    Returns:
        np.ndarray: Noise-reduced audio data
    """
    if filter_name == 'basic':
        return basic_filter(audio_np, **kwargs)
    elif filter_name == 'deepfilternet':
        return deepfilternet_filter(audio_np, **kwargs)
    else:
        raise ValueError(f"Unknown filter: {filter_name}")

def basic_filter(audio_np, noise_threshold=1000):
    """
    Apply basic noise reduction to audio data.
    
    Args:
        audio_np (np.ndarray): Input audio data as a NumPy array
        noise_threshold (int): PCM threshold value (0-32767). Values below this will be zeroed.
                             Typical values:
                             - Very quiet: 100-500
                             - Quiet: 500-2000
                             - Moderate: 2000-5000
                             - Loud: 5000-10000
    
    Returns:
        np.ndarray: Noise-reduced audio data
    """
    # Make a writable copy
    filtered_audio = audio_np.copy()
    
    # Zero out samples below the noise threshold
    filtered_audio[np.abs(filtered_audio) < noise_threshold] = 0
    

    return filtered_audio

def deepfilternet_filter(audio_np, **kwargs):
    """
    Apply DeepFilterNet noise reduction.
    
    Args:
        audio_np (np.ndarray): Input audio data as a NumPy array
        kwargs: Additional arguments for DeepFilterNet
    
    Returns:
        np.ndarray: Noise-reduced audio data
    """
    try:
        audio, _ = load_audio(audio_np, sr=_df_state.sr())
        enhanced_audio = enhance(_df_model, _df_state, audio)
        
        return enhanced_audio
    
    except Exception as e:
        print(f"DeepFilterNet enhancement error: {e}")
        # Fallback to basic filter if DeepFilterNet fails
        return basic_filter(audio_np)

# Initialize the model when the module is imported
try:
    initialize_deepfilternet()
except Exception as e:
    print(f"Could not pre-initialize DeepFilterNet: {e}")
