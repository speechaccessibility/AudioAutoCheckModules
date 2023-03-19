# -*- coding: utf-8 -*-

from collections import deque
from contextlib import closing
import sys
import wave
import numpy as np
from json import dump
from webrtcvad import Vad


def read_wave(path):

    with closing(wave.open(path, 'rb')) as wf:
        sample_width = wf.getsampwidth()
        assert sample_width == 2
        sample_rate = wf.getframerate()
        assert sample_rate in (8000, 16000, 32000, 48000)
        pcm_data = wf.readframes(wf.getnframes())
        num_channels = wf.getnchannels()
        # insert solution for multi-channels
        if num_channels == 2:
            wave_data = np.frombuffer(pcm_data, dtype=np.short)
            wave_data.shape = (-1, num_channels)
            mono_wave = np.sum(wave_data, axis=1, keepdims=True)/num_channels
            ints = mono_wave.astype(np.int16)
            mono_data = ints.astype('<u2').tobytes()
            return mono_data, sample_rate
        else:
            assert num_channels == 1
            return pcm_data, sample_rate


class Frame(object):

    def __init__(self, bytes, timestamp, duration):
        self.bytes = bytes
        self.timestamp = timestamp
        self.duration = duration


def frame_generator(frame_duration_ms, audio, sample_rate):

    n = int(sample_rate * (frame_duration_ms / 1000.0) * 2)
    offset = 0
    timestamp = 0.0
    duration = (float(n) / sample_rate) / 2.0
    while offset + n < len(audio):
        yield Frame(audio[offset:offset + n], timestamp, duration)
        timestamp += duration
        offset += n


def vad_collector(sample_rate, frame_duration_ms,
                  padding_duration_ms, vad, frames):
    
    num_padding_frames = int(padding_duration_ms / frame_duration_ms)

    ring_buffer = deque(maxlen=num_padding_frames)

    triggered = False

    voiced_frames = []
    
    for frame in frames:
        is_speech = vad.is_speech(frame.bytes, sample_rate)

        if not triggered:
            ring_buffer.append((frame, is_speech))
            num_voiced = len([f for f, speech in ring_buffer if speech])

            if num_voiced > 0.9 * ring_buffer.maxlen:
                triggered = True
                yield ring_buffer[0][0].timestamp
                
                for f, s in ring_buffer:
                    voiced_frames.append(f)
                ring_buffer.clear()
        else:
            
            voiced_frames.append(frame)
            ring_buffer.append((frame, is_speech))
            num_unvoiced = len([f for f, speech in ring_buffer if not speech])
            index_unvoiced = [i for i, buffer in enumerate(ring_buffer) if not buffer[1]]

            if num_unvoiced > 0.3 * ring_buffer.maxlen:
                num_frame = len([f for f, speech in ring_buffer]) - index_unvoiced[0]
                yield frame.timestamp - frame.duration * num_frame
                triggered = False
                ring_buffer.clear()
                voiced_frames = []
    if triggered:
        yield frame.timestamp


def write_json(json_path, audio_id, start_time, end_time):
    
    with open(json_path,"w") as f:
        flickr_dict = {'audio_id':audio_id,'start_time': start_time, 'end_time': end_time}
        dump(flickr_dict,f)


def main(args):
    if len(args) != 2:
        sys.stderr.write(
            'Usage: vad.exe <path to wav file> <path to json file>\n')
        sys.exit(1)
    audio, sample_rate = read_wave(args[0])
    vad = Vad(3)
    frames = frame_generator(10, audio, sample_rate)
    frames = list(frames)
    time_step = vad_collector(sample_rate, 10, 300, vad, frames)
    time_list = list(time_step)
    if len(time_list) > 0:
        start_time = round(time_list[0], 4)
        end_time = round(time_list[-1], 4)
    else:
        start_time = 0
        end_time = 0
    # write .json
    audio_id = args[0][:-4]
    json_path = args[1]
    write_json(json_path, audio_id, start_time, end_time)
    print(type(start_time))
    

if __name__ == '__main__':
    main(sys.argv[1:])