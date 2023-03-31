# postannotation-snr
Input .wav and .json paths, generate snr and detect audio clipping.

Usage: python snr-clip.py {path to wav file} {path to json file}

Output Format: {'audio_id':audio_id (str), 'snr': snr (float, up to two decimal places), 'snr_approximation': approximation (boolean, true if approximated),
'clip': audio_is_clip (boolean, true if clipped), 'clip_duration': duration (in seconds, float, up to four decimal places)}

Reference: #1. Original documents at http://labrosa.ee.columbia.edu/~dpwe/tmp/nist/doc/stnr.txt
#2. Matlab implementation at https://labrosa.ee.columbia.edu/projects/snreval/snreval.zip
#3. 

Notes: [SNR] This snr algorithm for noisy audio is constructed on the basis of nist-stnr method (preferred). Compared to the Matlab implementation, two modifications are made in order to better fit those audios with abnormal peak curves. #1. If (scale * the first peak > supremum), it is considered to be the noise level. The scale is set to be 10 in Matlab s.t. the noise level is reasonably big. In this case, we set the scale to be 15 in order to improve compatibility. #2. If only one peak is detected, the resulting snr by Matlab seems not very reasonale. Inspired by the "quick" nist-stnr method, we come up with another snr approximation in place of the Matlab outcome, where the noise level is set to be 5%, while the speech level remains 95%. However, this kind of method is not endorsed by NIST and thus it is for reference only. Under this circumstance, 'approximation' is True. (According to experiments on the MS-SNSD-master dataset, this rarely happens as only 3 of the first 50 audios has only one peak within clean-test set.) [CLIP] 
