# -*- coding: utf-8 -*-
###############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#    for any questions or remarks, contact : Matt Wilson: minvertedm at
#    gmail dot com
#    version 0.1
#
###############################################################################

# Lab Streaming Layer Import
#############################################
import sys; sys.path.append('liblsl-Python') # help python find pylsl relative to this example program
from pylsl import StreamInlet, resolve_stream, StreamInfo, StreamOutlet, local_clock

# Standard Anaconda:
#############################################
import csv
from datetime import datetime
# import matplotlib
# import matplotlib.pyplot as plt
# from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# from matplotlib.backends.backend_tkagg import NavigationToolbar2TkAgg
import multiprocessing
import numpy as np
import os
import os.path
import pandas as pd
import psutil
# import re
import socket
# import struct
import sys
import threading
import time
import Tkinter as tk
# import tkinter as tk  # Py3.5
import tkFileDialog as filedialog
# from tkinter import filedialog  # Py3.5
import tkMessageBox
# import tkinter.messagebox as tkMessageBox  # Py3.5
# Custom file dependencies:
#############################################
import Decoding
from ConfigGUI import ConfigGUI
# NOTE: ConfigGUI() creates another file called Config.py, which it imports
#       and reloads a couple of times. Some python interpretters may therefore
#       throw errors the first couple of times this script is run, until
#       Config.py has all its variables settled, especially if the OS is
#       running slowly and takes a long time to write that file. Sometimes it
#       is necessary to restart the inerpretter, or to open and re-save
#       Config.py.
# from LivePlotting_Process import livePlotting
from LivePlotting_Process_Lonely import livePlotting
from RPeakDetectLive import detect_beats

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
signalDict = {"noNetwork": (False, """Emulate the server locally to this
                                      script, without any network
                                      usage."""),
              "rate": (256, "Hz (ECG hardware)"),
              "processing_rate": (5, "Hz"),
              "plot_rate": (10, """Hz. Plot process polling rate
                                   (strictly > processing_rate)"""),
              "procWindowTime": (3, "sec"),
              "noPlot": (False, """Do not run the live plot process."""),
              "debugRun": (False, """Show debug configuration
                                     (after this window).""")
              }
debugDict = {"clientAskConfirm": (False, """Ask user to confirm the start
                                            of each major step."""),
             "debugPrinter": (False, "Print verbose status messages"),
             "recDebugPrinter": (False, "Print received values."),
             "debugRepetitions": (False, """Print a counter for every time
                                            a duplicate packet is received.
                                            """),
             "simpleSTOP": (False, """Do not animate the STOP button."""),
             "writeOutput": (True, """Write received values to a
                                      time-stamped text file.""")
             }

# WRITE-TO-FILE VARIABLES
#############################################
writeDict = {"TimeColumn": (True, """Timestamps. (If no other column selected,
                                     this will be enabled by default)"""),
             "ECGColumn": (True, """ECG stream up to last detected peak."""),
             "PeakColumn": (True, """Detected peaks (= ECG value at
                            time of peak)."""),
             "RRColumn": (True, """R-R Intervals (seconds)."""),
             "HRColumn": (True, """Heart rate (BPM)."""),
             "write_header": (True, """Include a column-label header."""),
             "SeparateECGFile": (True, """Write a separate file of the received
                                  ECG stream (if the main file is not ECG-only
                                  already)."""),
             "write_type": ("csv", """Filetype extension for output
                                      file (without '.').""")
             }

# # NETWORK VARIABLES
# #############################################
# configDict = {"TCP_Host": "localhost",
#               "TCP_Port": 1000,
#               "TCPtimeout": (1, "sec"),
#               "UDP_ClientIP": "localhost",
#               "UDP_ClientPort": 1001,
#               "UDPConnectTimeout": [1, "sec"],
#               "UDPReceiveTimeout": (5, "sec")
#               }

# DEFINE VARIABLES (set them in __main__)
#############################################
ConfigGUI(configDict=signalDict, readOnly=True)
ConfigGUI(configDict=debugDict, readOnly=True)
# ConfigGUI(configDict=configDict, readOnly=True)
ConfigGUI(configDict=writeDict, readOnly=True)
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

    # Close other processes
    try:
        processQ.put('Terminate')
    except:
        pass
    try:
        drawQ.put('Terminate')
    except:
        pass

    # Close UDP
    try:
        mySocketUDP.close()
    except:
        pass

    # Close TCP if necessary
    global noNetwork
    try:
        if (not noNetwork):
            mySocket.close()
    except:
        pass

    # Close files if open
    try:
        fileOut.close()
    except:
        pass
    try:
        ECGFileOut.close()
    except:
        pass

    time.sleep(1)  # Give the other processes a chance to close.

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
        ECGrecording = np.asarray([float(row[column])
                                  for row in ECGrecording])
        # for row in ECGrecording:
        #     print (row)
    return ECGrecording
#############################################


# FUNCTION: Browse for an ECG recording.
#############################################
def browseFile():
    fileDir = ""

    # Read the path from the Config file
    ConfigGUI(configDict={"filePath": ""}, readOnly=True)
    from Config import filePath  # Import (in case using a different file)
    dprint("Last used file: " + filePath)

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
            finish()
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


# FUNCTION: Encode given value to immitate ProComp UDP transmissions
#############################################
def getArtifMsg(i):
    "Encodes given value to immitate ProComp UDP transmissions"
    # Add this hex string to the beginning of each packet:
    hs = '21 44 19 01 24 00 00 00 00 00 00 00 03 00 00 00 04 00 00 00'
    hs = hs.replace(' ', '')
    # f1 = 5.1234 + i
    f1 = i
    f1Hex = Decoding.testingHexConversion('<f', f1)[1]
    f1Hex = f1Hex.replace(' ', '')
    # # debug: print float to be sent:
    # valdprint("("+str(f1Hex)+") "+str(f1))
    pkg = hs + f1Hex
    pkgUDP = pkg.decode('hex')  # Set to hex for transmission.
    return pkgUDP
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


# FUNCTION: Entry-field window:
#############################################
def nameEntry(message="", default=""):
    """nameEntry.Entry-field window. Returns the field.

    Default value optional."""

    def nameEntryCloser():
        print (abortMsg)
        finish()

    def okayButton():
        nameEntry.nameWindow.quit()
        nameEntry.nameWindow.destroy()
        return

    # WINDOW:
    nameEntry.nameWindow = tk.Tk(className=" Provide Identifier")
    nameEntry.nameWindow.protocol("WM_DELETE_WINDOW", nameEntryCloser)
    # Hide until positioned:
    nameEntry.nameWindow.withdraw()

    # VARIABLES :
    nameEntry.field = tk.StringVar()
    nameEntry.field.set(default)

    # Widgets:
    nameEntry.EntryFrame = tk.Frame(nameEntry.nameWindow)
    nameEntry.ButtonFrame = tk.Frame(nameEntry.nameWindow)

    nameEntry.Label = tk.Label(nameEntry.EntryFrame, text=message)
    nameEntry.Entry = tk.Entry(nameEntry.EntryFrame, width=15,
                               textvariable=nameEntry.field)

    nameEntry.OKAY = tk.Button(nameEntry.ButtonFrame, text="Okay",
                               command=okayButton, width=8)
    nameEntry.CANCEL = tk.Button(nameEntry.ButtonFrame, text="Cancel",
                                 command=nameEntryCloser, width=8)

    nameEntry.nameWindow.bind('<Escape>', (lambda esc,
                                           b=nameEntry.CANCEL:
                                           nameEntry.CANCEL.invoke()))
    nameEntry.nameWindow.bind('<Return>', (lambda ret,
                                           b=nameEntry.OKAY:
                                           nameEntry.OKAY.invoke()))

    # Pack:
    nameEntry.EntryFrame.pack(fill="x")
    nameEntry.ButtonFrame.pack(fill="x")
    nameEntry.Label.pack(side="left", anchor="nw")
    nameEntry.Entry.pack(side="right", anchor="nw")
    nameEntry.CANCEL.pack(side="right", anchor="se", fill="x")
    nameEntry.OKAY.pack(side="right", anchor="se")

    # Position in the centre of the screen:
    # "Draw" window (even if it is still withdrawn)
    nameEntry.nameWindow.update()
    w = nameEntry.nameWindow.winfo_width()  # width for the Tk root
    h = nameEntry.nameWindow.winfo_height()  # height for the Tk root
    # get screen width and height
    ws = nameEntry.nameWindow.winfo_screenwidth()  # width of the screen
    hs = nameEntry.nameWindow.winfo_screenheight()  # height of the screen
    # calculate centre x and y coordinates
    x = (ws / 2) - (w / 2)
    y = (hs / 2) - (h / 2)
    # set the dimensions of the window and where it is placed
    nameEntry.nameWindow.geometry("%dx%d+%d+%d" % (w, h, x, y))
    nameEntry.nameWindow.minsize(width=w, height=h)
    nameEntry.nameWindow.maxsize(width=w, height=h)
    # Finally, re-show the window, now that it is sized and positioned
    nameEntry.nameWindow.deiconify()

    # Hold until quit:
    nameEntry.nameWindow.mainloop()
    # Once nameEntry.nameWindow has been quit,
    # return what was in the entry field:
    return nameEntry.field.get()
#############################################


"""############################################################################
# NETWORK FUNCTIONS
############################################################################"""


# FUNCTION: Create and test TCP socket:
#############################################
def sendConnectionTCPSocketRequest(TCP_Host, TCP_Port):
    """Creates a TCP connection to the server and returns the connected
    socket object."""
    # 1) create socket:
    # Socket object called "mySocket" contains all necessary
    # properties and can be used to send, receive, etc.
    mySocket = socket.socket(socket.AF_INET,      # Internet protocol
                             socket.SOCK_STREAM)  # TCP
    confirm("Initialising socket.", override=True)

    # 2) Send a connection request to the server /
    #    envoi d'une requête de connexion au serveur :
    try:
        mySocket.connect((TCP_Host, TCP_Port))
        mySocket.settimeout(TCPtimeout)   # 3 sec
        # Receive data if there is any:
        confirm("Receive?")
        # # 3) Retrieve data from the server / Dialogue avec le serveur :
        # try:
        #     msgServeur = mySocket.recv(1024)
        #     """##########################################################
        #     # NOTE!                                                     #
        #     # I don't see a matching part to this in the emulator...!   #
        #     # Therefore including a "try/except" statement              #
        #     ##########################################################"""
        #     print ("RECEIVED: \n"+msgServeur)  # Displays receive message.
        # except socket.error:
        #     print ("No data incoming by TCP...")
    except socket.error:
        print ("The connection has failed / La connexion a echoue."
               "\nContinuing without TCP connection...")
        # sys.exit()
    print ("TCP connection established with the server /\n" +
           "    Connexion TCP etablie avec le serveur.")

    return mySocket
#############################################


# # FUNCTION: create UDP socket:
# #############################################
# # http://searchsoa.techtarget.com/definition/UDP :
# # UDP (User Datagram Protocol) is an alternative communications protocol to
# # Transmission Control Protocol (TCP) used primarily for establishing
# # low-latency and loss tolerating connections between applications on the
# # Internet. Both UDP and TCP run on top of the Internet Protocol (IP) and are
# # sometimes referred to as UDP/IP or TCP/IP. Both protocols send short packets
# # of data, called datagrams.
# def createUDPSocket(UDP_ClientIP, UDP_ClientPort):
#     """Creates a UDP connection to the server and returns the connected
#     socket object."""
#     if (not noNetwork):
#         print 'Opening UDP socket.'
#     confirm("UDP initialising.")  # Dialog box
#     # UDP socket:
#     mySocketUDP = socket.socket(socket.AF_INET,  # Internet protocol
#                                 socket.SOCK_DGRAM)  # UDP
#     # mySocketUDP = socket.socket(socket.AF_INET,
#     #                             socket.SOCK_RAW, socket.IPPROTO_UDP)
#     if (not noNetwork):
#         mySocketUDP.settimeout(UDPConnectTimeout)  # 1sec
#         try:
#             mySocketUDP.bind((UDP_ClientIP, UDP_ClientPort))
#         except socket.error:
#             print "UDP socket error. Cannot continue. Terminating..."
#             mySocketUDP.close()
#             mySocket.close()
#             finish()
#     return mySocketUDP
# #############################################


# # FUNCTION: Connection acknowledgement send (TCP: mySocket)
# #############################################
# def sendAckConnectionFrom1001(mySocket):
#     """Sends an encoded acknowledgement flag via TCP to the ProComp server."""
#     msgInit = ("21 88 39 7E 36 00 00 00 0F 27 00 00 09 00 00 00 "
#                "00 00 00 00 41 43 4B 4E 4F 57 4C 45 44 47 45 44 "
#                "5F 46 52 4F 4D 20 31 32 37 2E 30 2E 30 2E 31 20 "
#                "31 30 30 31 20 00")
#     msgInitHex = msgInit.replace(' ', '')  # Concatenate:
#     # 2188397E360000000F270000090000000000000041434B4E4F574C45444745445F46524F4
#     # D203132372E302E302E3120313030312000
#     msgInitHex = msgInitHex.decode('hex')
#     # "!\x889~6\x00\x00\x00\x0f'\x00\x00\t\x00\x00\x00\x00\x00
#     # \x00\x00ACKNOWLEDGED_FROM 127.0.0.1 1001 \x00"
#     print 'SENDING: <HEADER> ACKNOWLEDGED_FROM 127.0.0.1 1001'
#     # ACKNOWLEDGED_FROM ...
#     confirm("Sending connection acknowledgement.")
#     try:
#         mySocket.send(msgInitHex)  # TCP
#     except socket.timeout:
#         print "WARNING:\nAcknowledgement send timed out. Continuing..."
#         confirm("WARNING:\n\n"
#                 "Acknowledgement send timed out.\n\nContinuing...")
#     except socket.error:
#         print ("WARNING:\n"
#                "Acknowledgement send error (TCP socket may not be connected)."
#                "\nContinuing...")
#         confirm("WARNING:\n\n"
#                 "Acknowledgement send error "
#                 "(TCP socket may not be connected)."
#                 "\n\nContinuing...")
# #############################################


# # FUNCTION: Connection confirmation message send (TCP: mySocket)
# #############################################
# def sendConfirmation(mySocket):
#     """Sends an encoded confirmation flag via TCP to the ProComp server."""
#     msgConnAck = ("21 00 00 00 2A 00 00 00 07 00 00 00 00 00 00 00 "
#                   "00 00 00 00 43 6F 6E 6E 65 63 74 69 6F 6E 20 61 "
#                   "6B 6E 6F 77 6C 65 64 67 65 64")
#     msgConnAckHex = msgConnAck.replace(' ', '')  # Concatenate
#     msgConnAckHex = msgConnAckHex.decode('hex')
#     # print 'SENDING: \n'+msgConnAckHex
#     print 'SENDING: <HEADER> Connection aknowledged'
#     confirm("Sending connection confirmation.")
#     try:
#         mySocket.send(msgConnAckHex)  # TCP
#     except socket.timeout:
#         print "WARNING:\nConfirmation send timed out.\nContinuing..."
#         confirm("WARNING:\n\nConfirmation send timed out.\n\nContinuing...")
#     except socket.error:
#         print ("WARNING:\n"
#                "Confirmation send error (TCP socket may not be connected)."
#                "\nContinuing...")
#         confirm("WARNING:\n\n"
#                 "Confirmation send error (TCP socket may not be connected)."
#                 "\n\nContinuing...")
# #############################################


# # FUNCTION: Begin the UDP transmission
# #############################################
# def beginUPDTransmission(mySocket):
#     msgRdy = ("21 01 93 00 1A 00 00 00 0F 27 00 00 09 00 00 00 "
#               "01 00 00 00 52 45 41 44 59 00")
#     msgRdyHex = msgRdy.replace(' ', '')  # Concatenate
#     msgRdyHex = msgRdyHex.decode('hex')  # Hex-encode
#     print 'SENDING: <HEADER> READY TAIL'
#     confirm("UDP info coming hereafter.")
#     try:
#         mySocket.send(msgRdyHex)  # send trigger message by TCP
#         # Receive trigger acknowledgement:
#         msgDist = mySocket.recv(1024)
#         print ("msg received: " + str(msgDist.encode('hex')) +
#                "(" + msgDist + ")")
#     except socket.timeout:
#         print "WARNING:\nUDP-trigger send/receive timed out.\nContinuing..."
#         confirm("WARNING:\n\nUDP-trigger send/receive timed out."
#                 "\n\nContinuing...")
#     except socket.error:
#         print ("WARNING:\n"
#                "UDP-trigger send/receive error "
#                "(TCP socket may not be connected)."
#                "\nContinuing...")
#         confirm("WARNING:\n\n"
#                 "UDP-trigger send/receive error "
#                 "(TCP socket may not be connected)."
#                 "\n\nContinuing...")
#     dispInfo("PORT_UDP_DIST opened")
# #############################################


# FUNCTION: Receive ECG data via UDP
#############################################
# def launchReceptionFromUDP(mySocketUDP, lUDPMsgBrut, lAllFloats, lWindow,
#                            writeOutput):
def launchReceptionFromUDP(inlet, lUDPMsgBrut, lAllFloats, lWindow,
                           writeOutput):

    stopGUI = StopGUI()  # GUI with STOP button

    # if (not noNetwork):
    #     print ("Receiving from", str(mySocketUDP.getsockname()))
    #     # Set long timeout for actually receiving the data:
    #     mySocketUDP.settimeout(UDPReceiveTimeout)

    # Initialise loop:
    lastMsgHex = ''  # A comparison variable to flag the message end.
    continueFlag = True
    repetitionCount = 0
    global simpleSTOP
    global marker
    global timeCounter

    """##################
    #                   #
    #  noNetwork  True  #
    #                   #
    ##################"""
    if noNetwork:
        count = long(0)  # start counter index from 0
        prev = time.time()
        # while continueFlag and (not stopFlag):
        for dataPoint in ECGrecording:  # loop through items in ECGrecording
            # Allow the send loop to be interrupted at the end of a cycle:
            if not stopFlag:
                # Regulate frequency:
                count, prev = freqRegulate(count,
                                           INTERVAL,
                                           prev)

                # Encode to mimic ProComp
                UDPpacket = getArtifMsg(dataPoint)

                # 'Receive':
                msgUDP = UDPpacket

                # Add the raw 'received' data to the message list:
                lUDPMsgBrut.append(msgUDP)

                # Interpret whatever was received in Hex format:
                msgUDPHex = msgUDP.encode('hex')
                # print (msgUDPHex)

                # No need to check if new if not going via network...
                # Therefore no need for 'lastMsgHex'

                # Decode the current message into a temporary
                # list of floats for that particular message:
                # (should just be one, since this noNetwork)
                lFloats = Decoding.decodeUDPPackage(msgUDPHex)
                # print (lFloats[0])

                # Append those floats to the full list of
                # floats received:
                # (no loop, since it will only happen once:)
                f = lFloats[0]  # replaces loop
                timeCounter += INTERVAL  # Increment the timestamp
                # Add each term to the list of all floats:
                lAllFloats.append(f)

                # New point as data frame:
                # Option for sending Marker to processing process:
                dfF = pd.DataFrame({'ECG': [f, ],
                                    'Marker': ["{0:15s}".format(marker), ]},
                                   index=[timeCounter, ])
                # # Option for no Marker send:
                # dfF = pd.DataFrame({'ECG': [f, ],
                #                     },
                #                    index=[timeCounter, ])

                # Update the window list for ghost plot
                # (Append new and remove oldest):
                lWindow = listCycle(f, lWindow)

                # Pass data to other processes
                processQ.put(dfF)  # Send point to be processed as data frame
                # Send window list to plot (for latency comparison):
                if not noPlot:
                    ghostQ.put(lWindow)

                # Print received values:
                if recDebugPrinter:
                    print (str(f))
                # Write to file (live):
                if SeparateECGFile:
                    # Print with fixed decimal places:
                    ECGFileOut.writelines("{0:.9f}".format(timeCounter) +
                                          ", " +
                                          "{0: .4f}".format(f) +
                                          ", " +
                                          "{0:15s}".format(marker) +
                                          "\n")
                # Once sent (and written, if requested), reset marker:
                marker = ""
                if not simpleSTOP:
                    stopGUI.Y = int((7 * stopGUI.Y +
                                     50 + (25 * f)) / 8)
                    ##################################################
                    # Insert another function here if you want to do #
                    # anything else with the received value          #
                    ##################################################
        """##################
        #                   #
        #  noNetwork False  #
        #                   #
        ##################"""
    else:
        while continueFlag and (not stopFlag):
            # try:
                # # Try to receieve:
                # # max size for a UDP packet / taille max paquet UDP:
                # msgUDP, (addr, TCP_Port) = mySocketUDP.recvfrom(65535)
                # # msgUDP, (addr,TCP_Port) = mySocketUDP.recvfrom(1024)
                #
                # # print ("msgUDP: "+msgUDP)
                # # Add the raw received data to the message list:
                # lUDPMsgBrut.append(msgUDP)
                # # Interpret whatever was received in Hex format:
                # msgUDPHex = msgUDP.encode('hex')
                # # print ("msgUDPHex: " + msgUDPHex)
                # # Check for a fresh message:
                # if not lastMsgHex == msgUDPHex:
                #     # update the "last message" variable:
                #     lastMsgHex = msgUDPHex
                #     # and decode the current message into a temporary
                #     # list of floats for that particular message:
                #     lFloats = Decoding.decodeUDPPackage(msgUDPHex)
                #     # print ("UPD:" + str(lFloats))
                #     # Append those floats to the full list of
                #     # floats received:
                #     for f in lFloats:
                #         timeCounter += INTERVAL  # Increment the timestamp
                try:
                    item, timeCounter = inlet.pull_sample()
                    # print ("item =", item, "of type:", type(item))
                    f = item[0]
                    # print ("f =", item, "of type:", type(f))
                except:
                    print ("Can't pull from inlet.")
                    continueFlag = False
                    try:
                        stopGUI.rootWindow.quit()
                    except:
                        pass

                # Add each term to the list of all floats:
                lAllFloats.append(f)

                # New point as data frame:
                dfF = pd.DataFrame({'ECG': [f, ]},
                                   index=[timeCounter, ])
                # Update the window list for ghost plot
                # (Append new and remove oldest):
                lWindow = listCycle(f, lWindow)

                # Pass data to other processes:
                # Send point to sig-processing as a data frame:
                processQ.put(dfF)
                # Send window list to the plot process (for latency
                # comparison):
                if not noPlot:
                    ghostQ.put(lWindow)

                # Print received values:
                if recDebugPrinter:
                    print (str(f))
                # Write to file (live):
                    if SeparateECGFile:
                        # Print with fixed decimal places:
                        ECGFileOut.writelines("{0:.9f}"
                                              .format(timeCounter) +
                                              ", " +
                                              "{0: .4f}".format(f) +
                                              ", " +
                                              "{0:s}".format(marker) +
                                              "\n")
                        # Once written, reset marker:
                        marker = ""
                if not simpleSTOP:
                    stopGUI.Y = int((10 * stopGUI.Y +
                                     50 + (25 * f)) / 11)

                # else:  # No new message
                #     # print ("alreadyRec:" + msgUDPHex)
                #     repetitionCount += 1
                #     if debugRepetitions:
                #         print ("Received", repetitionCount, "duplicates.")

            # except:
            #     print ("Not receiving")
            #     continueFlag = False
            #     try:
            #         stopGUI.rootWindow.quit()
            #     except:
            #         pass

            # except socket.timeout:  # Quit the receive protocol when timeout.
            #     print ("UDP socket timed out")
            #     continueFlag = False
            #     try:
            #         stopGUI.rootWindow.quit()
            #     except:
            #         pass
#############################################


# # FUNCTION: Reinitialise the reception of values via UDP
# #############################################
# # (Uses the above launchReceptionFromUDP function)
# def restartReceptionFromUDP(inlet, lUDPMsgBrut, lAllFloats, lWindow,
#                             writeOutput,
#                             hostUDP):
#     """Relaunch the UDP receive function (launchReceptionFromUDP)"""
#     # Close UDP connection:
#     mySocketUDP.close()
#     UDP_ClientIP = hostUDP  # Why would we want to feed it this?
#     # Reestablish UDP connection:
#     mySocketUDP = createUDPSocket(UDP_ClientIP, UDP_ClientPort)
#     # And relaunch reception:
#     # launchReceptionFromUDP(mySocketUDP, lUDPMsgBrut, lAllFloats, lWindow,
#     #                        writeOutput)
#     launchReceptionFromUDP(inlet, lUDPMsgBrut, lAllFloats, lWindow,
#                            writeOutput)
# #############################################

"""
############################################################################
# Classes           ####   #        #     ####   ####  #####   ####
#                  #    #  #       # #   #      #      #      #
#                  #       #      #   #   ###    ###   #####   ###
#                  #    #  #      #####      #      #  #          #
#                   ####   #####  #   #  ####   ####   #####  ####
############################################################################
"""


# CLASS: Process the windows to detect peaks
#############################################
class peakProcessing(multiprocessing.Process):
    """Process in which to process the received ECG data"""
    def __init__(self, processQ, drawQ, processing_rate, rate, procWindowTime,
                 fileNameString, fileDict, noPlot):
        self.processQ = processQ
        self.drawQ = drawQ
        self.noPlot = noPlot
        # Time interval at which to run this processing loop:
        self.procInterval = 1.0 / processing_rate
        # Original ECG sampling time data:
        self.rate = rate
        self.INTERVAL = 1.0 / rate
        self.procWindowTime = procWindowTime
        self.liveWindow = int(procWindowTime * rate)
        # File for writing output:
        self.fileNameString = fileNameString
        self.fileDict = fileDict.copy()

        # Identify columns to be written (ECG and then the various peaks data):
        self.writeECG = self.fileDict['ECG']
        self.onlyECG = self.fileDict['unique']
        self.writeTimes = self.fileDict['times']
        self.writeHeader = self.fileDict['header']
        for discardItem in ['header', 'unique', 'times', 'ECG']:
            del self.fileDict[discardItem]
        # del self.fileDict['ECG']

        for key, val in self.fileDict.items():
            if not val:  # i.e. if value is False
                del self.fileDict[key]

        self.writeColumns = list(self.fileDict.keys())
        self.headerColumns = sorted((['ECG', ] * self.writeECG) +
                                    self.writeColumns + ['Markers', ])
        # We now know whether to write a header (writeHeader), what that header
        # should be (headerColumns), whether to write the ECG stream (writeECG)
        # (i.e. whether to use newData at all - if not, we skip the merge
        # step), and which columns to write whenever a peak is detected
        # (writeColumns) (if this is empty, we can again skip the merge with
        # newData), and whether to write indexes.

        # Start:
        multiprocessing.Process.__init__(self)
        self.start()

    def run(self):
        """"""
        """
        # LSL setup:
        """
        # The last value would be the serial number of the device or some other more or less locally unique identifier for the stream as far as available (you could also omit it but interrupted connections wouldn't auto-recover).
        plotInfo = StreamInfo('PeakData', 'Peaks', 4, 1, 'float32', 'CalculatedRPeaks')
        # next make an outlet
        plotOutlet = StreamOutlet(plotInfo)

        if noPlot:
            self.drawQ.close()  # Won't need this if not drawing.

        # Initiate Data to process:
        #############################

        # Last peak *found* and last peak *in the window* will be different:
        lastPeakT, lastWindowPeakT = 0, []

        RRIntervals, HR = [], []
        oldPeak_t = []

        # Write only the selected columns:
        dfPeaks = pd.DataFrame(self.writeColumns)
        # Will always need this:
        dfData = pd.DataFrame({'ECG': [None, ] * self.liveWindow},
                              index=range(-self.liveWindow, 0))
        # Only need this if writing the ECG stream
        if self.writeECG:
            dfNewData = pd.DataFrame({'ECG': []},
                                     index=[])

        # Open file to which to write:
        #############################
        self.fileOut = open(self.fileNameString, 'a')

        # Add header if requested:
        if self.writeHeader:
            # Create the string for the columns:
            names = ["Time", ] * self.writeTimes + self.headerColumns
            headerString = ""
            for name in names:
                headerString = (headerString + "{:15s}".format(" " + name) +
                                "," * (name != names[-1]))  # no comma on last
            # Write that string as the header:
            self.fileOut.write(headerString + "\n")

        # Initiate loop:
        #############################
        # Control:
        stopFlag = False
        # Frequency control:
        count = 0
        prev = time.time()

        while (not stopFlag):

            """FREQ REG"""
            count, prev = freqRegulate(count, self.procInterval, prev)

            """RECEIVE"""
            if (not self.processQ.empty()):  # Check if data in the queue
                # Start from a blank:
                dfDataRecv = pd.DataFrame({'ECG': []})
                limCount = 0
                while ((not self.processQ.empty()) and
                       # (limCount < (self.procInterval * self.rate * 3))):
                       # # Only collect enough data points to make up for 3
                       # # computation intervals.
                       (limCount < (self.liveWindow))):
                    # Only collect enough data points for 1 processing window,
                    # even if there's more backlog. Otherwise some points
                    # will not be processed.
                    # If data has been queued for longer than that, leave
                    # the excess queued for the next cycle.
                    limCount += 1

                    # Take off data from processQ:
                    dfPoint = self.processQ.get()

                    # Check for termination flag
                    if str(dfPoint) == 'Terminate':
                        stopFlag = True
                        break

                    # If not terminate, append point to the received data:
                    dfDataRecv = dfDataRecv.append(dfPoint)

                """CHECK LAG (BACKLOG)"""
                lag = self.processQ.qsize()
                if int(lag / 4) > 0:
                    print ("{:.2f}s la{}g".format(lag * self.INTERVAL,
                                                 ("a" * (lag / 8))))
                    sys.stdout.flush()

                if (not stopFlag):
                    """   INITIALISE PROCESSING   """

                    # store old length to be able to trim to get dfNewData
                    # for writing:
                    # oldLen = len(dfNewData.index.values)

                    """ Add received to the major data frames: """
                    # These contain just the ECG values, and are indexed
                    # with the timestamps.
                    dfData = dfData.append(dfDataRecv)
                    # We now have an over-sized dataframe of ECG points...
                    if self.writeECG:
                        dfNewData = dfNewData.append(dfDataRecv)

                    """ Trim dfData: """
                    dfData = dfData.iloc[-self.liveWindow:]
                    # We now have a fixed-length dfData dataframe of length
                    # liveWindow.

                    # print (dfData)
                    # sys.stdout.flush()

                    """Note:"""
                    # dfNewData needs no trimming/sizing before writing to
                    # file since it will already start with the point directly
                    # after the last peak that was written to file and if we
                    # only ever add dfDataReceived to it, then there will
                    # never be duplicate data.

                    """###########################################
                    # This is where the actual signal processing #
                    # happens.                                   #
                    ###########################################"""
                    # Work with simple lists from here:
                    ECGSample = list(dfData['ECG'])
                    ECGSampleTimes = list(dfData.index.values)
                    """ Detect Peaks """
                    # Local indeces:
                    peak_i = detect_beats(ECGSample, self.rate)
                    # Actual peak values and times:
                    peak_y, peak_t = [], []
                    try:
                        for i in peak_i:
                            peak_y.append(ECGSample[i])
                            peak_t.append(ECGSampleTimes[i])
                    except:
                        # peak_i returned empty
                        pass

                    """ check for new peaks in window """
                    if oldPeak_t != peak_t:
                        try:
                            if oldPeak_t[0] != peak_t[0]:
                                # Only update lastWindowPeakT if a peak has
                                # passed off the left edge:
                                lastWindowPeakT = [oldPeak_t[0], ]
                                # print ("lastWindowPeakT = ", lastWindowPeakT)
                        except:
                            # if oldPeak_t was empty (will only happen for
                            # very first peak):
                            pass
                            # print ("First peak detected")
                        # Update oldPeak_t to new list:
                        oldPeak_t = peak_t

                        """ Update Heart Rate """
                        # need to pre-append the last detected peak to get the
                        # right number of intervals:
                        HRtimes = lastWindowPeakT + peak_t  # list
                        RRIntervals = list(np.diff(HRtimes))
                        # In BPM, not Hz:
                        HR = [60.0 / i for i in RRIntervals]
                        if (lastWindowPeakT == []) and (HR != []):
                            # i.e. up until the first peak:
                            RRIntervals = [None, ] + RRIntervals
                            HR = [None, ] + HR

                        """ Frame """
                        # dfPeaks = pd.DataFrame({"peak_y": peak_y,
                        #                         "RRIntervals": RRIntervals,
                        #                         "HR": HR},
                        #                        index=peak_t)
                        dfPeaks = pd.DataFrame(columns=self.writeColumns,
                                               index=peak_t)
                        for column in self.writeColumns:
                            dfPeaks[column] = locals()[column]

                        """ Identify new peaks """
                        for t in peak_t:
                            if (t - lastPeakT) > 0:
                                # New peak detected.
                                """ Isolate new peaks """
                                # Note: don't confuse dfNewData and dfNewPeaks
                                if not self.onlyECG:
                                    dfNewPeaks = dfPeaks.loc[t:]
                                # Identify new last processed peak:
                                lastPeakT = peak_t[-1]

                                """ Build recordable dataframe """
                                if self.writeECG:
                                    # Extract dfNewData up to that last
                                    # processed peak:
                                    dfDraw = dfNewData.loc[:lastPeakT]
                                    # Leave the remaining data in dfNewData:
                                    dfNewData = dfNewData.iloc[len(dfDraw):]
                                    if not self.onlyECG:
                                        # Add the peak data:
                                        dfDraw = pd.concat([dfDraw,
                                                            dfNewPeaks],
                                                           axis=1)
                                else:
                                    dfDraw = dfNewPeaks.copy()
                                    # Need to add last trigger here...
                                # Write to file:
                                if self.writeTimes:  # write with timestamps
                                    dfDraw\
                                        .reset_index()\
                                        .to_csv(self.fileOut,
                                                index=False,
                                                float_format="%15.9f",
                                                na_rep=" " * 15,
                                                header=False)
                                else:  # write without timestamps
                                    dfDraw\
                                        .to_csv(self.fileOut,
                                                index=False,
                                                float_format="%15.9f",
                                                na_rep=" " * 15,
                                                header=False)

                                # print (dfDraw)
                                # print ("")
                                # sys.stdout.flush()
                                # break

                    # """   DRAW   """
                    # if not self.noPlot:
                    #     # Pass on to drawQ as tuple:
                    #     self.drawQ.put_nowait((dfData["ECG"],  # Main plot
                    #                            # (is actually faster to send
                    #                            #  the whole dataframe than
                    #                            #  to index it for a
                    #                            #  column and send that.)
                    #                            peak_i,  # Local peak indexes
                    #                            peak_y,  # Peak heights
                    #                            RRIntervals,  # R-R Intervals
                    #                            HR  # Heart rate
                    #                            )
                    #                           )
                    #     # Send to LSL plotting thread:
                    #     for i in xrange(len(peak_i)):
                    #         # print ("i =", i)
                    #         sample = [peak_i[i], peak_y[i], RRIntervals[i], HR[i]]
                    #         # print ("sample =", sample,", time =", peak_t[i])
                    #         if not (None in sample):
                    #             # print ("pushing...")
                    #             plotOutlet.push_sample(sample, peak_t[i])
                    #         # else:
                    #         #     print ("not pushing...")


            else:
                pass

        print ("Terminated 1 signal-processing process cleanly.")
        sys.stdout.flush()


# CLASS: GUI for interrupting the send
#############################################
class StopGUI(threading.Thread):

    def __init__(self):
        # Initialise
        self.rootWindow = tk.Tk(className="\nECGProc")
        # Position the window on the screen:
        w = 400  # width for the window
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
        self.stopButton = tk.Button(self.rootWindow, text="STOP ECG\nCLIENT",
                                    font=('Helvetica', 12, "bold"),
                                    command=self.stopbutton,
                                    bd=10, bg="red3", fg="white",
                                    cursor="pirate")
        self.markerButton = tk.Button(self.rootWindow, text="SET MARKER",
                                      font=('Helvetica', 12, "bold"),
                                      command=self.markerbutton,
                                      bd=10, bg='#b0c050', fg="white")

        self.stopButton.pack(side="left")
        self.markerButton.pack(side="right")

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

        # Bind the space bar to the marker button when the window is in focus.
        self.rootWindow.bind('<space>', (lambda esc,
                                         b=self.markerButton:
                                         self.markerButton.invoke()))

        # Bring window into focus to make use of those key bindings:
        self.rootWindow.update()
        self.rootWindow.deiconify()

        # Animated or static STOP button:
        global simpleSTOP
        if not simpleSTOP:
            # Animated
            self.updateLoop()
        else:
            # Static
            xScale = 4
            yScale = 2
            self.stopButton.place(width=xScale * self.Y,
                                  height=yScale * self.Y,
                                  x=100 - xScale * self.Y / 2,
                                  y=50 - yScale * self.Y / 2)
        # Just in case the loop accidentally exits:
        self.rootWindow.mainloop()

    def updateLoop(self):
        # Update button Y-position:
        xScale = 4
        yScale = 2
        self.stopButton.place(width=xScale * self.Y,
                              height=yScale * self.Y,
                              x=100 - xScale * self.Y / 2,
                              y=50 - yScale * self.Y / 2)
        # Update at 60Hz:
        self.rootWindow.after(int(1000 / 60), self.updateLoop)


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
        ConfigGUI("Signal Setup", "Enter ECG and processing parameters:",
                  configDict=signalDict, descWidth=160, entryWidth=6)
        ConfigGUI("Write Options",
                  "If no column or file selected, will write peak times only:",
                  configDict=writeDict, descWidth=160, entryWidth=6)
        # if not noNetwork:  # No need for network options if noNetwork:
        #     ConfigGUI("Network Setup", "Enter network parameters:",
        #               configDict=configDict, descWidth=100)
        # else:
        #     ConfigGUI(configDict=configDict, readOnly=True)
        if debugRun:  # Display debug config only if requested:
            ConfigGUI("Debug Options", "Select run parameters:",
                      configDict=debugDict, descWidth=160, entryWidth=6)
        else:
            ConfigGUI(configDict=debugDict, readOnly=True)
        from Config import *

        #######################################################################
        # Assign a name to the run
        #############################################
        runName = "Run_Name"  # Default in case of no pre-existing values
        # Import any saved name:
        ConfigGUI(configDict={"runName": ""}, readOnly=True)
        from Config import runName
        # Query user:
        runName = nameEntry(message="Enter an ID for the run:",
                            default=runName)
        print ("Run ID:", runName)
        # Write to Config file:
        ConfigGUI(configDict={"runName": runName}, setToDefaults=True)

    else:
        ConfigGUI(configDict=signalDict, readOnly=True)
        # ConfigGUI(configDict=configDict, readOnly=True)
        ConfigGUI(configDict=debugDict, readOnly=True)
        ConfigGUI(configDict=writeDict, readOnly=True)
        ConfigGUI(configDict={"runName": ""}, readOnly=True)
        from Config import *

    # Other variables
    #############################################
    INTERVAL = 1.0 / rate  # Sample period to be used for time-stamping
    liveWindow = int(procWindowTime * rate)  # sampling window in samples.
    timeCounter = 0  # counter with which to time-stamp the received ECG values
    stopFlag = False
    marker = ""

    # Write-to-file variables:
    #############################################
    # Check if writing only a file of the ECG stream, in which case will only
    # use the values from the processing process even if SeparateECGFile:
    # First check column selection:
    UniqueECGFile = (ECGColumn and
                     (not
                      (HRColumn or RRColumn or PeakColumn)))

    # Create a file tag according to selected columns:
    if not (RRColumn or HRColumn or ECGColumn or
            PeakColumn or UniqueECGFile):
        tag = "#PeakTimes"  # will also use this as a column flag in fileDict
        TimeColumn = True  # Override if no other column selected.
    else:
        tag = ((ECGColumn or UniqueECGFile) * "#ECG" +
               HRColumn * "#HR" +
               RRColumn * "#RR" +
               PeakColumn * "#Pk")

    # Falsify SeparateECGFile if writing only the the ECG stream anyway:
    SeparateECGFile = SeparateECGFile and (not UniqueECGFile)
    # print ("UniqueECGFile:", UniqueECGFile)
    print ("Creating %d output file%s..." % (1 + SeparateECGFile,
                                            's' * SeparateECGFile))

    # Put all the variables needed for the processing stream into a dictionary
    # which will be easy to pass to that process (Note these are the same as
    # the dataframe column titles, so can be used as keys if needed):
    fileDict = {"header": write_header,
                "unique": UniqueECGFile,
                "times": TimeColumn,
                "ECG": ECGColumn,
                "peak_y": PeakColumn,
                "RRIntervals": RRColumn,
                "HR": HRColumn
                }

    #######################################################################
    # Create output file title string
    #############################################
    # Output-writing algorithm (if writeOutput is True)
    # Writes date-stamped file to the output folder
    # (which it creates if non-existant)
    fileNameString = "_"  # Blank in case of writeOutput = False

    # Get date and time (converted into underscored format e.g. 1970_02_01):
    # fileNameString = re.sub('[.!,;: -]', '_', str(datetime.now()))
    fileNameString = datetime.now().strftime("%Y_%m_%d__%H_%M_%S")
    # Create an output folder if one doesn't exist:
    if not os.path.exists("output"):
        os.makedirs("output")

    # Create a string(s) for naming output:
    if SeparateECGFile:
        ECGFileNameString = ("output/" +
                             runName + "_run" + str(rate) + "_" +
                             fileNameString + "_#ECG." + write_type)
        ECGFileOut = open(ECGFileNameString, 'a')
    fileNameString = ("output/" +
                      runName + "_run" + str(rate) + "_" +
                      fileNameString + "_" + tag + "." + write_type)

    # Gets done in signal processing process:
    # Create a date-stamped .txt file to which it writes all the ECG data
    # # received (even if no writeOutput and therefore just temporary):
    # fileOut = open(fileNameString, 'a')

    # Start the extra process here:
    #############################################
    # Create queues to share data between processes
    # (must create drawQ and readyQ, even if noPlot because of process
    # argument lists)
    processQ = multiprocessing.Queue()
    drawQ = multiprocessing.Queue()
    # readyQ = multiprocessing.Queue()
    if not noPlot:
        ghostQ = multiprocessing.Queue()
    # Create the signal-processing process:
    peakProcess = peakProcessing(processQ, drawQ,
                                 processing_rate, rate, procWindowTime,
                                 fileNameString, fileDict, noPlot)

    # # Create the plotting process:
    # if not noPlot:
    #     livePlot = livePlotting(drawQ, readyQ, plot_rate, rate,
    #                             procWindowTime, ghostQ)
    #     # Wait for plot to initialise:
    #     ready = False
    #     print ("Initialising plot...")
    #     while (not ready):
    #         ready = readyQ.get()
    #         time.sleep(0.1)
    #     print ("Plot initialised.")
    # else:
    #     # Don't actually need this if not plotting:
    #     drawQ.close()
    # # Finished with readyQ now, whether plotting or not:
    # readyQ.close()

    ###########################################################################
    # Create background window for further messages
    #############################################
    rootWindow = tk.Tk()
    rootWindow.wm_withdraw()                 # Hide host window

    ###########################################################################
    # Import file to array if running with noNetwork
    #############################################
    if noNetwork:
        filePath = browseFile()
        print ("Simulated Server: Importing recorded ECG session now")
        confirm("Simulated Server: Importing recorded ECG session now")
        ECGrecording = importRecording(filePath)
        print ("Simulated Server: ECG session imported")

    ###########################################################################
    # START
    #############################################
    confirm("Starting script.")

    # if (not noNetwork):
    #     #######################################################################
    #     # SET UP CONNECTION(S)
    #     #############################################
    #     # (The UDP line will be the one actually receiving the data.)
    #     mySocket = sendConnectionTCPSocketRequest(TCP_Host, TCP_Port)  # TCP
    # # Need to create UDP socket regardless of network, because we need the
    # # object to be avaiable for the function calls:
    # mySocketUDP = createUDPSocket(UDP_ClientIP, UDP_ClientPort)  # UDP

    if (not noNetwork):
        #######################################################################
        # ACKNOWLEDGE and CONFIRM TCP CONNECTION(S)
        #############################################
        # Send reverse-engineered acknowledgement to the ProComp server:
        # sendAckConnectionFrom1001(mySocket)
        # sendConfirmation(mySocket)

        # LSL:
        # first resolve an ECG stream on the lab network
        print("looking for an ECG stream...")
        streams = resolve_stream('type', 'ECG')

        # create a new inlet to read from the stream
        inlet = StreamInlet(streams[0])
        print ('inlet created.')

        """
        #######################################################################
        # RECEIVE
        #############################################
        """
        # #######################################################################
        # # Trigger UDP via TCP:
        # #############################################
        # beginUPDTransmission(mySocket)
    else:
        inlet = None

    """
    ###########################################################################
    # LIVE PLOT
    #############################################
    """
    # Create blank lists into which to put the received data:
    lUDPMsgBrut = []  # "Brut"(Fr.) = "Raw"(En.)
    lAllFloats = []
    lWindow = [0.0, ] * liveWindow  # for last procWindowTime seconds
    # lWindowTimes = [0.0, ] * liveWindow  # corresponding timestamps
    # Pack as a data frame:
    # dfWindow = pd.DataFrame({'ECG': lWindow}, index=lWindowTimes)

    t = np.linspace(0, liveWindow * INTERVAL, liveWindow)

    ###########################################################################
    # Receive by LSL:
    #############################################
    # stopGUI = StopGUI()  # GUI with STOP button
    # launchReceptionFromUDP(mySocketUDP, lUDPMsgBrut, lAllFloats, lWindow,
    #                        writeOutput)
    launchReceptionFromUDP(inlet, lUDPMsgBrut, lAllFloats, lWindow,
                           writeOutput)

    # ###########################################################################
    # # Option to Continue/Append:
    # #############################################
    # continueFlag = True
    # # while continueFlag and (not stopFlag):
    # while continueFlag:
    #     print ("Number of floats received: " + str(len(lAllFloats)))
    #     res = confirm("UDP socket timed out or was stopped.\n"
    #                   "'Yes' to reset connection and continue, or\n"
    #                   "'No' to finish.",
    #                   noexit=True,
    #                   override=True)  # Display every time.
    #     # if res:
    #     #     continueFlag = True
    #     #     # global stopFlag
    #     #     stopFlag = False
    #     #     print ("Resetting UDP connection...")
    #     #     restartReceptionFromUDP(inlet, lUDPMsgBrut, lAllFloats,
    #     #                             lWindow,
    #     #                             writeOutput, UDP_ClientIP)
    #     # else:
    #     #     continueFlag = False
    continueFlag = False

    """
    ###########################################################################
    # FINISH
    #############################################
    """

    print ("Arrived at end of script successfully.")
    finish()

    # And they all lived happily ever after.
    #              THE END
