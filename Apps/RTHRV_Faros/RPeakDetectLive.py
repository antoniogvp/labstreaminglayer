# -*- coding: utf-8 -*-
###############################################################################
# Primative Offline QRV-Complex Identifier
##########################################
# Adapted from rpeakdetect.py from:
# https://github.com/tru-hy/rpeakdetect
#
# Adapted by Matthew Wilson
###############################################################################

# matplotlib config:
# C:\Anaconda2\Lib\site-packages\matplotlib\mpl-data\matplotlibrc
# The platform-dependent plot variable is the first one:
# >>> backend      : TkAgg
# or similar. Tk should work across platforms, but the others
# depend on QuickTime, or wxPython, or similar

# Standard Anaconda:
#############################################
import numpy as np
import scipy.signal
import scipy.ndimage

"""
###############################################################################
# Functions         #####   #   #   ##   #    ####
#                   #        # #    # #  #   #
#                   ####      #     #  # #    ###
#                   #        # #    #   ##       #
#                   #       #   #   #    #   ####
###############################################################################
"""
"""
############################################################################
# Original Functions
#############################################
"""


# FUNCTION: Run with plotting
#############################################
# i.e. include matplotlib
#########################
def plot_peak_detection(ECG, rate):
    import matplotlib.pyplot as plt
    dt = 1.0 / rate  # "Period" or "interval"
    # Create linearly-spaced time vector
    # (actually 'recreate' since it existed in the csv file,
    # but this means this can be adapted to other file styles):
    # linspace(start, end, number_of_points)
    t = np.linspace(0, len(ECG) * dt, len(ECG))

    # Returns the indeces of detections:
    peak_i = detect_beats(ECG, rate)

    # Plot:
    plt.plot(t, ECG)

    # Use those indeces to add points on the previous plot:
    plt.scatter(t[peak_i], ECG[peak_i], color='red')

    plt.show()
#############################################


# FUNCTION: Run peak detection
#############################################
def detect_beats(ECG,    # The raw ECG signal
                 rate,   # Sampling rate in HZ
                 # Low frequency of the band pass filter
                 lowfreq=5.0,
                 # High frequency of the band pass filter
                 highfreq=15.0
                 ):
    """
    ECG heart beat detection based on
    http://link.springer.com/article/10.1007/s13239-011-0065-3/fulltext.html
    with some tweaks (mainly robust estimation of the rectified signal
    cutoff threshold).
    """

    # # Convert window size from seconds to samples (int):
    # # ransac_window_size = int(ransac_window_size * rate)
    # ransac_window_size = len(ECG)

    # scipy.signal.butter(order, crit_frequency, type)
    # returns tuple of array of coefficients of the B/A transfer fxn
    lowpass = scipy.signal.butter(1, highfreq / (rate / 2.0), 'low')
    highpass = scipy.signal.butter(1, lowfreq / (rate / 2.0), 'high')
    # TODO: Could use an actual bandpass filter

    # scipy.signal.filtfilt(b, a, signal_to_be_filtered)
    # lowpass and highpass are already in (b,a) form.
    ECG_low = scipy.signal.filtfilt(*lowpass, x=ECG)
    ECG_band = scipy.signal.filtfilt(*highpass, x=ECG_low)
    # We now have a band-passed signal

    # NOTE: the butterworth filter can be used in 'band' mode,
    # which could perhaps save some time here (as noted above with TODO)...

    # Square (=signal power) of the first difference of the signal
    # numpy.diff(signal, n=1, axis=-1)
    # (returns a list of the differences between points, i.e. x => dx)
    dECG = np.diff(ECG_band)
    dECG_power = dECG**2
    # We now have the first 'derivative' of the band-passed signal
    # And the signal 'power' (square of rate of change of signal)

    # Robust threshold and normalizator estimation:
    ###############################################
    # # Use the standard deviations of power/2 as thresholds per window:
    threshold = 0.5 * np.std(dECG_power)
    max_power = np.max(dECG_power)
    # If below threshold, consider power to be zero:
    dECG_power[dECG_power < threshold] = 0

    # Normalise to power peak
    dECG_power /= max_power
    # Trim power peaks to 1.0
    dECG_power[dECG_power > 1.0] = 1.0
    # and square the resulting, trimmed set of above-threshold values:
    square_dECG_power = dECG_power**2

    # shannon_energy = -(filtered_power^2)*ln(filtered_power^2)
    shannon_energy = -square_dECG_power * np.log(square_dECG_power)
    # SAFETY CHECK:
    # ~ is 'not' in this case, so:
    # if not finite (inf. or NaN), set to zero
    # (e.g. log(0) = -inf.):
    shannon_energy[~np.isfinite(shannon_energy)] = 0.0

    # mean_window_length = 1 + rate/8 samples (= 33 samples for 256Hz)
    mean_window_len = int(rate * 0.125 + 1)
    # Convolve shannon_energy with (1.0 divided into mean_window_length parts)
    # (Multiplying a list by int(n) gives a new list of n copies of the list.)
    # I think this just smears the shannon_energy across mean_window_length.
    lp_energy = np.convolve(shannon_energy,
                            [1.0 / mean_window_len] * mean_window_len,
                            mode='same'  # fit to length of longest input
                            )
    # lp_energy = scipy.signal.filtfilt(*lowpass2, x=shannon_energy)

    # Apply a gaussian filter with SD = rate/8
    lp_energy = scipy.ndimage.gaussian_filter1d(lp_energy, rate / 8.0)
    # Get the 'derivative' of that:
    lp_energy_diff = np.diff(lp_energy)

    # Check for every point where the values cross zero going down
    # i.e. first value > 0 , next value < 0:
    zero_crossings = (lp_energy_diff[:-1] > 0) & (lp_energy_diff[1:] < 0)

    # Covert the boolean array to a list of indexes for the True values:
    zero_crossings = np.flatnonzero(zero_crossings)
    # and left-shift by 1 index:
    zero_crossings -= 1
    # So we've identified the points where lp_energy_diff dips below zero.
    # i.e. the crests of lp_energy
    # i.e. the high zones of shannon_energy smeared over mean_window_length

    # Now, the detected point should be within a window of the actual R-peak,
    # limited by how fast a heart can beat. There cannot be 2 peaks within
    # the window so, for heart-rates up to 4Hz (240 bpm!), 0.25 s should
    # suffice. Get that number in samples (+1 so never 0):
    peakWindow = int(1 + 0.25 * rate)
    # print "peakWindow:", peakWindow

    # Identify the maximum within peakWindow around each zero_crossing
    rPeaks = []
    for i in zero_crossings:
        low = i - peakWindow
        if low < 0:
            low = 0
        high = i + peakWindow
        if high > (len(ECG) - 1):
            high = len(ECG) - 1
        # get index within the window:
        # local = np.argmax(ECG[i - peakWindow:i + peakWindow], axis=0)
        local = np.argmax(ECG[low:high])
        # append
        rPeaks.append(local + low)

    return rPeaks
#############################################

"""
###############################################################################
# Main              #     #     #     #   ##   #
#                   ##   ##    # #    #   # #  #
#                   # # # #   #   #   #   #  # #
#                   #  #  #   #####   #   #   ##
#                   #     #   #   #   #   #    #
###############################################################################
"""
if __name__ == '__main__':
    """Code to run if this script is being run by itself."""
    import sys

    # FUNCTION: Import ECG recording as a 1D array
    #############################################
    def importRecording(recordingFile, fileDelim=',', column=1):
        """Imports recordingFile and converts and returns 1D array for
        transmission.

        Defaults to comma-delimited csv-type file with values in the second
        column, but these can be changed with \"fileDelim\" and \"column\"
        parameters (columns starting from 0)."""
        import csv
        with open(recordingFile, 'rb') as ECGfile:  # Read as read-only binary
            ECGrecording = csv.reader(ECGfile, delimiter=fileDelim,
                                      quotechar='|')
            ECGrecording = np.asarray([float(row[column])
                                       for row in ECGrecording])
            # for row in ECGrecording:
            #     print row
        return ECGrecording
    #############################################

    plot = True
    # rate = float(sys.argv[1])
    rate = float(256)

    # Import the values column from a multi-column ECG csv-like file
    # (as list):
    ECG = importRecording("PIAJA_trimmed_run256.txt")

    # Plot if requested:
    if plot:
        plot_peak_detection(ECG, rate)
    else:
        peaks = detect_beats(ECG, rate)
        # Writes to system display (like print):
        sys.stdout.write("\n".join(map(str, peaks)))
    sys.stdout.write("\n")
