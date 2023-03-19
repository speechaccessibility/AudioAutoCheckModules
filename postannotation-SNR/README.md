# postannotation-snr
Input .wav and .json paths, generate snr and detect audio clipping.

Usage: python snr.py {path to wav file} {path to json file}

Output Format: {'audio_id':audio_id (str), 'snr': snr (float, up to two decimal places), 'approximation': approximation (boolean, true if approximated)}

Reference: http://labrosa.ee.columbia.edu/~dpwe/tmp/nist/doc/stnr.txt
