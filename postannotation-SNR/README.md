# postannotation-snr
Input .wav and .json paths, generate snr and detect audio clipping.

Usage: python snr.py {path to wav file} {path to json file}

Output Format: {'audio_id':audio_id (str), 'snr': snr (float, up to two decimal places), 'approximation': approximation (boolean, true if approximated)}

Reference: 1. Original documents at http://labrosa.ee.columbia.edu/~dpwe/tmp/nist/doc/stnr.txt
2. Matlab implementation at https://labrosa.ee.columbia.edu/projects/snreval/snreval.zip

Notes: This snr algorithm for noisy audio is constructed on the basis of nist-stnr method. Compared to 
