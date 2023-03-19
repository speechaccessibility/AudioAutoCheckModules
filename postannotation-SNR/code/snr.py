# -*- coding: utf-8 -*-
"""
Created on Mon Feb 20 20:33:56 2023

@author: xiuwenz2

Calculate NIST STNR actually in Matlab, attempting to duplicate
stnr -c algorithm

2011-08-02 Dan Ellis dpwe@ee.columbia.edu
"""

from contextlib import closing
import sys
import wave
import numpy as np
from scipy import signal
from statistics import median
from json import dump


def read_wave(path, norm):

    with closing(wave.open(path, 'rb')) as wf:
        sample_rate = wf.getframerate()
        pcm_data = wf.readframes(wf.getnframes())
        num_channels = wf.getnchannels()
        # insert solution for multi-channels
        if num_channels == 2:
            wave_data = np.frombuffer(pcm_data, dtype=np.short)
            wave_data.shape = (-1, num_channels)
            mono_wave = np.sum(wave_data, axis=1, keepdims=True)/num_channels
            mono_data = mono_wave.astype(np.int16)
            if norm:
                rmsmono = (mono_data**2).mean()**0.5
                scalarmono = 10 ** (-25 / 20) / rmsmono
                mono_data = mono_data * scalarmono
            return mono_data, sample_rate
        else:
            assert num_channels == 1
            wave_data = np.frombuffer(pcm_data, dtype=np.short)
            if norm:
                rmsmono = (wave_data**2).mean()**0.5
                scalarmono = 10 ** (-25 / 20) / rmsmono
                wave_data = wave_data * scalarmono
            return wave_data, sample_rate


def medianf(X,W):
    
    nc = np.shape(X)[0];
    # nr = 1
    R = np.zeros(np.shape(X))
    w2 = int(np.floor(W/2))
    # print(X[0])
    # print(X[1])
    # print(np.zeros((nr, w2)))
    xx = np.hstack((X, np.zeros(w2)))
    xx = np.hstack((np.zeros(w2), xx))
    for c in range(nc):
        R[c] = median(xx[c:c+W])
    return np.array([R])


def nist_stnr(D,SR):

    # constants from snr.h
    MILI_SEC = 20.0;
    NOISE_LEVEL = 0.05;
    PEAK_LEVEL = 0.95;

    BINS = 500;
    SMOOTH_BINS = 15;
    CODEC_SMOOTH_BINS = 15;
    LOW = -28;
    HIGH = 96.75;

    # BLOCKSIZE = 2048;

    # constants from hist.h
    PEAK = 0;
    TROUGH = 1;
    # PEAK_WIDTH = 3;

    # algorithm is to form a power histogram over 20ms windows

    frame_width = SR / 1000 * MILI_SEC;
    frame_adv = int(frame_width / 2);

    # calculate power, assuming short samples
    D2 = (D/2)**2;

    nhops = int(np.floor(len(D2)/frame_adv));
    # D2 = np.reshape(D2[0:int(nhops*frame_adv)], (frame_adv, nhops));
    D2 = np.reshape(D2[0:int(nhops*frame_adv)], (nhops, frame_adv));
    # Power in each half window
    P2 = np.mean(D2,axis=1);
    # Power in overlapping windows
    conv = np.convolve([1,1],P2)
    Pdb = 10*np.log10(np.where(conv > 0.0000000001, conv, 0.0000000001));

    # Histogram
    hvals = np.linspace(LOW-0.25, HIGH+0.25, num=BINS+2, endpoint=True)
    power_hist = np.histogram(Pdb, bins=hvals)
    
    # stnr -c algorithm
    unspiked_hist = medianf(power_hist[0],3);
    presmooth_hist = signal.convolve2d(unspiked_hist,
                                       np.ones((1,CODEC_SMOOTH_BINS*2+1))/(CODEC_SMOOTH_BINS*2+1),
                                       mode='same');
    smoothed_hist = signal.convolve2d(presmooth_hist,
                                      np.ones((1,SMOOTH_BINS*2+1))/(SMOOTH_BINS*2+1),
                                      mode='same');
    unspiked_hist = unspiked_hist[0]
    presmooth_hist = presmooth_hist[0]
    smoothed_hist = smoothed_hist[0]

    # assume to begin with that we don't find any extrema */
    first_peak=BINS;
    first_trough=BINS;
    second_peak=BINS;
    second_trough=BINS;

    max_val = np.max(smoothed_hist);
    # now look for the extrema, sequentially */
    
    # find the noise peak; it should be reasonably big */
    starting_point=0;
    first_peak = locate_extremum(smoothed_hist,starting_point,BINS,PEAK);
    
    while (15*smoothed_hist[first_peak]) < max_val: # coef from 10 to 15
        first_peak = locate_extremum(smoothed_hist,starting_point,BINS,PEAK);
        starting_point = first_peak+1;
    # now find the rest */
    first_trough = locate_extremum(smoothed_hist,first_peak,BINS,TROUGH);
    second_peak = locate_extremum(smoothed_hist,first_trough,BINS,PEAK);
    second_trough = locate_extremum(smoothed_hist,second_peak,BINS,TROUGH);
    
    if first_peak==BINS:
        S = 0;
        return S, False
    
    noise_lvl = pick_center(smoothed_hist, first_peak);

    if first_trough==BINS:
        # for i in range(0,first_peak):
        #     full_hist[i] = 0;
        # cross_lvl = -Inf;
        noise_lvl = percentile_hist(unspiked_hist,BINS,NOISE_LEVEL);
        speech_lvl = percentile_hist(unspiked_hist,BINS,PEAK_LEVEL);
        S = speech_lvl - noise_lvl;
        return S, True
    
    for i in range(0,first_trough):
        unspiked_hist[i]=0;
    
    
    if second_peak==BINS:
        speech_lvl = percentile_hist(unspiked_hist,BINS,PEAK_LEVEL);
        S = speech_lvl - noise_lvl;
        return S, False
    # cross_lvl = -Inf;
      
    # # check for bogus hump */
    # if 60*(smoothed_hist(1+second_peak)-smoothed_hist(1+first_trough)) ...
    #       < smoothed_hist(1+first_peak)
    #   cross_lvl = -Inf;
    # else
    #   cross_lvl = pick_center(smoothed_hist, second_peak);
    # end
    
    if second_trough == BINS:
        second_lim = second_peak;
    else:
        second_lim = second_trough;
    
    for i in range(0,second_lim):
        unspiked_hist[i]=0;
        
    
    speech_lvl = percentile_hist(unspiked_hist,BINS,PEAK_LEVEL);
    
    S = speech_lvl - noise_lvl;
    
    return S, False


def locate_extremum(h,FROM,TO,TYPE):
    # from hist.c
    # from hist.h
    PEAK = 0;
    TROUGH = 1;
    PEAK_WIDTH = 3;
    
    for i in range(FROM+PEAK_WIDTH,TO-PEAK_WIDTH):
      if h[i] == 0:  # not interested in extrema at 0 
        continue;
      
      extremum=1; # assume it's an extremum to begin with
      pre_swing=0;
      post_swing=0;
      swing_loc=i-PEAK_WIDTH;
      for j in range(i-PEAK_WIDTH,i): # check the preceding samples
        if TYPE==PEAK:
          if h[j] > h[j+1]:
            extremum=0;
            break;
          if h[j] != h[j+1]:
            pre_swing=1;
        else: # type == TROUGH */
          if h[j] < h[j+1]:
            extremum=0;
            break;
          if h[j] != h[j+1]:
            pre_swing=1;
          
      if extremum == 0:
        continue;
        
      for j in range(i, i+PEAK_WIDTH):
        if TYPE==PEAK:
          if h[j] < h[j+1]:
            extremum=0;
            break;
          if h[j] != h[j+1]:
            post_swing=1;
        else: # type == TROUGH
          if h[j] > h[j+1]:
            extremum=0;
            break;
          if h[j] != h[j+1]:
            post_swing=1;
    
      # check to make sure it isn't a step function
      # this kind of check is necessary if the peak is wider than the window
      # if (((pre_swing+post_swing)<=1)&&(extremum))
      if pre_swing+post_swing<=1 and extremum:
        for k in range(i,FROM,-1):
          diff1 = h[k-1] - h[k]
          if diff1 != 0:
            break
        
        swing_loc=k
        for k in range(i,TO-1): # find next swing
          diff2 = h[k] - h[k+1]
          if diff2 !=0:
            break
        
        next_swing_loc=k
        if TYPE==PEAK and (diff1>0 or diff2<0):
            continue # no dice
        if TYPE==TROUGH and (diff1<0 or diff2>0):
            continue # ditto 
        
        # otherwise, the peak is at the mid-point of this plateau
        retval = int(np.round((swing_loc+next_swing_loc)/2))
        return retval
      if extremum:
        retval = i
        return retval
    
    retval = TO
    
    return retval


def pick_center(h, binn):
    # from snr.c
    
    BINS = 500
    LOW = -28.125
    HIGH = 96.875
    
    step = (HIGH-LOW)/BINS
    
    val = LOW+step*(binn+0.5)
    
    return val


def percentile_hist(h, bins, percent):

    cumm = np.cumsum(h)
    binn = np.where(cumm >= percent * cumm[-1], 0, 1)
    binn = np.sum(binn)
    val = pick_center(h, binn)
    
    return val


def write_json(json_path, audio_id, snr, approximation):
    
    with open(json_path,"w") as f:
        json_dict = {'audio_id': audio_id,'snr': snr, 'approximation': approximation}
        dump(json_dict,f)


def main(args):
    if len(args) != 2:
        sys.stderr.write(
            'Usage: snr.py <path to wav file> <path to json file>\n')
        sys.exit(1)
    audio, sr = read_wave(args[0], norm = False)
    snr, peak_is_single = nist_stnr(audio, sr)
    # write .json
    audio_id = args[0][:-4]
    json_path = args[1]
    write_json(json_path, audio_id, snr, peak_is_single)

    
if __name__ == '__main__':
    main(sys.argv[1:])