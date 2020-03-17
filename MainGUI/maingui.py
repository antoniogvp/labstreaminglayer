# -*- coding: utf-8 -*-
"""
Created on Thu Apr 11 17:04:26 2019

@author: Antonio
"""

import sys
from qtpy import QtWidgets
import subprocess, platform
import gui_config
from os import path, getcwd
from pathlib import PurePath
from functools import partial
 
class MainGUI(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainGUI,self).__init__()
        data = gui_config.readConfigFile()
        
        groups = ["Application Launcher", "Recording/processing tools",
                  "Viewer Tools", "Test tools", "Undefined"]
        groupsShort = ["app", "process_record", "viewer", "test"]
        
        layoutList = []
        boxList = []
        [layoutList.append(QtWidgets.QGridLayout()) for n in range(len(groups))]
        [boxList.append(QtWidgets.QGroupBox(groups[n])) for n in range(len(groups))]
        mainbox = QtWidgets.QVBoxLayout()
        
        for app_id, app_info in data.items():
            b = QtWidgets.QPushButton(app_info["name"])
            b.setFixedWidth(200)
            if app_info["func"] == "default":
                b.clicked.connect(partial(self.startLSLApp, app_id))
            else:
                b.clicked.connect(partial(getattr(self,app_info["func"]), app_id))
                
            try:
                nb = layoutList[groupsShort.index(app_info["group"])].count()
                layoutList[groupsShort.index(app_info["group"])].addWidget(b, int(nb/3), nb%3)
                
            except ValueError:
                nb = layoutList[4].count()
                layoutList[4].addWidget(b, int(nb/3), nb%3)
                
        for layout, box in zip(layoutList, boxList):
            box.setLayout(layout)
            
            if layout.count()>0:
                mainbox.addWidget(box)
                
        self.setCentralWidget(QtWidgets.QWidget(self))
        self.centralWidget().setLayout(mainbox)
        
        self.setWindowTitle("LSL Application Launcher")
        self.setFixedSize(self.sizeHint().width(),self.sizeHint().height())
       
        self.show() 
    
    def startLSLApp(self, appName):
        p = None
        startApp = True
        try:
            filepath, dictKey = gui_config.getAppFilePath(appName)
            if not(path.exists(filepath)):
                QtWidgets.QMessageBox.warning(None,'Executable file not found','The executable file was not found. Please specify a correct path.',QtWidgets.QMessageBox.Ok)
                fname = QtWidgets.QFileDialog.getOpenFileName(self, 'Select executable file', '.')
                try:
                    newPath = PurePath(path.relpath(str(fname[0]), getcwd())).as_posix()
                except ValueError:
                    newPath = PurePath(str(fname[0])).as_posix()
            
                if newPath == '.':
                    startApp = False
                else:
                    gui_config.writeConfigFileValue(appName,dictKey,newPath)
                    
                filepath = newPath
        
            if startApp is True:
                if platform.system() == 'Darwin':       # macOS
                    if filepath[-3:] == ".py":
                        cmd = r'directory=$(pwd); osascript -e "tell app \"terminal\" to do script \"cd $directory; python ' + filepath + r'\""'
                        p = subprocess.call(cmd, shell=True)
                    else:
                        cmd = r'directory=$(pwd); osascript -e "tell app \"terminal\" to do script \"cd $directory; open ' + filepath + r'\""'
                        p = subprocess.call(cmd, shell=True)
                elif platform.system() == 'Windows':    # Windows
                    filepath = '"' + filepath + '"'
                    p = subprocess.call('start "" ' + filepath, shell=True)
                else:                                   # linux variants
                    if filepath[-3:] == ".py":
                        p = subprocess.call(['gnome-terminal -- python ' + filepath], shell=True)
                    else:
                        p = subprocess.call("./" + filepath)
        
                return p
        except KeyError:
            QtWidgets.QMessageBox.critical(None,'Error','No version of this Application for this OS was found.',QtWidgets.QMessageBox.Ok)
              
    def closeApp(self,process): # to close a process
        process.terminate()
 
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    window = MainGUI()
    #window.show()
    sys.exit(app.exec_())
    
