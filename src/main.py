#
# Copyright 2018-2023 Picovoice Inc.
#
# You may not use this file except in compliance with the license. A copy of the license is located in the "LICENSE"
# file accompanying this source.
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
# an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
#
import os
import pveagle
from pvrecorder import PvRecorder
import wave
import struct
import argparse
import pvporcupine
from datetime import datetime
speaker_name = None


def get_files_in_directory(directory_path):
    return [f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))]



def def_porcupine_args(access_key, NON_ENGLISH_MODEL_PATH, NON_ENGLISH_KEYWORD_PATH):

    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--access_key',
        help='AccessKey obtained from Picovoice Console (https://console.picovoice.ai/)')

    parser.add_argument(
        '--keywords',
        nargs='+',
        help='List of default keywords for detection. Available keywords: %s' % ', '.join(
            '%s' % w for w in sorted(pvporcupine.KEYWORDS)),
        choices=sorted(pvporcupine.KEYWORDS),
        metavar='')

    parser.add_argument(
        '--keyword_paths',
        nargs='+',
        help="Absolute paths to keyword model files. If not set it will be populated from `--keywords` argument")

    parser.add_argument(
        '--library_path',
        help='Absolute path to dynamic library. Default: using the library provided by `pvporcupine`')

    parser.add_argument(
        '--model_path',
        help='Absolute path to the file containing model parameters. '
                'Default: using the library provided by `pvporcupine`')

    parser.add_argument(
        '--sensitivities',
        nargs='+',
        help="Sensitivities for detecting keywords. Each value should be a number within [0, 1]. A higher "
                "sensitivity results in fewer misses at the cost of increasing the false alarm rate. If not set 0.5 "
                "will be used.",
        type=float,
        default=None)

    parser.add_argument('--audio_device_index', help='Index of input audio device.', type=int, default=-1)

    parser.add_argument('--output_path', help='Absolute path to recorded audio for debugging.', default=None)

    parser.add_argument('--show_audio_devices', action='store_true')

    args = parser.parse_args()
    args.access_key = access_key
    args.model_path = NON_ENGLISH_MODEL_PATH
    args.keyword_paths = [NON_ENGLISH_KEYWORD_PATH]


    if args.keyword_paths is None:
        if args.keywords is None:
            raise ValueError("Either `--keywords` or `--keyword_paths` must be set.")

        keyword_paths = [pvporcupine.KEYWORD_PATHS[x] for x in args.keywords]
    else:
        keyword_paths = args.keyword_paths

    if args.sensitivities is None:
        args.sensitivities = [0.5] * len(keyword_paths)

    if len(keyword_paths) != len(args.sensitivities):
        raise ValueError('Number of keywords does not match the number of sensitivities.')

    try:
        porcupine = pvporcupine.create(
            access_key=args.access_key,
            library_path=args.library_path,
            model_path=args.model_path,
            keyword_paths=keyword_paths,
            sensitivities=args.sensitivities)
    except pvporcupine.PorcupineInvalidArgumentError as e:
        print("One or more arguments provided to Porcupine is invalid: ", args)
        print(e)
        raise e
    except pvporcupine.PorcupineActivationError as e:
        print("AccessKey activation error")
        raise e
    except pvporcupine.PorcupineActivationLimitError as e:
        print("AccessKey '%s' has reached it's temporary device limit" % args.access_key)
        raise e
    except pvporcupine.PorcupineActivationRefusedError as e:
        print("AccessKey '%s' refused" % args.access_key)
        raise e
    except pvporcupine.PorcupineActivationThrottledError as e:
        print("AccessKey '%s' has been throttled" % args.access_key)
        raise e
    except pvporcupine.PorcupineError as e:
        print("Failed to initialize Porcupine")
        raise e

    keywords = list()
    for x in keyword_paths:
        keyword_phrase_part = os.path.basename(x).replace('.ppn', '').split('_')
        if len(keyword_phrase_part) > 6:
            keywords.append(' '.join(keyword_phrase_part[0:-6]))
        else:
            keywords.append(keyword_phrase_part[0])      
    
    return porcupine, args

def load_speaker_profile():
    # Load the speaker profile
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

    return profiles, speaker_labels

# --------------------------------------- MAIN
if __name__ == '__main__':
    
    access_key="crtaUuhqVcVSJ5k/xf97tkJxc88oCXNt7U81rvoSHN9TK7jXTnFzvg=="
    NON_ENGLISH_MODEL_PATH="/home/grosato/python_ws/porcupine/lib/common/porcupine_params_it.pv"
    NON_ENGLISH_KEYWORD_PATH="/home/grosato/python_ws/ciao-alter-ego_it_linux_v3_0_0.ppn"

    # define porcupine args and create object
    porcupine, args = def_porcupine_args(access_key, NON_ENGLISH_MODEL_PATH, NON_ENGLISH_KEYWORD_PATH)
    
    # Load the speaker profile
    profiles, speaker_labels = load_speaker_profile()
    

    # Create the recognizer
    try:
        eagle = pveagle.create_recognizer(
            access_key=access_key,
            speaker_profiles=profiles)
    except pveagle.EagleError as e:
        # Handle error
        print('Erroooor')
        pass

    recorder = PvRecorder(frame_length=porcupine.frame_length, device_index=args.audio_device_index)
    recorder.start()
    # Initialize the scores vector with fixed size
    scores_vector = [[0 for _ in range(20)] for _ in range(2)]
    sum_scores = [0, 0]
    print('Listening ... (press Ctrl+C to exit)')
    try:
        while True:

            
            audio_frame = recorder.read()
            scores = eagle.process(audio_frame)
            result = porcupine.process(audio_frame)

            # print(scores)
            
            for i in range(len(scores)):
                # Append the scores to the scores vector
                scores_vector[i].append(scores[i])
                # print("index ", i, " score" ,scores_vector[i])
                # Keep the last 20 scores
                if len(scores_vector[i]) > 20:
                    # Remove the first element
                    scores_vector[i].pop(0)
                    # Calculate the sum of the scores
                    sum_scores[i] = sum(scores_vector[i])/20
                    # print("index ", i, " sum_score" ,sum_scores[i])
                    
            # # # Check if Ciao Ego is detected
            if result >= 0:
                for i in range(len(sum_scores)):
                    if(sum_scores[i] > 0):
                        speaker_name = speaker_labels[i]

                if speaker_name is not None:
                    print('Ciao', speaker_name)
                    speaker_name = None
                else:
                    print('Ciao')


    except KeyboardInterrupt:
        print('Stopping ...')
    finally:
        recorder.delete()
        porcupine.delete()
        eagle.delete()
