# -*- coding: utf-8 -*-
"""
Created on Thu Apr 11 17:04:26 2019

@author: Antonio
"""

import sys
from qtpy import QtWidgets, uic
import subprocess, platform
import importlib
import gui_config
from os import path, getcwd
 
qtCreatorFile = "launcher.ui"

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)
 
class MainGUI(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.pushButton.clicked.connect(lambda: self.startLSLApp("appBioSemi"))                     # BioSemi
        self.pushButton_2.clicked.connect(lambda: self.startLSLApp("appFaros"))                     # Faros
        self.pushButton_3.clicked.connect(lambda: self.startLSLApp("appLabRecorder"))               # LabRecorder
        self.pushButton_4.clicked.connect(lambda: self.startLSLApp("appEnobio"))                    # Enobio
        self.pushButton_5.clicked.connect(lambda: self.startLSLApp("appNirScout"))                  # NirScout
        self.pushButton_6.clicked.connect(lambda: self.startLSLApp("appNirSport"))                  # NirSport
        self.pushButton_7.clicked.connect(lambda: self.startLSLApp("appSMIRED500"))                 # SMI RED500
        self.pushButton_8.clicked.connect(lambda: self.startLSLApp("appTobiiStreamEngine"))         # Tobii Stream Engine
        self.pushButton_9.clicked.connect(lambda: self.startLSLApp("appTobiiPro"))                  # Tobii Pro
        self.pushButton_10.clicked.connect(lambda: self.startLSLApp("appSmartEye"))                 # SmartEye
        self.pushButton_11.clicked.connect(lambda: self.startLSLApp("appLiveAmp"))                  # LiveAmp
        self.pushButton_12.clicked.connect(lambda: self.startLSLApp("appEyeLink1000"))              # Eye Link
        self.pushButton_13.clicked.connect(lambda: self.startMATLABViewer("appMATLABViewer"))       # MATLAB viewer
        self.pushButton_14.clicked.connect(lambda: self.startLSLApp("appKeyboard"))                 # Keyboard
        self.pushButton_15.clicked.connect(lambda: self.startLSLApp("appMouse"))                    # Mouse
        self.pushButton_16.clicked.connect(lambda: self.startPythonPlotter("appPythonPlotter"))     # Python viewer
        self.pushButton_17.clicked.connect(lambda: self.startPythonDEViewer("appPythonDEViewer"))   # Python DE viewer
    
    def startLSLApp(self, appName):
        startApp = True
        try:
            filepath, dictKey = gui_config.getAppFilePath(appName)
            if not(path.exists(filepath)):
                QtWidgets.QMessageBox.warning(None,'Executable file not found','The executable file was not found. Please specify a correct path.',QtWidgets.QMessageBox.Ok)
                fname = QtWidgets.QFileDialog.getOpenFileName(self, 'Select executable file', '.')
                try:
                    newPath = path.relpath(str(fname[0]), getcwd())
                except ValueError:
                    newPath = str(fname[0])
            
                if newPath == '':
                    startApp = False
                else:
                    gui_config.writeConfigFileValue(appName,dictKey,newPath)
        
            if startApp is True:
                filepath = '"' + filepath + '"'
                if platform.system() == 'Darwin':       # macOS
                    p = subprocess.call(('open', filepath))
                elif platform.system() == 'Windows':    # Windows
                    p = subprocess.call('start "" ' + filepath, shell=True)
                else:                                   # linux variants
                    p = subprocess.call("./" + filepath)
        
                return p
        except KeyError:
            QtWidgets.QMessageBox.critical(None,'Error','No version of this Application for this OS was found.',QtWidgets.QMessageBox.Ok)
        
    def startMATLABViewer(self, name):
        matlab_spec = importlib.util.find_spec("matlab.engine")
        matlab_found = matlab_spec is not None
            
        if not matlab_found:
            QtWidgets.QMessageBox.critical(None,'Error','MATLAB Engine API for Python has not been found.',QtWidgets.QMessageBox.Cancel)
        else:
            from check_streams import check_cont_streams
            import matlab.engine
            availableStreams = check_cont_streams()
            
            if availableStreams == True:
                eng = matlab.engine.start_matlab()
                eng.cd(gui_config.getAppDirPath(name))
                eng.addpath(eng.genpath('../../LSL/liblsl-Matlab'))
                future = eng.vis_stream(nargout=0)
                ret = future.result()
                    
            else:
                QtWidgets.QMessageBox.critical(None,'Error','No online, continuous streams were found. Please make sure devices are correctly connected and linked.',QtWidgets.QMessageBox.Cancel)

    def startPythonPlotter(self, name):
        sys.path.append(gui_config.getAppDirPath(name))
        try:
            import plotter
            self.p = plotter.main()
        except:
            print("Window was closed.") 
                
    def startPythonDEViewer(self, name):
        sys.path.append(gui_config.getAppDirPath(name))
            
        try:
            import viewer
            self.v = viewer.main()
        except:
            print("Window was closed.") 

    def closeApp(self,process): # to close a process
        process.terminate()
 
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    window = MainGUI()
    window.show()
    sys.exit(app.exec_())
    