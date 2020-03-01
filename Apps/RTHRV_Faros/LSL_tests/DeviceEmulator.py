# -*- coding: utf-8 -*-
# python 2.7.11
############################################################################
# Emulator that simulates an ECG machine sending to the lab streaming layer
#
# - Matthew Wilson, 2016
############################################################################
# Dependencies:
# lsl
# pylsl
# ConfigGUI.py

# Lab Streaming Layer Import
#############################################
import sys; sys.path.append('liblsl-Python') # help python find pylsl relative to this example program
from pylsl import StreamInfo, StreamOutlet

# Standard Anaconda:
#############################################
import csv
import numpy
import os.path
import socket
# import struct
# import sys
import threading
import time
import Tkinter as tk
import tkFileDialog as filedialog
import tkMessageBox

# Custom file dependencies:
#############################################
import Decoding
from ConfigGUI import ConfigGUI
# NOTE: ConfigGUI() creates another file called Config.py, which it imports
#       and reloads a couple of times. Some python interpreters may therefore
#       throw errors the first couple of times this script is run, until
#       Config.py has all its variables settled, especially if the OS is
#       running slowly and takes a long time to write that file. Sometimes it
#       is necessary to restart the interpreter, or to open and re-save
#       Config.py.

# Run/Debug parameters
#############################################

# Debug config:
# "variableName": (defaultValue, "description [optional]"), ...
# or "variableName": [defaultValue, "description [optional]"], ...
debugDict = {
             "askConfirm": (False, """Ask user to confirm the start
                                      of each major step"""),
             "askSend": (False, "Ask user to initiate sending the data"),
             "debugPrinter": (False, "Print verbose status messages"),
             "valDebugPrinter": (False, "Print sent values"),
             "simpleSTOP": (False, """Do not animate the STOP button
                                      (for slower PCs, perhaps)"""),
             }

# Network and emulator config:
# "variableName": (defaultValue, "description [optional]"), ...
# or "variableName": [defaultValue, "description [optional]"], ...
configDict = {
              "rate": (256, "Hz"),
              }

ConfigGUI("Debug options:", "Select run parameters:",
          configDict=debugDict, descWidth=160, entryWidth=6)
ConfigGUI("Network Setup:", "Enter network and ECG parameters:",
          configDict=configDict, descWidth=40)
from Config import *

if debugPrinter:
    print "rate           ", rate, "Hz", type(rate)

# Other variables
#############################################
INTERVAL = 1.0/rate  # Time between sends
stopFlag = False  # For stopping the send loop remotely from the StopGUI
Y = float(0.0)  # used for sizing the animation of the STOP button
abortMsg = ("\n##==========================================##"
            "\n|| Emulator: User aborted the ECG emulator. ||"
            "\n##==========================================##\n")

"""
############################################################################
# Functions         #####   #   #   ##   #    ####
#                   #        # #    # #  #   #
#                   ####      #     #  # #    ###
#                   #        # #    #   ##       #
#                   #       #   #   #    #   ####
############################################################################
"""


# FUNCTION: Ask user to confirm continuation if askConfirm is True
#############################################
def confirm(message, override=askConfirm):
    """If askConfirm flag is True, displays a message box with 'message' plus
    'Confirm?' on a new line.

    Optional: Override the default 'askConfirm' status to force a print."""
    if override:  # i.e. if askConfirm
        if not tkMessageBox.askyesno("confirm", str(message) + "\n\nConfirm?"):
            print abortMsg
            exit()  # if user selects 'No', returns False, so "if not"
#                     evaluates to True, so quits the Python interpretter.
#############################################


# FUNCTION: print debugging messages if debugPrinter is True
#############################################
def dprint(str):
    "If debugPrinter flag is True, prints str"
    if debugPrinter:
        print str
#############################################


# FUNCTION: print sent values if valDebugPrinter is True
#############################################
def valdprint(str):
    "If valDebugPrinter flag is True, prints str"
    if valDebugPrinter:
        print str
#############################################


# FUNCTION: Clamp input value between given values (default: [0,1])
#############################################
def clamp(n, minn=0.0, maxn=1.0):
    "Clamps n between minn (def 0.0) and maxn (def 1.0)"
    n = sorted([minn, n, maxn])[1]
    return n
#############################################


# FUNCTION: Clamp input value above given value (default: 0)
#############################################
def lowclamp(n, minn=0.0):
    "Clamps n above minn (def 0)"
    n = sorted([minn, n])[1]
    return n
#############################################


# FUNCTION: Browse for an ECG recording.
#############################################
def browseFile():
    fileDir = ""

    # Read the path from the Config file
    ConfigGUI(configDict={"filePath": ""}, readOnly=True)
    from Config import filePath  # Import (in case using a different file)
    print "Last used file:", filePath

    # Ask user to select a file, giving the last used one as default if
    # a record of it is found.
    # Use temporary variable so that, in case of cancelation, so we won't lose
    # the last-used path:
    tempPath = filedialog.askopenfilename(title="Please select an ECG "
                                          "recording file",
                                          initialdir=fileDir,
                                          initialfile=filePath
                                          )
    # If the path does not exist, is broken, or was not chosen, ask whether
    # the user wants to cancel the run or browse again:
    while not os.path.exists(tempPath):
        # Abort run if user chooses "Cancel" (returns blank)
        if not tkMessageBox.askretrycancel(title="No ECG recording selected",
                                           message="Browse again,\n"
                                           " or Cancel run?",
                                           icon="error",
                                           type="retrycancel",
                                           default="retry"):
            exit()
        else:  # Else provide browser window again...
            tempPath = filedialog.askopenfilename(title="PLEASE Select an ECG "
                                                  "recording file",
                                                  initialdir=fileDir,
                                                  initialfile=filePath
                                                  )
    # If we get this far, then a path has been selected, so can be stored:
    filePath = tempPath
    # Save a record of that filePath for re-runs:
    ConfigGUI(configDict={"filePath": filePath}, setToDefaults=True)
    # and then return the filePath for current usage:
    return filePath
#############################################


# FUNCTION: Import ECG recording as a 1D array
#############################################
def importRecording(recordingFile, fileDelim=',', column=1):
    """Imports recordingFile and converts and returns 1D array for
    transmission.

    Defaults to comma-delimited csv-type file with values in the second
    column, but these can be changed with \"fileDelim\" and \"column\"
    parameters (columns starting from 0)."""
    with open(recordingFile, 'rb') as ECGfile:  # Read as read-only binary
        ECGrecording = csv.reader(ECGfile, delimiter=fileDelim, quotechar='|')
        ECGrecording = numpy.asarray([float(row[column])
                                     for row in ECGrecording])
        # for row in ECGrecording:
        #     print row
    return ECGrecording
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
        self.rootWindow = tk.Tk(className=" STOP")
        # Position the window on the screen:
        w = 200  # width for the window
        h = 100  # height for the window
        # get screen width and height
        ws = self.rootWindow.winfo_screenwidth()  # width of the screen
        hs = self.rootWindow.winfo_screenheight()  # height of the screen
        # calculate centre x and y coordinates
        x = (2*ws/3) - (w/2)
        y = (3*hs/4) - (h/2)
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
        # Stop the background loop
        global stopFlag
        stopFlag = True
        # Quit window
        self.rootWindow.quit()

    def run(self):
        # Main loop for the GUI window
        self.rootWindow.protocol("WM_DELETE_WINDOW", self.closer)

        # self.button = tk.Button(self.rootWindow, text="STOP",
        #                         command=self.stopbutton,
        #                         bd=5, bg="red", fg="white")
        self.stopButton = tk.Button(self.rootWindow, text="STOP HEART",
                                    font=('Helvetica', 12, "bold"),
                                    command=self.stopbutton,
                                    bd=10, bg="red3", fg="white",
                                    cursor="pirate")
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

        self.stopButton.pack()
        self.updateLoop()
        # Just in case the loop accidentally exits:
        self.rootWindow.mainloop()

    def updateLoop(self):
        # Update buttone Y-position:
        xScale = 4
        yScale = 2
        self.stopButton.place(width=xScale*self.Y, height=yScale*self.Y,
                              x=100-xScale*self.Y/2, y=50-yScale*self.Y/2)
        # Update at 60Hz:
        self.rootWindow.after(int(1000/60), self.updateLoop)


# CLASS: Send loop for sending packets to emulate the ECG device
#############################################
class ECGEmulator(threading.Thread):
    """Sends a packet to the LSL at a regulated frequency."""
    def __init__(self):
        # Initialise
        self.LoopInterrupted = False  # Local flag in case user interrupts send
        self.count = long(0)  # start counter index from 0

        threading.Thread.__init__(self)
        self.start()

    def interruptSend(self):
        print "\nEmulator: User interrupted send."
        print "\n          (see pop-up message window)\n"
        self.LoopInterrupted = True  # Flag that user interrupted
        return self.LoopInterrupted

    def start(self):
        global stopFlag
        # global Y
        self.prev = time.time()  # "previous" time value for use in loop
        self.start = time.time()  # for frequency check at end
        for dataPoint in ECGrecording:  # loop through items in ECGrecording
            # Allow the send loop to be interrupted at the end of a cycle:
            if not stopFlag:
                # Also check for default keyboard interrupt:
                try:
                    # Regulate frequency:
                    self.count, self.prev = freqRegulate(self.count,
                                                         INTERVAL,
                                                         self.prev)

                    # Send dataPoint out to the Lab Streaming Layer
                    outlet.push_sample([dataPoint])

                    # Update the STOP button size:
                    if not simpleSTOP:
                        stopGUI.Y = int((10*stopGUI.Y +
                                         50+(25*dataPoint))/11)
                except KeyboardInterrupt:  # Allow interrupt with Ctrl+C
                    self.LoopInterrupted = self.interruptSend()
                    break
            else:
                self.LoopInterrupted = self.interruptSend()
                break
        self.end = time.time()
        """
        HOW DO YOU FORCE THIS NEXT WINDOW ON TOP ?!
        """
        if self.LoopInterrupted:  # Display message if user interrupted
            tkMessageBox.showinfo("Interrupted",
                                  "Heart Stopped\n\n"
                                  "\"It's just a flesh wound!\"\n\n"
                                  "But it would seem the user has prematurely"
                                  "\nterminated the virtual heart and the\n"
                                  "ECG emulator must therefore now stop its\n"
                                  "transmission.")
        dprint("Emulator: "
               "Sent with avg. frequency of " + format(self.count /
                                                       (self.end -
                                                        self.start)) +
               " Hz.")
        return  # necessary?

"""
############################################################################
# Main              #     #     #     #   ##   #
#                   ##   ##    # #    #   # #  #
#                   # # # #   #   #   #   #  # #
#                   #  #  #   #####   #   #   ##
#                   #     #   #   #   #   #    #
############################################################################
"""
"""
############################################################################
# General Setup
#############################################
"""
############################################################################
# Create background window for messages
#############################################
rootWindow = tk.Tk()
rootWindow.wm_withdraw()                 # Hide host window

confirm("Starting ProComp ECG emulator at " + str(rate) + " Hz.")
# Display chosen sample rate
dprint("Emulator: Data rate: " + format(rate) + " Hz,\n\
        at intervals of " + format(INTERVAL) + " seconds.")
############################################################################
# Import file to array
#############################################
filePath = browseFile()
print "Emulator: Importing recorded ECG session now"
confirm("Emulator: Importing recorded ECG session now")
ECGrecording = importRecording(filePath)
print "Emulator: ECG session imported"


print "Emulator: Connecting now"
confirm("Emulator: Establishing connection now", True)
"""
############################################################################
# Connect
#############################################
"""

# first create a new stream info
# (here we set the name to Faros, the content-type to ECG, 1 channel, frequency = rate,
# float-valued data, and the MAC address)
# The last value, the MAC address of the device, is a local identifier for the stream
# (you could also omit it but interrupted connections wouldn't auto-recover).
streamConfig = StreamInfo('Faros','ECG',1,rate,'float32','AA:BB:CC:11:22:33');
# next make an outlet
outlet = StreamOutlet(streamConfig)

"""
############################################################################
# Send Transmission
#############################################
"""
# debug
dprint('Emulator: Sending to LSL...')


# Call the frequency-controlled emulator sender class and GUI:
stopGUI = StopGUI()  # GUI with STOP button
emulator = ECGEmulator()        # Actual send class (loop)

stopGUI.rootWindow.quit()

# debug
dprint("Emulator: Sending complete")

"""
############################################################################
# Finish
#############################################
"""
print "        Closing connections now"
confirm("Closing connections now")

dprint("Emulator: FINISHED")

tkMessageBox.showinfo("Emulator FINISHED",
                      "The Device Emulator has finished sending the\n"
                      "selected ECG recording and will now close.")

# ...and they lived happily ever after.
#
#            ---THE END---
