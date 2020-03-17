# -*- coding: utf-8 -*-
"""
Created on Fri Feb 28 16:51:05 2020

@author: Antonio
"""

import json, platform

def readConfigFile():
    try:
        with open('config.json') as json_data_file:
            data = json.load(json_data_file)
            return data
    
    except IOError:
        print("WARNING: No configuration file was found. Creating default file.")
        createDefaultConfigFile()
        readConfigFile()
        
    except (json.JSONDecodeError, TypeError):
        print("WARNING: Unreadable configuration file. Creating default file.")
        createDefaultConfigFile()
        readConfigFile()
        
def writeConfigFileValue(app,field,value):
    try:
        data = readConfigFile()
        data[app][field] = value
        with open('config.json', 'w') as outfile:
            json.dump(data, outfile, indent=4)
    
    except IOError:
        print("WARNING: No configuration file was found. Creating default file.")
        createDefaultConfigFile()
        writeConfigFileValue(app,field,value)
        
def getAppFilePath(appName):
    data = readConfigFile()
    filepath = None
    dictKey = None
    if "path" in data[appName]:
        filepath = data[appName]["path"]
        dictKey = "path"
    else:
        if platform.system() == 'Darwin':       # macOS
            filepath = data[appName]["macpath"]
            dictKey = "macpath"
        elif platform.system() == 'Windows':    # Windows
            filepath = data[appName]["winpath"]
            dictKey = "winpath"
        else:                                   # linux variants
            filepath = data[appName]["linpath"]
            dictKey = "linpath"
    return filepath, dictKey

def getAppDirPath(appName):
    data = readConfigFile()
    dirpath = None
    if "dirpath" in data[appName]:
        dirpath = data[appName]["dirpath"]
    else:
        print("Key was not found.")
    return dirpath
        
def createDefaultConfigFile():
    data = {
        "appBioSemi": {
            "linpath": "../Apps/BioSemi/build/BioSemi",
            "winpath": ".",
            "name": "BioSemi",
            "group": "app",
            "func": "default"
        },
        "appFaros": {
            "path": "../Apps/RTHRV_Faros/FarosLauncherGUI.py",
            "name": "Faros",
            "group": "app",
            "func": "default"
        },
        "appEnobio": {
            "winpath": "C:/Program Files (x86)/Neuroelectrics/NIC2/NIC2.exe",
            "linpath": "",
            "name": "Enobio",
            "group": "app",
            "func": "default"
        },
        "appLiveAmp": {
            "linpath": "",
            "winpath": "",
            "name": "LiveAmp",
            "group": "app",
            "func": "default"
        },
        "appNirScout": {
            "path": "../Apps/NirScout/ReceiveData.py",
            "name": "NirScout",
            "group": "app",
            "func": "default"
        },
        "appNirSport": {
            "linpath": "",
            "winpath": "",
            "name": "NirSport",
            "group": "app",
            "func": "default"
        },
        "appSMIRED500": {
            "linpath": "",
            "winpath": "",
            "name": "SMI RED5000",
            "group": "app",
            "func": "default"
        },
        "appEyeLink1000": {
            "path": "../Apps/EyeLink/eyelink.py",
            "name": "Eye Link 1000",
            "group": "app",
            "func": "default"
        },
        "appTobiiStreamEngine": {
            "linpath": "",
            "winpath": "../Apps/TobiiStreamEngine/build/Release/TobiiStreamEngine.exe",
            "name": "Tobii Stream Engine",
            "group": "app",
            "func": "default"
        },
        "appTobiiPro": {
            "linpath": "",
            "winpath": "../Apps/TobiiPro/build/install/TobiiPro/TobiiPro.exe",
            "name": "Tobii Pro",
            "group": "app",
            "func": "default"
        },
        "appSmartEye": {
            "path": "../Apps/EyeLink/eyelink.py",
            "name": "SmartEye",
            "group": "app",
            "func": "default"
        },
        "appLabRecorder": {
            "linpath": "",
            "winpath": "../OnlineProcessing/LabRecorder/build/install/LabRecorder/LabRecorder.exe",
            "name": "Lab Recorder",
            "group": "process_record",
            "func": "default"
        },
        "appMATLABViewer": {
            "path": "../OnlinePlotter/MATLABViewer/matlab_viewer_launch.py",
            "name": "MATLAB Viewer",
            "group": "viewer",
            "func": "default"
        },
        "appPythonPlotter": {
            "path": "../OnlinePlotter/PythonPlotter/plotter.py",
            "name": "Python Plotter",
            "group": "viewer",
            "func": "default"
        },
        "appPythonDEViewer": {
            "path": "../OnlinePlotter/PythonViewer/viewer.py",
            "name": "Discrete Event Viewer",
            "group": "viewer",
            "func": "default"
        },
        "appKeyboard": {
            "linpath": "",
            "winpath": "../Apps/Input/build/install/Input/keyboard.exe",
            "name": "Keyboard Input",
            "group": "test",
            "func": "default"
        },
        "appMouse": {
            "linpath": "",
            "winpath": "../Apps/Input/build/install/Input/mouse.exe",
            "name": "Mouse Input",
            "group": "test",
            "func": "default"
        },
        "pythonScripts": {
            "path": "../Apps/PythonScripts/python_scripts.py",
            "name": "Python example scripts",
            "group": "test",
            "func": "default"
        }
    }
    
    with open('config.json', 'w') as outfile:
        json.dump(data, outfile, indent=4)
    print("Default configuration file was successfully created.")
        
        