# -*- coding: utf-8 -*-
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
import numpy as np
import os.path
import pandas as pd
# import socket
# import struct
# import sys
import threading
import time
import Tkinter as tk
import tkFileDialog as filedialog
import tkMessageBox

# Custom file dependencies:
#############################################
from ConfigGUI import ConfigGUI
# NOTE: ConfigGUI() creates another file called Config.py, which it imports
#       and reloads a couple of times. Some python interpreters may therefore
#       throw errors the first couple of times this script is run, until
#       Config.py has all its variables settled, especially if the OS is
#       running slowly and takes a long time to write that file. Sometimes it
#       is necessary to restart the interpreter, or to open and re-save
#       Config.py.

# Other variables
#############################################
stopFlag = False  # For stopping the send loop remotely from the StopGUI
fastforward = False  # For fast forwarding to the end (turning off recorded timing)
ffrate = 4000.0  # Hz. Rate at which to transmit to LSL when fast forwarding
                 # (seems stable at 5000 Hz on an i5 with 4GB RAM and numerous processes
                 # running at the same time, but it's best to be safe)
abortMsg = ("\n##=================================================##"
            "\n|| Emulator: User aborted the LSL stream emulator. ||"
            "\n##=================================================##\n")

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
def confirm(message):
    """If askConfirm flag is True, displays a message box with 'message' plus
    'Confirm?' on a new line."""
    if not tkMessageBox.askyesno("confirm", str(message) + "\n\nConfirm?"):
        print abortMsg
        exit()  # if user selects 'No', returns False, so "if not"
                # evaluates to True, so quits the Python interpretter.
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
def browseFiles():
    # Read the path from the Config file
    ConfigGUI(configDict={"filePaths": ("", "")}, readOnly=True)
    from Config import filePaths  # Import result
    print "Previous file(s):", filePaths
    if type(filePaths) == str:  # in the case of only one previous file
        filePaths = (filePaths,)

    # Get folder for previous files:
    fileDir = os.path.dirname(filePaths[0])

    # fileNames = list(filePaths)
    # for i in xrange(len(fileNames)):
    #     fileNames[i] = os.path.basename(fileNames[i])
    # print fileNames

    # Ask user to select files, giving the last used ones as default if
    # a record of them is found.
    # Use temporary variable so that, in case of cancellation, we won't lose
    # the last-used paths:
    tempPaths = filedialog.askopenfilenames(title="Please select "
                                           "recording files to stream (Cancel for last-used files)",
                                            initialdir=fileDir,
                                            # initialfile=filePaths[0],
                                            # initialfile=fileNames
                                            )

    # If no path was chosen, returns "":
    if tempPaths == "":  # noting was selected
        confirm("Continuing with last-used recording files.")
    else:  # something was selected
        filePaths = tempPaths
    # Save a record of that filePath for re-runs:
    ConfigGUI(configDict={"filePaths": (filePaths, )}, setToDefaults=True)
    # and then return the filePath for current usage:
    return filePaths
#############################################


# FUNCTION: Import ECG recording as a 1D array
#############################################
def importRecording(recordingFile, fileDelim=',', timecol=0, datacol=1):
    """Imports recordingFile and converts and returns a pandas Series for
    transmission.

    Defaults to comma-delimited csv-type file in [time, data] format,
    but these can be changed with the \"fileDelim\", \"timecol\", and
    \"datacol\" parameters (columns starting from 0)."""
    with open(recordingFile, 'rb') as file:  # Read as read-only binary
        recording = csv.reader(file, delimiter=fileDelim, quotechar='|', skipinitialspace=True)
        data = []
        time = []
        foundString = False
        for row in recording:
            try:
                data += [float(row[datacol])]
            except ValueError:
                foundString = True
                data += [str(row[datacol])]
            time += [float(row[timecol])]

        if foundString:
            dtype = str
        else:  # assume number:
            dtype = np.float32

    return pd.Series(data=data, index=time, dtype=dtype)
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

# FUNCTION: Frequency-control for a loop
#############################################
def prepareData(filePaths):
    """Pulls the data from all given file paths (to pd.Series), opens outlets
    for each stream, and identifies the earliest timestamp (t0) in all streams.
    Also names the streams according to the suffixes of the file names.

    Input: a tuple of file path strings

    Returns: (t0, list of recording series, list of outlets)"""

    # INIT:
    t0 = []
    recordings = []
    outlets = []

    # LOOP:
    for i in xrange(len(filePaths)):
        print "\n File index:  ", i
        print "       Path:  ", filePaths[i]

        """ DATA """
        recordings += [importRecording(filePaths[i])]
        print "  Recording:  ", recordings[i].dtype

        t0 += [recordings[i].index[0]]
        print " Start time:  ", t0[i], "sec"

        try:
            rate = int(1.0/(recordings[i].index[1]-recordings[i].index[0]))
        except:
            print "Less than two datapoints found"
            rate = 0
        print "Stream rate:  ", rate, "Hz (estimated)"

        """ STREAM TYPE """
        # Extract the file name by taking the last segment after a "/", then:
        # Extract type from file name by breaking at "__" and taking the
        # last bit after that, or, if no "__", then take the first bit
        # before a "_" (should be the run name). Then chop off the
        # file extension if it exists. If no "_", you should get the
        # whole file name.
        if "__" in filePaths[i]:
            streamType = filePaths[i].split("/")[-1].split("__")[-1].split(".")[0]
        else:
            streamType = filePaths[i].split("/")[-1].split("_")[0].split(".")[0]
        print "Stream type:  ", streamType

        """ OUTLET """
        # Now create a new stream info object:
        # (here we set the name to Faros, the content-type to ECG, 1 channel, frequency = rate,
        # float-valued data, and the MAC address)
        # The last value, the MAC address of the device, is a local identifier for the stream
        # (you could also omit it but interrupted connections wouldn't auto-recover).
        # streamConfig = StreamInfo('Emulator', streamType, 1, rate, 'float32', 'Emulator');
        print 'recordings[i].dtype:', recordings[i].dtype
        if recordings[i].dtype == np.float32:
            lsldtype = 'float32'
        else:
            lsldtype = 'string'
            recordings[i] = recordings[i].astype(str)  # Cast everything as strings so LSL understands
        streamConfig = StreamInfo('Emulator_' + streamType, streamType, 1, 100, lsldtype, 'Emulator_' + streamType);
        # next add an outlet to the list
        outlets += [StreamOutlet(streamConfig)]
        print "     Outlet:  ", outlets[i]

    # Extract earliest time:
    t0 = min(t0)

    return (t0, recordings, outlets)
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
        self.rootWindow = tk.Tk(className=" EMULATOR")
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

    def FFbutton(self):
        # Stop the background loop
        global fastforward
        fastforward = True
        return

    def run(self):
        # Main loop for the GUI window
        self.rootWindow.protocol("WM_DELETE_WINDOW", self.closer)

        """ BUTTONS """
        self.stopButton = tk.Button(self.rootWindow, text="STOP",
                                    font=('Helvetica', 12, "bold"),
                                    command=self.stopbutton,
                                    bd=10, bg="red3", fg="white",
                                    cursor="pirate")
        self.FFButton = tk.Button(self.rootWindow, text="FF\n>>|",
                                  font=('Helvetica', 12, "bold"),
                                  command=self.FFbutton,
                                  bd=10, bg="gray20", fg="white")
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

        """ PLACE """
        self.stopButton.pack()
        self.FFButton.pack()
        # Set up buttons:
        self.stopButton.place(width=125, height=100,
                              x=0, y=0)
        self.FFButton.place(width=75, height=100,
                              x=125, y=0)

        # Hold this window open and keep it interactive:
        self.rootWindow.mainloop()


# CLASS: Send loop for sending samples to emulate the ECG device
#############################################
def Emulator(recording, outlet, replayOffset=0):
    """Sends a packet to the LSL according to given timestamps."""
    # Initialise
    LoopInterrupted = False  # Local flag in case user interrupts send
    print "launched an emulator stream thread..."

    # global fastforward
    global stopFlag
    global interrupted

    for i in xrange(len(recording)):  # loop through items in recording
        # Allow the send loop to be interrupted at the end of a cycle:
        if not stopFlag:
            # Also check for default keyboard interrupt:
            try:
                # Break up data:
                dataPoint, t = recording.iloc[i], recording.index[i]
                # Regulate timing:
                if not fastforward:  # i.e. if FF, don't wait.
                    tTransmit = t + replayOffset  # local time at which to transmit sample
                    wait = lowclamp(tTransmit - time.time())  # time until that time arrives.
                    time.sleep(wait)  # wait for that time to arrive.
                else:  # fastforward speed
                    time.sleep(1.0/ffrate)
                    # This cannot be simply as fast as the PC can run,
                    # because then LSL drops some points.

                # Send dataPoint out to the Lab Streaming Layer (with original timestamp)
                # print dataPoint, t
                if not (type(dataPoint) is type(None)):
                    outlet.push_sample([dataPoint], t)
            except KeyboardInterrupt:  # Allow interrupt with Ctrl+C
                interrupted = True
                break
        else:
            interrupted = True
            break

    print "ended an emulator stream thread."
    return  # necessary? -- I think this ensures he program only ends after threads close...


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

"""
############################################################################
# Import files
#############################################
"""
filePaths = browseFiles()
t0, recordings, outlets = prepareData(filePaths)

"""
############################################################################
# Send Transmission
#############################################
"""
# Launch the stop button GUI
stopGUI = StopGUI()  # GUI with STOP button

# Get the time offset for the emulation from the original recordings:
replayOffset = time.time() - t0

print "\nGlobal:"
print " Recording time:  ", t0, "sec"
print "  Offset to now:  ", replayOffset, "sec"

# Call the emulator sender function in different threads:
interrupted = False  # Flag in case the user interrupted the stream instead
                     # of letting it run to completion

streams = []  # container for the various streaming threads
for i in xrange(len(recordings)):
    # Create thread
    streams += [threading.Thread(target=Emulator,
                                 args=(recordings[i],
                                       outlets[i],
                                       replayOffset)
                                 )]
    # Launch thread
    streams[i].start()

for i in xrange(len(streams)):
    streams[i].join()  # Script won't continue until all streams have closed.

if interrupted:  # Display message if user interrupted
    print "\nEmulator: User interrupted send."
    print "\n          (see pop-up message window)\n"
    tkMessageBox.showinfo("Interrupted",
                          "Emulator Stopped\n\n"
                          "The user has prematurely terminated the stream.")

# Close the stopGUI window:
stopGUI.rootWindow.quit()

"""
############################################################################
# Finish
#############################################
"""
print "          Closing connections now."
# confirm("Closing connections now")

# dprint("Emulator: FINISHED")

if not interrupted:
    tkMessageBox.showinfo("Emulator FINISHED",
                          "The Device Emulator has finished sending the\n"
                          "selected recording(s) and will now close.")

time.sleep(1)

# ...and they lived happily ever after.
#
#            ---THE END---
