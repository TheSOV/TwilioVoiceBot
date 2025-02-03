import librosa
import numpy as np
import matplotlib.pyplot as plt

# Load the noisy audio
y, sr = librosa.load("recordings/audio_20250129_072721.wav", sr=None)

# Define frame and hop length
frame_length = 1024
hop_length = 512

# Compute Short-Time Energy (STE)
energy = np.array([
    sum(abs(y[i:i + frame_length] ** 2))
    for i in range(0, len(y), hop_length)
])

# Normalize energy
energy = energy / np.max(energy)

# Estimate background noise energy as the 20th percentile
background_energy = np.percentile(energy, 20)

# Compute adaptive threshold: Main speaker is at least **3x louder** than background noise
adaptive_threshold = max(np.percentile(energy, 90), background_energy * 3)

# **Hard Threshold** (Minimum energy required to detect speech)
hard_threshold = 0.05  # Adjust this value based on your noise floor

# Use the higher of the two thresholds
main_speaker_threshold = max(adaptive_threshold, hard_threshold)

# Detect when the main speaker is talking
main_speaker_active = energy > main_speaker_threshold

# Implement a "Hangover Period" to avoid sudden silence detection
hangover_frames = 15  # Number of frames before declaring silence
speech_active = []
hangover_count = 0

for active in main_speaker_active:
    if active:
        speech_active.append(1)
        hangover_count = hangover_frames  # Reset hangover
    else:
        if hangover_count > 0:
            speech_active.append(1)
            hangover_count -= 1  # Decrease hangover counter
        else:
            speech_active.append(0)

# Convert to NumPy array
speech_active = np.array(speech_active)

# Plot results
plt.figure(figsize=(12, 5))
plt.plot(energy, label="Normalized Energy", alpha=0.7)
plt.axhline(y=adaptive_threshold, color='r', linestyle="dashed", label="Adaptive Threshold")
plt.axhline(y=background_energy, color='b', linestyle="dotted", label="Background Noise Level")
plt.axhline(y=hard_threshold, color='purple', linestyle="dashdot", label="Hard Minimum Threshold")
plt.fill_between(range(len(speech_active)), 0, 1, where=speech_active, color='green', alpha=0.3, label="Main Speaker Active")
plt.legend()
plt.xlabel("Frame Index")
plt.ylabel("Energy")
plt.title("Main Speaker Silence Detection with Hard Threshold")
plt.show()

# Plotting with speech zones and annotations
plt.figure(figsize=(15, 8))

# Plot amplitude
time = np.linspace(0, len(y) / sr, num=len(y))
plt.plot(time, y, label='Amplitude', alpha=0.5, color='blue')

# Plot energy
energy_time = np.linspace(0, len(y) / sr, num=len(energy))
plt.plot(energy_time, energy, label='Energy', color='red', linewidth=2)

# Plot threshold line
plt.axhline(y=main_speaker_threshold, color='green', linestyle='--', label='Threshold')

# Identify speech zones and annotation points
speech_starts = []
speech_ends = []
annotation_points = []
in_speech = False
threshold_time = None

# Print debug information
print("Energy max:", np.max(energy))
print("Main speaker threshold:", main_speaker_threshold)

for i in range(len(speech_active)):
    current_time = i * hop_length / sr
    
    # Detect when threshold is first reached
    if not threshold_time and energy[i] > main_speaker_threshold:
        threshold_time = current_time
        print(f"Threshold first reached at {threshold_time} seconds")
    
    # Track speech zones
    if not in_speech and speech_active[i] == 1:
        # Speech start
        speech_starts.append(current_time)
        in_speech = True
    elif in_speech and speech_active[i] == 0:
        # Speech end
        speech_ends.append(current_time)
        in_speech = False
    
    # Check for 0.75 seconds after threshold
    if threshold_time and current_time >= (threshold_time + 0.75):
        annotation_points.append(current_time)
        print(f"Annotation point added at {current_time} seconds")
        threshold_time = None  # Reset to avoid multiple annotations

# Add last speech zone if speech is ongoing
if in_speech:
    speech_ends.append(len(y) / sr)

# Add rectangles for speech zones
for start, end in zip(speech_starts, speech_ends):
    plt.axvspan(start, end, color='green', alpha=0.2)

# Add arrows for annotation points
print("Annotation points:", annotation_points)
for point in annotation_points:
    plt.annotate('0.75s', 
        xy=(point, main_speaker_threshold), 
        xytext=(point, main_speaker_threshold * 1.5),
        arrowprops=dict(
            facecolor='purple', 
            edgecolor='purple',
            width=2, 
            headwidth=10,
            headlength=10
        ),
        ha='center',
        fontweight='bold',
        color='purple'
    )

# Customize x-axis ticks to show minutes:seconds
def format_time(x, pos):
    minutes = int(x // 60)
    seconds = int(x % 60)
    return f'{minutes:02d}:{seconds:02d}'

plt.gca().xaxis.set_major_formatter(plt.FuncFormatter(format_time))

plt.title('Audio Amplitude, Energy, Speech Zones, and 0.75s Annotations')
plt.xlabel('Time (minutes:seconds)')
plt.ylabel('Normalized Amplitude / Energy')
plt.legend()
plt.tight_layout()
plt.show()
