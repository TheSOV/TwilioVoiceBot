import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.io import wavfile
from scipy.signal import find_peaks
from scipy.interpolate import CubicSpline

def plot_rolling_mean(audio_signal, sample_rate=8000, window_size=1024, step=512, output_path=None, 
plot_graph=False, speech_threshold=5000, silence_threshold=3000, speech_min_duration=0.75, 
silence_min_duration=1):
    """
    Calculate and plot rolling mean of audio signal

    Parameters:
        audio_signal (np.ndarray): Input audio waveform
        sample_rate (int): Sampling rate in Hz (default=8000)
        window_size (int): Number of samples for rolling window (default=1024)
        step (int): Step size for rolling window calculation (default=512)
        output_path (str): Optional path to save plot `image`
        plot_graph (bool): Enable/disable graph plotting (default=False)
        speech_threshold (float): Threshold for speech detection (default=5000)
        silence_threshold (float): Threshold for silence detection (default=3000)
        speech_min_duration (float): Minimum duration for speech detection (default=0.3)
        silence_min_duration (float): Minimum duration for silence detection (default=0.5)
    """
    # Validate parameters
    if silence_threshold >= speech_threshold:
        raise ValueError(f"Silence threshold ({silence_threshold}) must be lower than speech threshold ({speech_threshold})")
    
    if speech_min_duration <= 0 or silence_min_duration <= 0:
        raise ValueError("Minimum durations must be positive values")

    # Convert to absolute values and pandas Series
    abs_signal = np.abs(audio_signal)
    signal_series = pd.Series(abs_signal)
    
    # Calculate rolling mean with step
    rolling_mean = signal_series.rolling(window=window_size, center=True).mean()[::step]

    # Calculate mean, max, and min of the rolling mean
    mean_value = rolling_mean.mean()
    max_value = rolling_mean.max()
    min_value = rolling_mean.min()
    print(f'Mean of rolling mean: {mean_value}')
    print(f'Max of rolling mean: {max_value}')
    print(f'Min of rolling mean: {min_value}')


    # Create time axis
    time = np.arange(len(rolling_mean)) / sample_rate
    
    # Detect local maxima peaks
    peaks, _ = find_peaks(
        abs_signal,
        distance=int(0.1 * sample_rate),  # Minimum 100ms between peaks
        prominence=np.percentile(abs_signal, 75)
    )
    
    # Adaptive window sizing based on peak density
    min_window = int(0.1 * sample_rate)  # 100ms minimum
    max_window = int(0.4 * sample_rate)  # 400ms maximum
    
    filtered_peaks = []
    i = 0
    
    while i < len(peaks):
        # Calculate local peak density
        lookahead = min(i+5, len(peaks)-1)
        density = peaks[lookahead] - peaks[i]
        
        # Set window size inversely proportional to density
        window_size = min(max(int(density/2), min_window), max_window)
        
        current_peak = peaks[i]
        window_max = current_peak
        
        while i < len(peaks) and peaks[i] - current_peak <= window_size:
            if abs_signal[peaks[i]] > abs_signal[window_max]:
                window_max = peaks[i]
            i += 1
        
        filtered_peaks.append(window_max)
    
    # Create smooth envelope through peaks using cubic spline
    time_points = np.array(filtered_peaks) / sample_rate
    peak_values = abs_signal[filtered_peaks]
    cs = CubicSpline(time_points, peak_values, bc_type='clamped')
    smooth_envelope = np.maximum(cs(np.arange(len(abs_signal))/sample_rate), 0)
    smooth_envelope = np.clip(smooth_envelope, 0, np.max(abs_signal))
    
    # Detect speech/silence intervals
    speech_active = False
    start_time = 0
    speech_events = []
    
    # Create threshold comparison array
    above_speech_thresh = smooth_envelope > speech_threshold
    below_silence_thresh = smooth_envelope < silence_threshold
    
    for i in range(len(smooth_envelope)):
        current_time = i / sample_rate
        
        if not speech_active:
            if above_speech_thresh[i]:
                if start_time == 0:
                    start_time = current_time
                # Check duration requirement
                if (current_time - start_time) >= speech_min_duration:
                    speech_active = True
                    speech_events.append(('start', start_time))
            else:
                start_time = 0
        else:
            if below_silence_thresh[i]:
                if start_time == 0:
                    start_time = current_time
                # Check silence duration requirement
                if (current_time - start_time) >= silence_min_duration:
                    speech_active = False
                    speech_events.append(('end', current_time))
                    start_time = 0
            else:
                start_time = 0
    
    # Handle ongoing speech at end
    if speech_active:
        speech_events.append(('end', current_time))
    
    if plot_graph:
        # Plot results
        plt.figure(figsize=(12, 4))
        plt.plot(np.arange(len(audio_signal)) / sample_rate, audio_signal, alpha=0.3, label='Original Signal')
        plt.plot(time, rolling_mean, label=f'Rolling Mean (Window: 40 samples, Gaussian)', linewidth=2)
        plt.axhline(silence_threshold, color='red', linestyle='--', label=f'Silence Threshold: {silence_threshold}')
        plt.plot(
            np.array(filtered_peaks)/sample_rate,  # Convert to numpy array
            abs_signal[filtered_peaks], 
            'x', 
            label='Detected Peaks'
        )
        plt.plot(np.arange(len(abs_signal))/sample_rate, smooth_envelope, 
                label='Smooth Envelope', color='purple', linewidth=2)
        plt.axhline(speech_threshold, color='green', linestyle=':', label=f'Speech Threshold ({speech_threshold})')
        plt.axhline(silence_threshold, color='orange', linestyle=':', label=f'Silence Threshold ({silence_threshold})')
        
        # Shade speech regions
        for event_type, time in speech_events:
            if event_type == 'start':
                region_start = time
            elif event_type == 'end':
                plt.axvspan(region_start, time, alpha=0.2, color='green')
        
        plt.xlabel('Time (s)')
        plt.ylabel('Amplitude')
        plt.title('Audio Signal with Rolling Mean and Threshold')
        plt.legend()
        
        if output_path:
            plt.savefig(output_path)
            plt.close()
        else:
            plt.show()
    
    return speech_events

def detect_silent_zones(signal_series, window_size=100, 
upper_threshold=3000, silent_threshold=1.0, speaker_min_duration=0.5, 
silent_min_duration=1.0, sample_rate=8000):
    # Convert input to numpy array if it's not already
    if isinstance(signal_series, (bytes, bytearray)):
        signal_series = np.frombuffer(signal_series, dtype=np.int16)
    
    # Handle both numpy arrays and series
    signal = np.abs(signal_series.to_numpy() if hasattr(signal_series, 'to_numpy') else signal_series)

    # Calculate rolling mean using NumPy
    cumsum = np.cumsum(np.insert(signal, 0, 0))
    rolling_mean = (cumsum[window_size:] - cumsum[:-window_size]) / window_size

    # Pad rolling_mean to match original signal length
    rolling_mean = np.pad(rolling_mean, (window_size // 2, window_size // 2), mode='edge')

    # Detect speech and silence
    is_speaking = rolling_mean > upper_threshold

    # Find transitions between speech and silence
    transitions = np.diff(is_speaking.astype(int))
    speech_starts = np.where(transitions == 1)[0]
    speech_ends = np.where(transitions == -1)[0]

    # Handle edge cases
    if is_speaking[0]:
        speech_starts = np.insert(speech_starts, 0, 0)
    if is_speaking[-1]:
        speech_ends = np.append(speech_ends, len(is_speaking) - 1)

    # Calculate silent zones
    silent_zones = []
    for i in range(len(speech_ends)):
        if i < len(speech_starts) - 1:
            silent_start = speech_ends[i]
            silent_end = speech_starts[i + 1]
            silent_duration = (silent_end - silent_start) / sample_rate
            if silent_duration >= silent_min_duration:
                silent_zones.append((silent_start / sample_rate, silent_end / sample_rate))

    return bool(silent_zones)

if __name__ == "__main__":
    audio_path = "recordings/audio_20250129_072721.wav"

    try:

        sample_rate, audio_data = wavfile.read(audio_path)
        speech_events = plot_rolling_mean(audio_data, sample_rate, plot_graph=True, speech_threshold=5000, silence_threshold=3000, speech_min_duration=0.3, silence_min_duration=0.5)
        signal_series = pd.Series(np.abs(audio_data))
        silent_zones_detected = detect_silent_zones(signal_series, sample_rate=sample_rate)
        print("Silent zones detected:", silent_zones_detected)
    except FileNotFoundError:
        print(f"Audio file not found: {audio_path}")