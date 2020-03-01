# -*- coding: utf-8 -*-
###############################################################################
#
# license info here...
#
###############################################################################

# Lab Streaming Layer Import
#############################################
import sys; sys.path.append('liblsl-Python') # help python find pylsl relative to this example program
# from pylsl import StreamInlet, resolve_stream, StreamInfo, StreamOutlet, local_clock

# Standard Anaconda:
#############################################
# import csv
# from datetime import datetime
# import matplotlib
# import matplotlib.pyplot as plt
# from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# from matplotlib.backends.backend_tkagg import NavigationToolbar2TkAgg
import multiprocessing
# import numpy as np
import os
import os.path
# import pandas as pd
import psutil
# import re
# import socket
# import struct
from subprocess import call
# import sys
import threading
import time
import Tkinter as tk
# import tkinter as tk  # Py3.5
# import tkFileDialog as filedialog
# from tkinter import filedialog  # Py3.5
import tkMessageBox
# import tkinter.messagebox as tkMessageBox  # Py3.5
# Custom file dependencies:
#############################################
# import Decoding
from ConfigGUI import ConfigGUI
# NOTE: ConfigGUI() creates another file called Config.py, which it imports
#       and reloads a couple of times. Some python interpreters may therefore
#       throw errors the first couple of times this script is run, until
#       Config.py has all its variables settled, especially if the OS is
#       running slowly and takes a long time to write that file. Sometimes it
#       is necessary to restart the interpreter, or to open and re-save
#       Config.py.
# from LivePlotting_Process import livePlotting
# from RPeakDetectLive import detect_beats

# # For live plotting in Tkinter, ensure matplotlib plots in Tkinter:
# #############################################
# matplotlib.use('TkAgg')

"""
###########################################################################
# Initialise        ###   ##   #   ###   #####
#                    #    # #  #    #      #
#                    #    #  # #    #      #
#                    #    #   ##    #      #
#                   ###   #    #   ###     #
###########################################################################
"""
# RUN/DEBUG VARIABLES
#############################################
# Config dictionary entries in format:
# "variableName": (defaultValue, "description [optional]"), ...
# or "variableName": [defaultValue, "description [optional]"], ...

farosDict = {
              # "--help": (True, """show this help message and exit"""),
              # "--scan": (True, """Scan for available Bluetooth devices."""),
              # "--blink": (True, """Blink the lights of a device."""),
              # "device-list": ("file.txt", """File containing the names and bluetooth addresses of
              #                                devices. Create using --scan and pipe the output to a
              #                                file."""),
              "Faros_MAC": ("EC:FE:7E:16:09:C2", """Bluetooth MAC address."""),
              # "name": ("FAROS-1520085", """Bluetooth device name."""),
              # "--show-settings": (True, """Get the settings of a device"""),
              # "--sync-time": (True, """Synchronise device time."""),
              # "--configure": (True, """Configure the device."""),
              "ecg_n": (1, """Number of ECG channels (1 or 3)."""),
              "rate": (500, """ECG sampling rate in Hz (0, 100, 125, 250, 500, 1000)."""),
              "ecg_res": (1, """ECG resolution in uV / count (0.25 uV or 1 uV)."""),
              "ecg_hp": (10, """ECG highpass filter in Hz (1 Hz or 10 Hz)."""),
              "acc_rate": (100, """Acc sampling rate in Hz (0, 20, 25, 40, 50, 100)"""),
              "acc_res": (1, """Acc resolution in mg / count (0.25 uV or 1 uV)"""),  # TODO: ConfigGUI not saving floats, so not saving '0.25' correctly
              "stream_RR": (1, """Record RR interval (0 = no, 1 = yes)"""),
              "stream_Temp": (1, """Record temperature (0 = no, 1 = yes)"""),
              # "--stream": (True, """Start streaming data."""),
              "stream_prefix": ("Faros", """LSL stream name prefix. Default is empty string.""")
             }

# DEFINE VARIABLES (set them in __main__)
#############################################
ConfigGUI(configDict=farosDict, readOnly=True)
from Config import *

# GLOBAL VARIABLES
#############################################
abortMsg = ("\n##==============================================##"
            "\n|| Client: User aborted the ProComp ECG client. ||"
            "\n##==============================================##\n")
"""
###############################################################################
# Functions         #####   #   #   ##   #    ####
#                   #        # #    # #  #   #
#                   ####      #     #  # #    ###
#                   #        # #    #   ##       #
#                   #       #   #   #    #   ####
###############################################################################
"""

"""############################################################################
# UTILITY FUNCTIONS
############################################################################"""


# FUNCTION: Clamp input value above given value (default: 0)
#############################################
def finish():

    # And then the somewhat violent end (There must be a better way...):
    procCount = 1
    hostProc = psutil.Process(os.getpid())
    # print "hostProc:", hostProc
    subProcs = hostProc.children(recursive=True)
    for subProc in subProcs:
        procCount += 1
        # print "subProc:", subProc
        subProc.kill()
    psutil.wait_procs(subProcs, timeout=5)
    print ("Terminated %i main process(es)." % procCount)

    print ("*** FIN ***")

    hostProc.kill()
    hostProc.wait(5)
#############################################


# FUNCTION: Clamp input value above given value (default: 0)
#############################################
def lowclamp(n, minn=0.0):
    "Clamps n above minn (def 0)"
    n = sorted([minn, n])[1]
    return n
#############################################


# FUNCTION: Frequency-control for a loop
#############################################
def freqRegulate(count, interval, prev):
    """Iterates and regulates the frequency of execution of a while loop by
    waiting for the clock to reach the next allowable execution tick
    ("interval"). NOTE: if the previous iteration of the loop ever takes
    longer to run than "interval", this will execute immediately, potentially
    breaking synchronicity if that is your objective.
    * INPUTS:
    count => value for counter
    interval => time interval at which to execute (inverse of frequency)
    prev => previous tick (should start at loop start time)
    * RETURNS:
    count => updated counter
    prev => updated previous tick (for next iteration)"""
    nxt = prev + interval
    wait = lowclamp(nxt - time.time())  # Set time until next interval
    time.sleep(wait)                    # wait for that next interval
    prev = nxt         # update
    count = count + 1   # update
    return (count, prev)
#############################################


# FUNCTION: Update lWindow
#############################################
def listCycle(x, list):
    """Append x to list and maintain length.
    Returns updated list."""
    list.append(x)  # append new value
    # list.pop(0)     # get rid of first value (to maintain size)
    del list[0]  # get rid of first value (to maintain size)
    return list
#############################################

"""############################################################################
# DISPLAY FUNCTIONS
############################################################################"""


# FUNCTION: print debugging messages if debugPrinter is True
#############################################
def dprint(str):
    "If debugPrinter flag is True, prints str"
    if debugPrinter:
        print (str)
#############################################


# FUNCTION: Ask user to confirm continuation if clientAskConfirm is True
#############################################
def confirm(message, override=clientAskConfirm, noexit=False):
    """If clientAskConfirm flag is True, displays a message box with 'message' plus
    'Confirm?' on a new line. Returns True if user clicks 'Okay', terminates
    the script if the user clicks 'Cancel' (unless noexit=True in which case
    returns False).

    Optional:
    override: Overrides the default 'clientAskConfirm' status to force a print.
    noexit: do not exit on 'Cancel'."""
    if override:  # i.e. if clientAskConfirm
        if not tkMessageBox.askyesno("confirm", str(message) + "\n\nConfirm?"):
            print (abortMsg)
            if noexit:
                return False
            else:
                finish()
        else:
            return True
#############################################


# FUNCTION: Display an information dialogue box (and pause)
#############################################
def dispInfo(message, condition=True):
    """If clientAskConfirm flag is True, displays a message box with 'message'
    plus 'Confirm?' on a new line.

    Optional: tie to a condition (like clientAskConfirm) to suppress a print.
    """
    if condition:  # i.e. if clientAskConfirm
        tkMessageBox.showinfo("Info", str(message))
#############################################


# FUNCTION: Display an warning dialogue box (and pause)
#############################################
def dispWarn(message, condition=True):
    """If clientAskConfirm flag is True, displays a message box with 'message'
    plus 'Confirm?' on a new line.

    Optional: tie to a condition (like clientAskConfirm) to suppress a print.
    """
    if condition:  # i.e. if clientAskConfirm
        tkMessageBox.showwarning("Warning", str(message))
#############################################



"""
############################################################################
# Classes           ####   #        #     ####   ####  #####   ####
#                  #    #  #       # #   #      #      #      #
#                  #       #      #   #   ###    ###   #####   ###
#                  #    #  #      #####      #      #  #          #
#                   ####   #####  #   #  ####   ####   #####  ####
############################################################################
"""

# CLASS: GUI for interrupting the send
#############################################
class StopGUI(threading.Thread):

    def __init__(self):
        # Initialise
        self.rootWindow = tk.Tk(className="\nECGProc")
        # Position the window on the screen:
        w = 200  # width for the window
        # w = 400  # width for the window
        h = 100  # height for the window
        # get screen width and height
        ws = self.rootWindow.winfo_screenwidth()  # width of the screen
        hs = self.rootWindow.winfo_screenheight()  # height of the screen
        # calculate centre x and y coordinates
        x = (1 * ws / 3) - (w / 2)
        y = (3 * hs / 4) - (h / 2)
        # set the dimensions of the window and where it is placed
        self.rootWindow.geometry("%dx%d+%d+%d" % (w, h, x, y))
        self.rootWindow.minsize(width=w, height=h)
        self.rootWindow.maxsize(width=w, height=h)  # lock size

        self.rootWindow.configure(bg="grey5")
        # self.rootWindow.iconbitmap(default=ICO_PATH)  # point to blank icon
        self.Y = int(50)
        self.YLast = int(50)

        threading.Thread.__init__(self)
        self.start()

    def closer(self):
        # Stop the background loop
        global stopFlag
        stopFlag = True
        # Quit window
        self.rootWindow.quit()

    def stopbutton(self):
        self.closer()

    def markerbutton(self):
        global marker
        marker = "Event"
        print ("Marker logged:", marker)
        return

    def run(self):
        # Main loop for the GUI window
        self.rootWindow.protocol("WM_DELETE_WINDOW", self.closer)

        # self.button = tk.Button(self.rootWindow, text="STOP",
        #                         command=self.stopbutton,
        #                         bd=5, bg="red", fg="white")
        self.stopButton = tk.Button(self.rootWindow, text="STOP \n(inactive)",
                                    font=('Helvetica', 12, "bold"),
                                    command=self.stopbutton,
                                    bd=10, bg="red3", fg="white",
                                    cursor="pirate")
        # self.markerButton = tk.Button(self.rootWindow, text="SET MARKER",
        #                               font=('Helvetica', 12, "bold"),
        #                               command=self.markerbutton,
        #                               bd=10, bg='#b0c050', fg="white")

        self.stopButton.pack(side="left")
        # self.markerButton.pack(side="right")

        # Bind the "Escape" and "Ctrl-c" key commands to the STOP button when
        # the window is in focus.
        self.rootWindow.bind('<Escape>', (lambda esc,
                                          b=self.stopButton:
                                          self.stopButton.invoke()))
        # self.rootWindow.bind('<Return>', (lambda esc,
        #                                   b=self.stopButton:
        #                                   self.stopButton.invoke()))
        self.rootWindow.bind('<Control-c>', (lambda esc,
                                             b=self.stopButton:
                                             self.stopButton.invoke()))

        # # Bind the space bar to the marker button when the window is in focus.
        # self.rootWindow.bind('<space>', (lambda esc,
        #                                  b=self.markerButton:
        #                                  self.markerButton.invoke()))

        # Bring window into focus to make use of those key bindings:
        self.rootWindow.update()
        self.rootWindow.deiconify()

        # Animated or static STOP button:
        # global simpleSTOP
        # if not simpleSTOP:
        #     # Animated
        #     self.updateLoop()
        # else:
        #     # Static
        xScale = 4
        yScale = 2
        self.stopButton.place(width=xScale * self.Y,
                              height=yScale * self.Y,
                              x=100 - xScale * self.Y / 2,
                              y=50 - yScale * self.Y / 2)
        # Just in case the loop accidentally exits:
        self.rootWindow.mainloop()
    #
    # def updateLoop(self):
    #     # Update button Y-position:
    #     xScale = 4
    #     yScale = 2
    #     self.stopButton.place(width=xScale * self.Y,
    #                           height=yScale * self.Y,
    #                           x=100 - xScale * self.Y / 2,
    #                           y=50 - yScale * self.Y / 2)
    #     # Update at 60Hz:
    #     self.rootWindow.after(int(1000 / 60), self.updateLoop)


"""
###############################################################################
# Main              #     #     #     #   ##   #
#                   ##   ##    # #    #   # #  #
#                   # # # #   #   #   #   #  # #
#                   #  #  #   #####   #   #   ##
#                   #     #   #   #   #   #    #
###############################################################################
"""
if __name__ == '__main__':  # Have to do this for multiprocessing :/
    """Main script to run after initialisation."""

    """
    ###########################################################################
    # General Setup
    #############################################
    """
    # Only display the setup dialogue boxes in the main process:
    if ("_MainProcess" in str(multiprocessing.current_process())):
        # Set custom variables:
        #############################################
        ConfigGUI("Faros Setup", "Enter Faros device parameters:",
                  configDict=farosDict, descWidth=350, entryWidth=17)
        from Config import *

    else:
        ConfigGUI(configDict=farosDict, readOnly=True)
        from Config import *

    ###########################################################################
    # Create background window for further messages
    #############################################
    rootWindow = tk.Tk()
    rootWindow.wm_withdraw()                 # Hide host window

    # stopFlag = False
    # stopGUI = StopGUI()  # GUI with STOP button
    stopFlag = True

    # Blink to test:
    call(['faros',
          '--mac', Faros_MAC,
          '--blink'])
    # Configure device:
    call(['faros',
          '--mac', Faros_MAC,
          # '--sync-time',
          '--configure',
          '--ecg-n', str(ecg_n),
          '--ecg-fs', str(rate),
          '--ecg-res', str(ecg_res),
          '--ecg-hp', str(ecg_hp),
          '--acc-fs', str(acc_rate),
          '--acc-res', str(acc_res),
          '--rr', str(stream_RR),
          '--temp', str(stream_Temp)])
    # # Sync device clock to computer:
    # call(['faros',
    #       '--mac', Faros_MAC,
    #       '--sync-time'])
    # Show that it is configured:
    call(['faros',
          '--mac', Faros_MAC,
          '--show-settings'])
    # Stream:
    call(['faros',
          '--mac', Faros_MAC,
          '--stream',
          '--stream-prefix', stream_prefix])


    # farosDict = {
    #     # "--help": (True, """show this help message and exit"""),
    #     # "--scan": (True, """Scan for available Bluetooth devices."""),
    #     # "--blink": (True, """Blink the lights of a device."""),
    #     # "device-list": ("file.txt", """File containing the names and bluetooth addresses of
    #     #                                devices. Create using --scan and pipe the output to a
    #     #                                file."""),
    #     "Faros_MAC": ("EC:FE:7E:16:09:C2", """Bluetooth MAC address."""),
    #     # "name": ("FAROS-1520085", """Bluetooth device name."""),
    #     # "--show-settings": (True, """Get the settings of a device"""),
    #     # "--sync-time": (True, """Synchronise device time."""),
    #     # "--configure": (True, """Configure the device."""),
    #     "ecg_n": (1, """Number of ECG channels (1 or 3)."""),
    #     "rate": (500, """ECG sampling rate in Hz (0, 100, 125, 250, 500, 1000)."""),
    #     "ecg_res": (1, """ECG resolution in uV / count (0.25 uV or 1 uV)."""),
    #     "ecg_hp": (10, """ECG highpass filter in Hz (1 Hz or 10 Hz)."""),
    #     "acc_rate": (100, """Acc sampling rate in Hz (0, 20, 25, 40, 50, 100)"""),
    #     "acc_res": (0.25, """Acc resolution in mg / count (0.25 uV or 1 uV)"""),
    #     "stream_RR": (1, """Record RR interval (0 = no, 1 = yes)"""),
    #     "stream_Temp": (1, """Record temperature (0 = no, 1 = yes)"""),
    #     # "--stream": (True, """Start streaming data."""),
    #     "stream_prefix": ("Faros", """LSL stream name prefix. Default is empty string.""")
    # }

    # }
    while not stopFlag:
        time.sleep(0.1)

    # call(['q'])  # quit the stream

    """
    ###########################################################################
    # FINISH
    #############################################
    """

    print ("Arrived at end of script successfully.")
    finish()

    # And they all lived happily ever after.
    #              THE END
