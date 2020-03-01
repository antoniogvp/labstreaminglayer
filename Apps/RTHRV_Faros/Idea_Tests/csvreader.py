############################################################################
# Test program to read csv text file
#
# - Matthew Wilson, 2016
############################################################################

import csv
import numpy


with open('PIAJA_run256.txt', 'rb') as ECGfile:  # Read as read-only binary
    ECGrecording = csv.reader(ECGfile, delimiter=',', quotechar='|')
    ECGrecording = numpy.asarray([float(row[1]) for row in ECGrecording])
    # for row in ECGrecording:
    #     print row
