# -*- coding: utf-8 -*-
"""
Created on Wed Mar 11 19:16:06 2020

@author: Antonio
"""

import importlib
import subprocess
from qtpy import QtWidgets
from os import path, chdir
import time
import sys
from misc_utils import check_cont_streams, checkPath, noStreams

class ViewerCreator():
    def __init__(self):
        self.eng = None
    
    def startMATLABViewer(self):
        matlab_spec = importlib.util.find_spec("matlab.engine")
        matlab_found = matlab_spec is not None
            
        if not matlab_found:
            print("MATLAB Engine API for Python has not been found. Running MATLAB from shell.")
            try:
                matlab_cmd = "addpath(genpath('../../LSL/liblsl-Matlab')); vis_stream()"
                win_cmd = 'matlab -nosplash -nodesktop -wait -r ' + '"' + matlab_cmd + '"'
                subprocess.call(win_cmd, shell=True)
            except subprocess.CalledProcessError:
                QtWidgets.QMessageBox.critical(None,'Error','MATLAB was not found. Is MATLAB installed in your system?',QtWidgets.QMessageBox.Cancel)
        else:
            import matlab.engine
            print("MATLAB Engine API is loading... Do not close window.")
            self.eng = matlab.engine.start_matlab()
            self.eng.addpath(self.eng.genpath('../../LSL/liblsl-Matlab'))
            self.eng.vis_stream(nargout=0, background=True)
                
        return self.eng

if __name__ == "__main__":
    abspath = path.abspath(__file__)
    dname = path.dirname(abspath)
    chdir(dname)
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    if checkPath():
        if check_cont_streams():
            v = ViewerCreator()
            eng = v.startMATLABViewer()
            while True:
                time.sleep(1)
        else:
            noStreams()