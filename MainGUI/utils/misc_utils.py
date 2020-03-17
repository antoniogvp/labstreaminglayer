# -*- coding: utf-8 -*-
"""
Created on Sun Mar  1 11:30:02 2020

@author: Antonio
"""
from pylsl import StreamInlet, resolve_stream
from os import path
from qtpy import QtWidgets

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

def checkPath():
    start = True
    if not(path.exists('vis_stream.m')): 
        start = False
        QtWidgets.QMessageBox.critical(None,'Error','MATLAB vis_stream.m fuction was not found. Is the file in the correct directory?',QtWidgets.QMessageBox.Ok)
    elif not(path.exists('../../LSL/liblsl-Matlab')):
        start = False
        QtWidgets.QMessageBox.critical(None,'Error','MATLAB LSL library was not found. Is the file in the correct directory?',QtWidgets.QMessageBox.Ok)
    return start

def noStreams():
    QtWidgets.QMessageBox.critical(None,'Error','No online, continuous streams were found. Please make sure devices are correctly connected and linked.',QtWidgets.QMessageBox.Cancel)