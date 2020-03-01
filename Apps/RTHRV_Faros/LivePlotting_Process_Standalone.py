# -*- coding: utf-8 -*-
###############################################################################
#
#    Live Plotting of Received LSL Time Series.
#
#    - Matthew Wilson, 2016
###############################################################################
#
#    license info here...
#
###############################################################################

# Lab Streaming Layer Import
#############################################
import sys; sys.path.append('liblsl-Python') # help python find pylsl relative to this example program
from pylsl import StreamInlet, resolve_stream, StreamInfo, StreamOutlet, local_clock

# Standard Anaconda:
#############################################
# import csv
import datetime
import matplotlib
import matplotlib.pyplot as plt
# import matplotlib.animation as anim
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# from matplotlib.backends.backend_tkagg import NavigationToolbar2TkAgg
import matplotlib.dates as pldates
import matplotlib.ticker as plticker
import multiprocessing
import numpy as np
import os
# import os.path
import pandas as pd
import psutil
# import socket
# import struct
import sys
import threading
import time
import Tkinter as tk
# import tkFileDialog as filedialog
# import tkMessageBox
# Custom file dependencies:
#############################################
# import Decoding
# from ConfigGUI import ConfigGUI
# # NOTE: ConfigGUI() creates another file called Config.py, which it imports
# #       and reloads a couple of times. Some python interpretters may therefore
# #       throw errors the first couple of times this script is run, until
# #       Config.py has all its variables settled, especially if the OS is
# #       running slowly and takes a long time to write that file. Sometimes it
# #       is necessary to restart the inerpretter, or to open and re-save
# #       Config.py.
# from RPeakDetectLive import detect_beats

# For live plotting in Tkinter, ensure matplotlib plots in Tkinter:
#############################################
matplotlib.use('TkAgg')


"""
###############################################################################
# Functions         #####   #   #   ##   #    ####
#                   #        # #    # #  #   #
#                   ####      #     #  # #    ###
#                   #        # #    #   ##       #
#                   #       #   #   #    #   ####
###############################################################################
"""

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


"""
############################################################################
# Classes           ####   #        #     ####   ####  #####   ####
#                  #    #  #       # #   #      #      #      #
#                  #       #      #   #   ###    ###   #####   ###
#                  #    #  #      #####      #      #  #          #
#                   ####   #####  #   #  ####   ####   #####  ####
############################################################################
"""

# CLASS: Multiprocess plotting
#############################################
class livePlotting(threading.Thread):
    """Process in which to analyse and plot the incoming ECG.
    args:
    drawQ = the data queue to be drawn
    plot_rate = rate (in Hz) at which to attempt to redraw.
    rate = sampling rate
    liveWindowTime = window width in seconds"""

    def __init__(self, type, plot_rate, rate, liveWindowTime, internalTime,
                 thickness, col, negative, inverted, scale, offset, valueText):
        self.type = type
        self.rate = rate
        self.internalTime = internalTime
        self.INTERVAL = 1.0 / rate
        self.liveWindowTime = liveWindowTime
        self.thickness = thickness
        self.col = col
        self.negative = negative
        self.inverted = inverted
        self.scale = scale
        self.offset = offset
        self.valueText = valueText
        self.refresh = int(1000 / plot_rate)  # Hz to milliseconds

        self.liveWindow = int(liveWindowTime * rate)
        self.startTime = 0.0
        self.internalT = 0.0
        self.prevT = 0
        # Persistent main data plots:
        self.ECGsample = []
        self.ECGtime = []
        self.ECG = pd.Series()
        # Start:
        threading.Thread.__init__(self)
        self.start()


    def updateplot(self):
        peak_i, peak_y, RRIntervals, HR = [],[],[],[]
        peak_t = []

        """ Pull LSL Data """
        try:
            LSLSample, LSLtimestamp = self.peakInlet.pull_chunk()
        except WindowsError:
            # If there's an access error, try again...
            print "WindowsError. Retrying..."
            self.window.after(self.refresh, self.updateplot)
            return  # just in case
        # print "sample:", LSLSample, "\n time", LSLtimestamp

        """ Convert list of lists to simple list and append to existing data """
        sample=[]
        # Datapoints come as one-item lists (since only one channel on this stream)
        for item in LSLSample:
            # For a multi-channel stream, use item[n] for the nth channel
            if self.negative:
                if self.inverted:
                    sample += [-self.scale/(item[0] + self.offset)]
                else:
                    sample += [-self.scale*(item[0] + self.offset)]
            else:
                if self.inverted:
                    sample += [self.scale/(item[0] + self.offset)]
                else:
                    sample += [self.scale*(item[0] + self.offset)]
        # print 'sample:', sample

        """ Set time internally """
        if self.internalTime:
            time = []
            if LSLtimestamp:
                for n in xrange(len(LSLtimestamp)):
                    # update 'clock'
                    self.prevT += self.INTERVAL
                    # add to index list
                    time += [self.prevT]
            # print 'time:', time
        else:
            """ Set time by received """
            # Set start time as first received time:
            if self.startTime == 0.0:
                # (i.e. Do this each time until a startTime has been assigned)
                if not (LSLtimestamp == []):  # wait for first timestamp
                    # set startTime as first timestamp
                    self.startTime = float(LSLtimestamp[0])
            # Start from zero:
            time = [(x - self.startTime) for x in LSLtimestamp]

        """ Trim by time """
        # if len(time) > 1:
        #     print [time[0], time[-1]]
        # Cast new data into pandas Series and append to existing:
        self.ECG = self.ECG.append(pd.Series(sample, time))

        # Trim to the window duration back from the most recent point.
        if self.ECG.size > 1:
            if (self.ECG.index[-1] - self.ECG.index[0]) > self.liveWindowTime:
                self.ECG = self.ECG[self.ECG.index[-1] - self.liveWindowTime:]

        """ Plot """
        # line:
        self.line.set_ydata(self.ECG)
        self.line.set_xdata(self.ECG.index)

        # Ticks by Locator:
        loc = plticker.MultipleLocator(np.ceil(self.liveWindowTime/5.0))
        self.ax.xaxis.set_major_locator(loc)
        self.ax.set_xticklabels([str(int(x)) for x in self.ax.get_xticks()])
        # "{:10.4f}".format(x - self.startTime)

        """ Rescale """
        # Recompute the data limits and update the view:
        self.ax.relim()
        self.ax.autoscale()
        if list(self.ECG.index):
            self.ax.set_xlim([self.ECG.index[0], self.ECG.index[0] + self.liveWindowTime])
            # self.ax.set_xlim([self.ECG.index[0], self.ECG.index[-1]])
            # print [self.ECG.index[0], self.ECG.index[0] + self.liveWindowTime]

        # Label
        if (self.valueText != "") and list(self.ECG):
            # If there *is* a value to be printed:
            self.label.set_text("{lab}: {num:d}".format(lab = self.valueText,
                                                        num = int(self.ECG.iloc[-1])
                                                        )
                                )

        """ Redraw: """
        self.ax.draw_artist(self.ax)
        self.ax.draw_artist(self.line)
        # self.ax.draw_artist(self.peak)
        # self.ax.set_xlim(loc_t[0], loc_t[-1])
        self.canvas.draw()
        self.canvas.flush_events()  # Common practice...? :/
        self.window.after(self.refresh, self.updateplot)
        # else:
        #     # self.window.after(self.refresh, self.updateplot)
        #     pass
        # self.window.after(self.refresh, self.updateplot)

    def run(self):
        # Create a window
        self.window = tk.Tk(className='\n' + self.type + ' Plot')
        self.window.protocol("WM_DELETE_WINDOW", self.terminate)
        self.window.configure(bg='black')
        self.window.tk_setPalette(background='#282820',
                                  foreground='black',
                                  activeBackground='black',
                                  activeForeground='#282820')

        self.fig, self.ax = plt.subplots(1, 1)
        self.fig.set_facecolor('#282820')
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.window)
        self.canvas.get_tk_widget().pack(side='top', fill='both', expand=1)
        self.canvas._tkcanvas.pack(side='top', fill='both', expand=1)

        # Beautify:
        self.ax.spines["top"].set_visible(False)
        self.ax.spines["bottom"].set_visible(False)
        self.ax.spines["right"].set_visible(False)
        self.ax.spines["left"].set_visible(False)
        self.ax.set_axis_bgcolor('black')
        self.ax.set_xlabel("Seconds", fontsize=14, color='white', alpha=0.3)
        self.ax.set_xlim(0, self.liveWindowTime)
        # self.ax.set_ylim(-1.5, 2.5)
        xlist = range(0, int(self.liveWindowTime + 1))
        self.ax.set_xticks(xlist)
        self.ax.set_xticklabels([str(x) for x in xlist],
                                fontsize=14, color='white')
        self.ax.set_autoscaley_on(True)
        self.ax.tick_params(axis="both", which="both", bottom="off", top="off",
                            labelbottom="on", left="off", right="off",
                            labelleft="on", labelsize=14, labelcolor='white')

        self.canvas.show()

        # Initial Data:
        #####################
        self.t = np.linspace(0, self.liveWindow * self.INTERVAL,
                             self.liveWindow)
        # # Centreline:
        # self.ax.plot(self.t, [0, ] * len(self.t),
        #              color='white', alpha=0.3, linewidth=2.0)

        # Set colour
        colDict = {'gold':'#b0c050', 'red':'red', 'blue':'skyblue', 'gray':'dimgray',
                   'grey':'dimgray', 'silver':'lightgrey'}
        try:
            tempCol = colDict[self.col]
        except:
            tempCol = colDict['gold']
        # Initialise line
        self.line, = self.ax.plot(self.t, [0, ] * len(self.t),
                                  color=tempCol,
                                  linewidth=self.thickness, zorder=0)
        # Text display (top right corner):
        if self.valueText != "":
            self.label = self.ax.text(0.98, 0.97,  # Coordinates (percentage)
                                      "", fontweight='bold',
                                      verticalalignment='top',
                                      horizontalalignment='right',
                                      transform=self.ax.transAxes,
                                      fontsize=14, color=tempCol)


        # LSL:
        # first resolve a stream on the lab network
        print"looking for a(n)", self.type, "stream..."
        peakStream = resolve_stream('type', self.type)
        print"found a(n)", self.type, "stream..."
        # create a new inlet to read from the stream
        self.peakInlet = StreamInlet(peakStream[0])

        # Run the animation:
        self.updateplot()

        # Maintain the window even when not updated:
        self.window.mainloop()
        self.terminate()
        return

    def terminate(self):
        count = 1
        hostProc = psutil.Process(os.getpid())
        # print "hostProc:", hostProc
        subProcs = hostProc.children(recursive=True)
        for subProc in subProcs:
            count += 1
            # print "subProc:", subProc
            subProc.kill()
        psutil.wait_procs(subProcs, timeout=5)

        print "Terminated %i window process(es)." % count
        # print "Window terminated."
        sys.stdout.flush()
        hostProc.kill()
        hostProc.wait(5)
        pass
#############################################

"""
###########################################################################
# Main              #     #     #     ###   ##   #
#                   ##   ##    # #     #    # #  #
#                   # # # #   #   #    #    #  # #
#                   #  #  #   #####    #    #   ##
#                   #     #   #   #   ###   #    #
###########################################################################
"""

if __name__ == "__main__":
    # BPM:
    plot_rate = 15
    rate = 500  # ignored if no internalTime
    windowTime = 60  # seconds
    type = 'RR'
    internalTime = False  # use internally generated timestamps rather than received ones
    thickness = 5
    col = 'red'  # gold, red, blue, gray/grey, or silver
    negative = False
    inverted = True  # Take the inverse
    scale = 60000.0  # <float> Multiplies y-values by this (after inverse)
    offset = 32768  # add to reading (before inversion or scaling)
    valueText = "BPM"  # Text, if desired, to indicate the current value (for HR, for example)

    # # Standard Deviation:
    # plot_rate = 15
    # rate = 500  # ignored if no internalTime
    # windowTime = 180  # seconds
    # type = 'HRV_STD'
    # internalTime = False  # use internally generated timestamps rather than received ones
    # thickness = 5
    # col = 'blue'  # gold, red, blue, gray/grey, or silver
    # negative = False
    # inverted = False  # Take the inverse
    # scale = 1.0  # <float> Multiplies y-values by this (after inverse)
    # offset = 0  # add to reading (before inversion or scaling)
    # valueText = ""  # Text, if desired, to indicate the current value (for HR, for example)

    # # ECG
    # plot_rate = 15
    # rate = 500  # ignored if no internalTime
    # windowTime = 5  # seconds
    # type = 'ECG'
    # internalTime = True  # use internally generated timestamps rather than received ones
    # thickness = 2
    # col = 'gold'  # gold, red, blue, gray/grey, or silver
    # negative = True
    # inverted = False  # Take the inverse
    # scale = 1.0  # <float> Multiplies y-values by this (after inverse)
    # offset = 0  # add to reading (before inversion or scaling)
    # valueText = ""  # Text, if desired, to indicate the current value (for HR, for example)

    # # ECG
    # plot_rate = 15
    # rate = 1000  # ignored if no internalTime
    # windowTime = 0.5  # seconds
    # type = 'Stream'
    # internalTime = False  # use internally generated timestamps rather than received ones
    # thickness = 1
    # col = 'gold'  # gold, red, blue, gray/grey, or silver
    # negative = False
    # inverted = False  # Take the inverse
    # scale = 1.0  # <float> Multiplies y-values by this (after inverse)
    # offset = 0  # add to reading (before inversion or scaling)
    # valueText = ""  # Text, if desired, to indicate the current value (for HR, for example)

    Plot = livePlotting(type, plot_rate, rate, windowTime, internalTime,
                        thickness, col, negative, inverted, scale, offset, valueText)


# And they all lived happily ever after.
#              THE END
