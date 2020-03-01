# -*- coding: utf-8 -*-
###############################################################################
#
#    Rolling Standard Deviation processing for an RR stream.
#
#   Creates a multi-channel LSL stream containing the results of each selected
#   type of smoothing or window length.
#
#    - Matthew Wilson, 2016
#
#   (ASCII FIGlet text generated on patorjk.com/software/taag/)
###############################################################################

# Lab Streaming Layer Import
#############################################
import sys; sys.path.append('liblsl-Python') # help python find pylsl relative to this example program
from pylsl import StreamInlet, resolve_stream, StreamInfo, StreamOutlet, local_clock
# from pylsl import *

# Standard Anaconda:
#############################################
import datetime
import inspect
import matplotlib.pyplot as plt
import numpy as np
from os import environ
import os.path
import pandas as pd
import tkMessageBox
# from scipy.interpolate import interp1d
# from scipy.signal import hilbert, butter, lfilter, filtfilt, freqz




"""##########################
# Save the console log
##########################"""
# Get time:
now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
# Get this module's path:
here = inspect.stack()[0][1]
filepath = os.path.dirname(here) + "/logs"  # extract filename
file = os.path.basename(here).replace(".py","")

print file, "running in", filepath
# Create the desired folder if it doesn't exist:
if not os.path.exists(filepath):
    try:
        os.makedirs(filepath)
    except OSError as exc:  # Guard against race condition
        if exc.errno != errno.EEXIST:
            raise
# Change std.out() to log to both the command line and a text file.
class Logger(object):
    def __init__(self, filename="CommandLog.log"):
        self.terminal = sys.stdout
        self.log = open(filename, "w")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
sys.stdout = Logger(filepath + "/" + file + "_Console_Log_" + now + ".log")



"""
###############################################################################
Parameters:
        :::::::::     :::     :::::::::      :::     ::::    ::::   ::::::::
        :+:    :+:  :+: :+:   :+:    :+:   :+: :+:   +:+:+: :+:+:+ :+:    :+:
        +:+    +:+ +:+   +:+  +:+    +:+  +:+   +:+  +:+ +:+:+ +:+ +:+
        +#++:++#+ +#++:++#++: +#++:++#:  +#++:++#++: +#+  +:+  +#+ +#++:++#++
        +#+       +#+     +#+ +#+    +#+ +#+     +#+ +#+       +#+        +#+
        #+#       #+#     #+# #+#    #+# #+#     #+# #+#       #+# #+#    #+#
        ###       ###     ### ###    ### ###     ### ###       ###  ########
###############################################################################
"""
online = True  # retrieve stream from LSL rather than local file.
plotting = True  # Plot the whole thing when finished.
plottingECG = False  # Plot ECG (only works if offline)
threshold = 1000  # threshold value on acceleration of signal for ectopic filtering

plotThresh = 60  # threshold line to plot

"""
###############################################################################
Initialise processing
        :::::::::::      ::::    :::      :::::::::::      :::::::::::
            :+:          :+:+:   :+:          :+:              :+:
            +:+          :+:+:+  +:+          +:+              +:+
            +#+          +#+ +:+ +#+          +#+              +#+
            +#+          +#+  +#+#+#          +#+              +#+
            #+#          #+#   #+#+#          #+#              #+#
        ###########      ###    ####      ###########          ###
###############################################################################
"""
# If offline, confirm that this is the desired situation, in case this has bee launched from another script, blind:
if not online:
    import Tkinter as tk
    window = tk.Tk(className=" Query")
    window.withdraw()
    response = tkMessageBox.askyesnocancel("Run offline?",
                                           "Are you sure you wish to run the standard deviation processing offline?")
    if response == None:
        sys.exit(0)
    else:
        online = not response

offline = not online
"""
HRV parameters:
"""
# Try different window lengths and smoothing:
# The following 4 items must have the same length first dimension:
# trims = [10, ]  # Length to which to trim the sample for each test
# stdsmoothing = [10, ]  # how much to smooth, if smoothing
# hrv = [[], ]
# hrvsmooth = [[], ]

trims = [12, 12, 12 ]  # Length to which to trim the sample for each test
stdsmoothing = [7, 15, 20 ]  # how much to smooth, if smoothing
hrv = [[], [], []]  # to log the whole run (with various trimming levels)
hrvsmooth = [[], [], []]  # to log the whole run (with trimming *and* smoothing)

# trims = [10, 10, 10 ]  # Length to which to trim the sample for each test
# stdsmoothing = [10, 10, 10 ]  # how much to smooth, if smoothing
# hrv = [[], [], []]  # to log the whole run (with various trimming levels)
# hrvsmooth = [[], [], []]  # to log the whole run (with trimming *and* smoothing)


sampleT = []  # to log the whole run's timestamps

# Number of RR intervals between which to define the main window
# (samplesize >= max(trims))
samplesize = max(trims)

# Because everyone's heart has a different initial SD value, there is no
# good initial value to start from, so we might as well start from 0.
stdsmooth = [0, ] * len(trims)
# stdsmooth = [plotThresh, ] * len(trims)


"""
Initialise LSL:
"""
if online:
    """ INLET """
    # First resolve an RR stream on the lab network
    print "\nlooking for an RR stream..."
    RRStream = resolve_stream('type', 'RR')
    print "found an RR stream."
    # create a new inlet to read from the stream
    # (Don't attempt to recover if data lost)
    RRInlet = StreamInlet(RRStream[0], recover=False)

    """ OUTLET """
    # Now create a new stream info object:
    # (here we set the name to Faros, the content-type to ECG, 1 channel, frequency = rate,
    # float-valued data, and the MAC address)
    # The last value, the MAC address of the device, is a local identifier for the stream
    # (you could also omit it but interrupted connections wouldn't auto-recover).
    # streamConfig = StreamInfo('Emulator', streamType, 1, rate, 'float32', 'Emulator');
    streamID = 'RR_STD_CALC_' + environ['COMPUTERNAME']
    channel_count = len(trims)
    print "Created outlet with ID:", streamID, 'with', channel_count, 'channel(s)'
    streamConfig = StreamInfo('RR_STD_CALC', 'HRV_STD', channel_count, 100, 'float32', streamID);
    # next add an outlet to the list
    RRoutlet = StreamOutlet(streamConfig)
    print "LSL channels opened\n"

"""
###############################################################################
Read
        :::::::::       ::::::::::          :::          :::::::::
        :+:    :+:      :+:               :+: :+:        :+:    :+:
        +:+    +:+      +:+              +:+   +:+       +:+    +:+
        +#++:++#:       +#++:++#        +#++:++#++:      +#+    +:+
        +#+    +#+      +#+             +#+     +#+      +#+    +#+
        #+#    #+#      #+#             #+#     #+#      #+#    #+#
        ###    ###      ##########      ###     ###      #########
###############################################################################
"""
# Only takes single-series recordings - i.e. not the old ones made with ProComp
if not online:
    """################### CHOOSE FILES ###################"""

    # session = "Pilot_Experiments\\VELPED_500Hz_3_electrode_pilot_replay"
    # session = "Experiments\\csv\\SRIVAC_500Hz_replay"
    # session = "Experiments\\csv\\Invalid\\RAJARA_500Hz"
    # session = "Experiments\\csv\\Uncertain\\BOUATH_500Hz"
    # session = "Experiments\\csv\\BHOHEM_500Hz"
    # session = "Experiments\\csv\\SENMEH_500Hz"
    # session = "Experiments\\csv\\Uncertain\\MALAMR_500Hz"
    # session = "Experiments\\csv\\Uncertain\\BOVANG_500Hz"
    # session = "Experiments\\csv\\ROYRAP_500Hz"
    # session = "Experiments\\csv\\TOSCHI_500Hz"
    # session = "Experiments\\csv\\JAHEMI_500Hz"
    # session = "Experiments\\csv\\Uncertain\\DELFAB_500Hz"
    # session = "Experiments\\csv\\BRIMIG_500Hz"
    # session = "Experiments\\csv\\SAUPIE_500Hz"
    # session = "Experiments\\csv\\GANSRE_500Hz"
    session = "Experiments\\csv\\GIAGUI_500Hz"


    filename = '..\\..\\..\\Results\\' + session + '__RR.txt'
    ECGfile = '..\\..\\..\\Results\\' + session + '__ECG.txt'
    Markfile = '..\\..\\..\\Results\\' + session + '__StrMarkers.txt'


    """################### EXTRACT DATA ###################"""

    # Retrieve all data:
    fullData = pd.read_csv(filename, index_col=0, skipinitialspace=True, squeeze=True)
    ECGData = pd.read_csv(ECGfile, index_col=0, skipinitialspace=True, squeeze=True)
    Markers = pd.read_csv(Markfile, index_col=0, skipinitialspace=True, squeeze=True)
    # print fullData

    # break it down:
    # Faros device has binary overflow and is in milliseconds:
    data = (fullData.values + 2**15)#/1000.0
    # Start time from zero:
    times = (fullData.index) - fullData.index[0]
    # print data
    # print times
    RR = pd.Series(data, times)

    # same for ECG
    ECGtimes = (ECGData.index) - fullData.index[0]
    ECGData = pd.Series(ECGData.values, ECGtimes)

    # same for markers:
    # (remove keystrokes:)
    Markers = Markers.ix[np.logical_not(Markers.str.contains('K:'))]
    Marktimes = (Markers.index) - fullData.index[0]
    Markers = pd.Series(Markers.values, Marktimes)
    # print Markers

    print "Data imported"

"""
###############################################################################
Loop:
        :::              ::::::::        ::::::::       :::::::::
        :+:             :+:    :+:      :+:    :+:      :+:    :+:
        +:+             +:+    +:+      +:+    +:+      +:+    +:+
        +#+             +#+    +:+      +#+    +:+      +#++:++#+
        +#+             +#+    +#+      +#+    +#+      +#+
        #+#             #+#    #+#      #+#    #+#      #+#
        ##########       ########        ########       ###
###############################################################################
"""
if online:
    # set first samples at constant 70 bpm (60/70 * 1000 milliseconds):
    rr = pd.Series([60.0/70 * 1000, ] * samplesize, index=[0.0, ] * samplesize)
    RR = pd.Series()
else:
    rr = pd.Series([RR.iloc[0], ] * samplesize, index=[0.0, ] * samplesize)
rrfull = rr.copy(True)
# rrfull will contain every value recorded
# rr will have ectopic beats removed

startTime = -1.0

print "Processing IBI series. Calculating rolling standard deviation..."


def advanceAndCheck(rr,newsample,newtimestamp,threshold=0.0):
    """Takes in new sample, checks if acceleration (difference
    of difference) of the new sample is above the threshold.
    Returns updated rr (with new value appended, but length still
    samplesize) and a boolean for if an ectopic beat was detected.

    threshold=0 : no threshold, just advance rr and return [rr, False]."""
    try:
        rr = rr.iloc[1:].append(pd.Series([newsample, ],
                                          index=[newtimestamp, ]))
        if threshold == 0.0:
            return rr, False
        else:
            rrvel = rr.diff(1)
            rraccel = rrvel.diff(1)
            if np.abs(rraccel.iloc[-1]) < threshold:
                return rr, False
            else:
                return rr, True
    except:  # Error
        print "Error!"
        return rr, True

ects = 0  # ectopic counter
i = 0  # main loop iteration counter
while True:
    """
    ############################################################################
    # Cycle chunks or load recording:
    #############################################
    """

    """
    Pull chunk or recording:
    """
    if online:
        # Online:
        try:
            RRi, Ti = RRInlet.pull_chunk(timeout=1.5)  # lists of lists
            # of format:
            # RRi = [[rr,], [rr,], [rr,], [rr,],...]
            # Ti = [t, t, t, t,...]
            # RRi, Ti == [], None if timeout reached with no sample found

            if RRi == []:
                print "No more samples to pull..."
                RRInlet.__del__()
                break
        except WindowsError:
            # skip iteration and try again
            # print "Windows access exception on loop", i
            i += 1
            continue

        if RRi != []:
            for n in xrange(len(RRi)):  # each received sample in the chunk
                RRi[n] = (RRi[n][0] + 2 ** 15) #/ 1000.0  # Compensate for Faros silliness

            # RR = RR.append(pd.Series(RRi, index=Ti))
        else:
            # skip iteration and try again
            i += 1
            continue

    else: # Offline:
        if i > 0:
            print "End of recording..."
            break

        RRi = list(RR.values)
        Ti = RR.index

    """
    ############################################################################
    # Cycle within chunk or recording:
    #############################################
    """
    for n, rri in enumerate(RRi):
        tLSL = ti = Ti[n]
        # print 'ti', ti, 'rri', rri
        # We now have an rri, ti pait for each sample

        rrfull, ectopic = advanceAndCheck(rrfull, rri, ti, threshold)
        """
        Update if not ectopic:
        """
        if not ectopic:
            rr, ectopic = advanceAndCheck(rr, rri, ti)
            # This will change the value of ectopic, since it can only be False
            # under this condition and giving no threshold to advanceAndCheck
            # also returns False.


        """
        Skip STD calcs if ectopic:
        """
        if ectopic:
            # Ectopic or error
            ects += 1
            continue  # restart the loop, ignoring what comes below.

        """
        Set time index:
        """
        # Set time by received (for plotting purposes)
        # Set start time as first received time:
        if startTime == -1.0:
            # (i.e. Do this each time until a startTime has been assigned)
            if not (ti == []):  # wait for first timestamp
                # set startTime as first timestamp
                startTime = ti
        # Start from zero:
        ti -= startTime
        sampleT += [ti, ]  # append to list of timestamps

        if plotting and online:
            # Record RR for plot
            RR = RR.append(pd.Series([rri,], index=[ti,]))

        # Remove offset:
        rrsym = rr - rr.mean()
        # rrsym = rr - 0.8

        # plt.figure(4)
        # plt.plot(rrsym)
        # print rr

        """
        HRV
        """
        for x in xrange(len(trims)):  #TODO: This loop only useful for testing smoothing.
            #TODO: trim is only necessary if using multiple configs (len(trim) > 1):
            rrtrim = rrsym.copy().iloc[-trims[x]:]  # get last trims[x] samples
            # plt.figure(4)
            # plt.plot(rrtrim - x * 0.2)
            stdev = rrtrim.std()
            # plt.plot(RR.index[i], stdev, 'o')
            if stdsmoothing[x]:
                stdsmooth[x] = ((stdev + stdsmooth[x] * stdsmoothing[x]) /
                                (stdsmoothing[x] + 1))
                hrvsmooth[x] += [stdsmooth[x], ]  # for record of run
            else:
                hrvsmooth[x] += [stdev, ]  # for record of run

            # Unsmoothed version:
            hrv[x] += [stdev, ]  # for record of run
            # print "hrv[{}]:".format(x), stdsmooth[x]
        # print rrsym, stdsmooth

        """ STREAM OUT """
        if online:
            RRoutlet.push_sample(stdsmooth, tLSL)  # push all smoothed types

    """ ITERATE """
    i += 1  # loop counter

# the ectopic detection algorithm always discards the ectopic IBI *and* the two after it,
# since it can only accept beats which do not deviate beyond the threshold from the trend of
# the previous *2* IBIs. Therefore, unless there are two successive ectopic beats, the count
# of discarded points will always be 3 times the actual number of ectopic beats (or arythmias).
ects = int(ects/3.0)
print "Number of ectopic beats found:", ects
print "Out of a total of:", len(hrvsmooth[0]) + ects

"""
###############################################################################
Plot at end:
        :::::::::       :::              ::::::::       :::::::::::
        :+:    :+:      :+:             :+:    :+:          :+:
        +:+    +:+      +:+             +:+    +:+          +:+
        +#++:++#+       +#+             +#+    +:+          +#+
        +#+             +#+             +#+    +#+          +#+
        #+#             #+#             #+#    #+#          #+#
        ###             ##########       ########           ###
###############################################################################
"""

if plotting:

    plt.figure(1)
    plt.title('Rolling Standard Deviation of IBI series')

    # ax1 = plt.subplot(211) # for either offline or online
    ax1 = plt.subplot2grid((3,1),(0,0),rowspan=2) # for either offline or online

    """ Plot """
    for i in xrange(len(trims)):
        # hrv[i] = pd.Series(hrv[i], index=RR.index)
        # plt.plot(hrv[i], lw=3, alpha=0.5, label='HRV %d' % trims[i])
        if hrvsmooth[i] != []:
            hrvsmooth[i] = pd.Series(hrvsmooth[i], index=sampleT)
            ax1.plot(hrvsmooth[i], #'o-',
                     lw=2, alpha=0.6,
                     label=('{}-sample window, smooth-weighting {}'
                            .format(trims[i], stdsmoothing[i])))
            plt.rc('legend', fontsize=10)  # legend fontsize
    # Threshold line:
    for i in range(15):
        ax1.plot([0, max(hrvsmooth[0].index)], [plotThresh, plotThresh],
                 'k', alpha=0.02, lw=i * 1.5)
    ax1.plot([0, max(hrvsmooth[0].index)], [plotThresh, plotThresh], 'k')

    ax1.grid(alpha=0.5)
    ax1.legend(loc='best')
    plt.ylabel('IBI standard deviation (ms)')
    # plt.xlabel('time (seconds)')

    """ Markers """
    if offline:
        for i, mark in enumerate(Markers):
            if 'E:' in mark:
                ax1.axvline(x=Markers.index[i], alpha=1, color='blue')
                # ax1.text(Markers.index[i], plotThresh, Markers.values[i],
                #          rotation=90, size=6)



            elif 'T:' in mark:
                text = Markers.values[i]
                for cut in "T: 1. 2. 3. 4. 5. 6. 7. 8. 9.".split(" "):
                    text = text.replace(cut, "")
                ax1.axvline(x=Markers.index[i], alpha=0.4, color='green')
                ax1.text(Markers.index[i] + 3, plotThresh* 2/3,  # x-offset by 3 seconds
                         text,
                         rotation=0, size=6, color='green')
            elif 'C:' in mark or 'P:' in mark:
                ax1.axvline(x=Markers.index[i], alpha=0.2, color='red')
            else:
                # ax1.axvline(x=Markers.index[i], alpha=0.1, color='black')
                pass

    """ RR and ECG """
    if offline and plottingECG:
        # ax2 = plt.subplot(413, sharex=ax1)  # for ECG
        ax2 = plt.subplot2grid((6,1), (4,0), sharex=ax1)  # for ECG
    else:
        # ax2 = plt.subplot(212, sharex=ax1)  # for ECG
        ax2 = plt.subplot2grid((3,1), (2,0), sharex=ax1)  # for ECG
        plt.xlabel('time (seconds)')
    ax2.plot(RR, #'o-',
             lw=1, color='red')
    ax2.grid(alpha=0.5)
    plt.ylabel('RR\n(ms)')

    if offline and plottingECG:
        # ax3 = plt.subplot(414, sharex=ax1)  # for ECG
        ax3 = plt.subplot2grid((6,1), (5,0), sharex=ax1)  # for ECG
        ax3.plot(ECGData, lw=1)
        plt.ylabel('ECG\n(uV)')
        plt.xlabel('time (seconds)')


    print "Displaying plot... (close plot to end script)"
    plt.show()
print "HRV standard deviation script done"

# ...and they lived happily ever after.
#
#            ---THE END---