import pveagle
from pvrecorder import PvRecorder
import os

access_key="crtaUuhqVcVSJ5k/xf97tkJxc88oCXNt7U81rvoSHN9TK7jXTnFzvg=="

def get_files_in_directory(directory_path):
    return [f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))]
    
input_profile_paths = []


# Usage
directory_path = "/home/grosato/python_ws/profiles"  
files = get_files_in_directory(directory_path)
# concatenate the directory_path with the file in a list
input_profile_paths = [os.path.join(directory_path, file) for file in files]


profiles = list()
speaker_labels = list()
for profile_path in input_profile_paths:
    speaker_labels.append(os.path.splitext(os.path.basename(profile_path))[0])
    with open(profile_path, 'rb') as f:
        profile = pveagle.EagleProfile.from_bytes(f.read())
    profiles.append(profile)


try:
    eagle = pveagle.create_recognizer(
        access_key=access_key,
        speaker_profiles=profiles)
except pveagle.EagleError as e:
    # Handle error
    pass

DEFAULT_DEVICE_INDEX = -1
recorder = PvRecorder(
    device_index=DEFAULT_DEVICE_INDEX,
    frame_length=eagle.frame_length)

recorder.start()
while True:
    audio_frame = recorder.read()
    scores = eagle.process(audio_frame)
    print(scores, speaker_labels)

eagle.delete()
recorder.stop()