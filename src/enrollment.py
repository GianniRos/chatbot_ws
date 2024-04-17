import pveagle
from pvrecorder import PvRecorder

access_key="crtaUuhqVcVSJ5k/xf97tkJxc88oCXNt7U81rvoSHN9TK7jXTnFzvg=="
output_profile_path="/home/grosato/python_ws/profiles/speaker_profile.json"
try:
    eagle_profiler = pveagle.create_profiler(access_key=access_key)
except pveagle.EagleError as e:
    # Handle error
    pass

DEFAULT_DEVICE_INDEX = -1
recorder = PvRecorder(
    device_index=DEFAULT_DEVICE_INDEX,
    frame_length=eagle_profiler.min_enroll_samples)

recorder.start()

enroll_percentage = 0.0
while enroll_percentage < 100.0:
    audio_frame = recorder.read()
    enroll_percentage, feedback = eagle_profiler.enroll(audio_frame)
    print('Enrollment progress: %.2f%%' % enroll_percentage)

recorder.stop()
speaker_profile = eagle_profiler.export()
with open(output_profile_path, 'wb') as f:
    f.write(speaker_profile.to_bytes())
print('\nSpeaker profile is saved to %s' % output_profile_path)
