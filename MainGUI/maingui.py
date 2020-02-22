# -*- coding: utf-8 -*-
"""
Created on Thu Apr 11 17:04:26 2019

@author: Antonio
"""

import sys
from qtpy import QtCore, QtWidgets, uic
from pyqtgraph.Qt import QtGui
import subprocess, os, platform
import os.path
import importlib
 
qtCreatorFile = "launcher.ui" # Enter file here.
 
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)
 
class MyApp(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.pushButton.clicked.connect(lambda: self.appButtonPushed(1)) # BioSemi
        self.pushButton_2.clicked.connect(lambda: self.appButtonPushed(2)) # Faros
        self.pushButton_3.clicked.connect(lambda: self.appButtonPushed(3)) # LabRecorder
        self.pushButton_4.clicked.connect(lambda: self.appButtonPushed(4)) # Enobio
        self.pushButton_5.clicked.connect(lambda: self.appButtonPushed(5)) # NirScout
        self.pushButton_8.clicked.connect(lambda: self.appButtonPushed(8)) # Tobii Stream Engine
        self.pushButton_9.clicked.connect(lambda: self.appButtonPushed(9)) # Tobii Pro
        
        self.pushButton_12.clicked.connect(lambda: self.appButtonPushed(12)) # EyeLink
        self.pushButton_13.clicked.connect(lambda: self.appButtonPushed(13)) # MATLAB viewer
        self.pushButton_14.clicked.connect(lambda: self.appButtonPushed(14)) # Keyboard
        self.pushButton_15.clicked.connect(lambda: self.appButtonPushed(15)) # Mouse
        self.pushButton_16.clicked.connect(lambda: self.appButtonPushed(16)) # Python viewer
        self.pushButton_17.clicked.connect(lambda: self.appButtonPushed(17)) # Python DE viewer
    
    def appButtonPushed(self, appNumber):
        if (appNumber==1):
            if platform.system() == 'Linux':
                self.launchApp(os.path.join("..","Apps","BioSemi",
                               "build","BioSemi"))
                
            elif platform.system() == 'Windows':    # Windows
                self.launchApp(os.path.join("..","Apps","BioSemi",
                               "BioSemi.exe"))

        elif (appNumber==3):
            self.launchApp(os.path.join("..","OnlineProcessing","LabRecorder",
                               "build","install","LabRecorder","LabRecorder.exe"))
        elif (appNumber==2):
            self.launchApp(os.path.join("..","Apps","RTHRV_Faros",
                               "FarosLauncherGUI.py"))
        elif (appNumber==4):
            self.launchApp(os.path.join("..","Apps","Enobio",
                               "Enobio.exe"))
        elif (appNumber==5):
            self.launchApp(os.path.join("..","Apps","NirScout",
                               "ReceiveData.py"))
        elif (appNumber==8):
            self.launchApp(os.path.join("..","Apps","TobiiStreamEngine","build",
                               "Release","TobiiStreamEngine.exe"))
        elif (appNumber==9):
            self.launchApp(os.path.join("..","Apps","TobiiPro","build",
                               "install","TobiiPro","TobiiPro.exe"))
            
        elif (appNumber==12):
            self.launchApp(os.path.join("..","Apps","EyeLink",
                               "eyelink.py"))
        elif (appNumber==13):
            matlab_spec = importlib.util.find_spec("matlab.engine")
            matlab_found = matlab_spec is not None
            
            if not matlab_found:
                print("MATLAB Engine API for Python has not been found.")
            else:
                import matlab.engine
                import io
                eng = matlab.engine.start_matlab()
                eng.cd(os.path.join("..","OnlinePlotter","MATLABViewer"))
                future = eng.check_streams(background=True)
                if future.result() == 1:
                    out = io.StringIO()
                    err = io.StringIO()
                    future1 = eng.vis_stream(nargout=0,stdout=out,stderr=err)
                    ret = future1.result()
                    
                else:
                    QtWidgets.QMessageBox.critical(None,'Error','No online streams were found. Please make sure devices are correctly connected and linked.',QtWidgets.QMessageBox.Cancel)
                
                ##print (err.getvalue())
        elif (appNumber==14):
            self.launchApp(os.path.join("..","Apps","Input","build",
                               "install","Input","keyboard.exe"))
        elif (appNumber==15):
            self.launchApp(os.path.join("..","Apps","Input","build",
                               "install","Input","mouse.exe"))
        elif (appNumber==16):
            sys.path.append(os.path.join("..","OnlinePlotter","PythonViewer"))
            
            # try:
            #     import plotter
            #     self.p = plotter.main()
            # except:
            #     print("Window was closed.") 
            import plotter
            self.win = plotter.main()
                
        elif (appNumber==17):
            sys.path.append(os.path.join("..","OnlinePlotter","PythonDEViewer"))
            
            try:
                import viewer
                self.v = viewer.main()
            except:
                print("Window was closed.") 
            
        else:
            print("Hola")
            
    def launchApp(self,filepath):
        if platform.system() == 'Darwin':       # macOS
            p = subprocess.call(('open', filepath))
        elif platform.system() == 'Windows':    # Windows
            p = subprocess.call(('start', filepath), shell=True)
        else:                                   # linux variants
            p = subprocess.call("./" + filepath)
        
        return p

    def closeApp(self,process): # to close a process
        process.terminate()
 
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
    