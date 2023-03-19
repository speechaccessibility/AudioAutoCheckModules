# postannotation-snr
Input .wav and .json paths, generate snr and detect audio clipping.

Usage: python snr.py {path to wav file} {path to json file}

Output Format: {'audio_id':audio_id (str), 'snr': snr (float, in seconds, up to four decimal places), 'end_time': end_time (float, in seconds, up to four decimal places)}

{'audio_id': audio_id,'snr': snr, 'approximation': approximation}

Reference: https://github.com/wiseman/py-webrtcvad
