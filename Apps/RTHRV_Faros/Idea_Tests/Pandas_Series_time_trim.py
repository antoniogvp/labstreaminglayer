# Testing list-trimming
import pandas as pd
import numpy as np
import time
import tkFileDialog as filedialog
import tkMessageBox


# Sub-divide:
time1 = [1.5, 2, 3, 4, 5, 6, 7, 8, 9]
ECG1 = [2, 1, 3, -2, 0, 0, 2, 4, -2]
peakst1 = [3, 8]
peaks1 = [3, 4]
intervals1 = [3, None]

time2 = [6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
ECG2 = [0, 2, 4, -2, 0.5, 1, 0, 3, -1, 1]
peakst2 = [8, 13]
peaks2 = [4, 3]
intervals2 = [None, 5]

time3 = [10, 11, 12, 13, 14, 15]
ECG3 = [0.5, 1, 0, 3, -1, 1]
peakst3 = [13, ]
peaks3 = [3, ]
intervals3 = [5, ]

Series1 = pd.Series(ECG1, time1, dtype=np.float32, name='ECGsample')
print Series1
cut = 2.5
print Series1[:cut].append(Series1[cut+0.000000001:].iloc[:1])
print 2**15
print "{lab}: {num:d}".format(lab = 'BPM', num = int(Series1.iloc[-1]))

# Extract type from file name by breaking at "__" and taking the
# last bit after that, or, if no "__", then take the first bit
# before a "_" (should be the run name). Then chop off the
# file extension if it exists. If no "_", you should get the
# whole file name.
test = "test__ext_ens.txt"
if "__" in test:
    print test.split("__")[-1].split(".")[0]
else:
    print test.split("_")[0].split(".")[0]

stream = []
for i in xrange(10):
    stream += [i**2]
    print stream[i]
print stream

import os
## first file in current dir (with full path)
file = os.path.join(os.getcwd(), os.listdir(os.getcwd())[0])
print file
print os.path.dirname(file) ## directory of file
print os.path.basename(file)

print len(Series1)

for item in enumerate(time3):
    print item

#############################################################################
completeList= ('L', 'm', 'K', 'r', 'g', 'W', 'p')
responseList = ('L', 'm', 'K', 'r', 'g', 'r', 'q')

completeList= [x.upper() for x in completeList]
responseList = [x.upper() for x in responseList]
print completeList
print responseList

# from Command_Line_Test import process_args
# from collections import OrderedDict
# import sys
# argDict = OrderedDict([
#             ("help",
#              [None, "Display this help text", "h", ""]),])
#
# process_args(argDict, sys.argv[1:])

# os.system("Command_Line_Test.py -h")
# import inspect
# print inspect.stack()[0][1]
#
# print Series1.ix[np.logical_not(Series1.isin([0,]))]
#
# string = list('abcdefghi')
# string = ['a:',] * 4 + ['b:',] * 5
# SeriesS = pd.Series(string, time1, name='Strings')
# print SeriesS.ix[np.logical_not(SeriesS.isin(['a',]))]
# print SeriesS.ix[np.logical_not(SeriesS.str.contains('a'))]

def aug(ser):
    return ser + 1

print Series1
print aug(Series1)
print Series1
print Series1.iloc[-50:]
print Series1.size



print ""

print list(Series1.index)
print list(Series1.values)
d = dict(x=list(Series1.index), y=list(Series1.values))
print d
print d.keys



# else:
#     print test.split(".")[0]

# Sub-divide
# timeDF1 = pd.DataFrame({'time': time1, 'ECG': ECG1})
# peaksDF1 = pd.DataFrame({'time': peakst1,
#                          'peaks': peaks1,
#                          'intervals': intervals1,
#                          })
# timeDF2 = pd.DataFrame({'time': time2, 'ECG': ECG2})
# peaksDF2 = pd.DataFrame({'time': peakst2,
#                          'peaks': peaks2,
#                          'intervals': intervals2,
#                          })
# timeDF1 = pd.DataFrame({'ECG': ECG1},
#                        index=time1)
# peaksDF1 = pd.DataFrame({'peaks': peaks1,
#                          'intervals': intervals1,
#                          },
#                         index=peakst1)
# timeDF2 = pd.DataFrame({'ECG': ECG2},
#                        index=time2)
# peaksDF2 = pd.DataFrame({'peaks': peaks2,
#                          'intervals': intervals2,
#                          },
#                         index=peakst2)
# timeDF3 = pd.DataFrame({'ECG': ECG3},
#                        index=time3)
# peaksDF3 = pd.DataFrame({'peaks': peaks3,
#                          'intervals': intervals3,
#                          },
#                         index=peakst3)


# start = time.time()
# concatA = pd.concat([merged1, merged3])
# mid1 = time.time()
# appendA = merged1.append(merged3)
# mid2 = time.time()
# mergedC = pd.merge(merged1, merged3,
#                    on=list(merged1.columns.values),
#                    left_index=True, right_index=True, how='outer')
# mid3 = time.time()
# combineA = merged1.combine_first(merged3)
# end = time.time()

# # Retain a certain length:
# last10 = mergedA.iloc[-10:]

# # Append a new row:
# mergedA = mergedA.append(pd.DataFrame([[0, None, None], ],
#                                       index=[17, ],
#                                       columns=mergedA.columns.values))

