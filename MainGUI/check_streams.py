# -*- coding: utf-8 -*-
"""
Created on Sun Mar  1 11:30:02 2020

@author: Antonio
"""
from pylsl import StreamInlet, resolve_stream

def check_cont_streams(): # Checks if there is a continuous, plottable stream available
    availableStreams = False
    streams = resolve_stream()
        
    for stream in streams:
        stream_type = StreamInlet(stream).info().type()
        if stream_type == "Markers" or stream_type == "Events":
            pass
        else:
            availableStreams = True
            
    return availableStreams