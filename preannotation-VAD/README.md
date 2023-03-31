# preannotation-vad
Input .wav and .json paths, generate start and end time of speech w.r.t. the beginning of audio.

#### Usage:
```
python vad.py {path to wav file} {path to json file}
```

#### Output Format:
```
{'audio_id':audio_id (str), 'start_time': start_time (float, in seconds, up to four decimal places), 'end_time': end_time (float, in seconds, up to four decimal places)}
```

#### Reference:
+ [VAD] A python interface to the WebRTC Voice Activity Detector (VAD) at https://github.com/wiseman/py-webrtcvad
