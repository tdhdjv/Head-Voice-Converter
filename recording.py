from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import sounddevice as sd

from numpy import typing as npType

SAMPLE_RATE = 44100
CONDENSED_SAMPLE_RATE = 200

INITIAL_RECORDING_SIZE = SAMPLE_RATE
INITIAL_CONDENSED_SIZE = CONDENSED_SAMPLE_RATE

@dataclass
class RecordingData:
    samplerate:int = SAMPLE_RATE
    condensed_samplerate:int = CONDENSED_SAMPLE_RATE

    current_time:float = 0.0
    max_time:float = 0.0

    in_stream:sd.InputStream = field(init=False)
    out_stream:sd.OutputStream = field(init=False)
    should_stop:bool = False

    recording:Optional[npType.NDArray] = field(default_factory=lambda: np.zeros((INITIAL_RECORDING_SIZE, 2)))
    condensed_recording:Optional[npType.NDArray] = field(default_factory=lambda: np.zeros(INITIAL_CONDENSED_SIZE))

    def __post_init__(self) -> None:
        self.in_stream = sd.InputStream(self.samplerate, channels=2, callback=self.record_callback)
        self.out_stream = sd.OutputStream(self.samplerate, channels=2, callback=self.play_callback)
    
    def play_callback(self, outdata:npType.NDArray, frames:int, _, status:sd.CallbackFlags):
        if status:
            print(status)
        
        stream_pointer:int = int(self.current_time * self.samplerate)
        end_pointer:int = stream_pointer+frames
        
        if end_pointer >= self.recording.shape[0] or self.current_time >= self.max_time:
            outdata[:] = 0
            self.should_stop = True
        else:
            outdata[:] = self.recording[stream_pointer: stream_pointer+frames]
            self.current_time += frames/self.samplerate
        
    def record_callback(self, indata:npType.NDArray, frames:int, _, status:sd.CallbackFlags):
        if status:
            print(status)
        
        stream_pointer:int = int(self.current_time * self.samplerate)
        condensed_pointer:int = int(self.current_time * self.condensed_samplerate)
        sample_ratio:int = int(self.samplerate/self.condensed_samplerate)

        new_data = indata[:]
        new_condensed_data = new_data[0, ::sample_ratio]
        #grow data if too short
        if self.recording.shape[0] <= stream_pointer + frames:
            self.recording = np.append(self.recording, np.zeros(self.recording.shape), axis=0)
        if self.condensed_recording.shape[0] <= condensed_pointer + frames//sample_ratio:
            self.condensed_recording = np.append(self.condensed_recording, np.zeros(self.condensed_recording.shape), axis=0)

        self.recording[stream_pointer:stream_pointer+frames, :] = new_data
        self.condensed_recording[condensed_pointer:condensed_pointer+new_condensed_data.shape[0]] = new_condensed_data

        self.current_time += frames/self.samplerate
        self.max_time = max(self.max_time, self.current_time)

def start(recordingData:RecordingData):
    recordingData.current_time = 0

def toggle_record(recordingData: RecordingData):
    if not recordingData.out_stream.stopped:
        return
        
    if recordingData.in_stream.stopped:
        recordingData.in_stream.start()
    else:
        recordingData.in_stream.stop()

def toggle_play(recordingData: RecordingData):
    if not recordingData.in_stream.stopped:
        return

    if recordingData.out_stream.stopped:
        recordingData.out_stream.start()
    else:
        recordingData.out_stream.stop()

def update_recording_data(recordingData: RecordingData):
    if recordingData.should_stop:
        recordingData.out_stream.stop()
        recordingData.should_stop = False