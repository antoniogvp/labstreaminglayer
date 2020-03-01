# Testing list-trimming
import pandas as pd
import numpy as np
import time
import tkMessageBox


#############################################
def getNew(newYlist, newTlist, oldTlist):
    """Trims a new sample of any repeat samples
    by comparing time values with the last sample's
    time values. Can take an empty oldTlist.
    Returns: newYlist, newTlist"""
    if (oldTlist == []):  # No old values:
        return newYlist, newTlist
    else:
        # last old t-value
        lastT = oldTlist[-1]
        # Return distance from end of list at which that lastT was found.
        # This works even if there is a list of 0s at the beginning of
        # the run:
        try:
            revList = list(newTlist)
            revList.reverse()
            fromEnd = revList.index(lastT)
        except:  # if not found, assume either completely new or empty:
            return newYlist, newTlist

        if fromEnd != 0:  # Trim:
            newTlist = newTlist[-fromEnd:]
            newYlist = newYlist[-fromEnd:]
        else:  # We have nothing new:
            return [], []
    return newYlist, newTlist
#############################################


#############################################
def groupListAlign():
    """A list alignment function for creating spreadsheet-type data.
    Takes a set of lists on a common x-axis, in style:
    [[[x...], [y...]],
     [[x...], [y...]],
     [[x...], [y...]],
     ...]
    where some lists might be sparse (e.g. a scatter plot to be superimposed
    on a continuous line, and returns a set in the style of:
    [[ 0, 1, 2, 3, 4, etc.],
     [ 1, 2, 3,-2, 0, etc.],
     [  ,  , 3,  ,  , etc.],
     [  ,  , 5,  ,  , etc.],
     [  ,  ,.2,  ,  , etc.]]"""
#############################################

# listFull = range(0, 20, 2)
# listFullT = range(0, 10)

# # listRev = list(listFull)
# # listRev.reverse()
# # print listRev, listFull

# list1 = listFull[0:7]
# list1T = listFullT[0:7]
# list2 = listFull[7:10]
# list2T = listFullT[7:10]
# print list1
# print list2
# print list1 + list2

# list3, list3T = getNew(list2, list2T, list1T)
# print list3
# print list1 + list3

# Full
# time = [1.5, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
# ECG = [2, 1, 3, -2, 0, 0, 2, 4, -2, 0.5, 1, 0, 3, -1, 1]
# peakst = [3, 8, 13]
# peaks = [3, 4, 3]
# intervals = [3, None, 5]

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

# time2 = []
# ECG2 = []
# peakst2 = []
# peaks2 = []
# intervals2 = []

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
timeDF1 = pd.DataFrame({'ECG': ECG1},
                       index=time1)
peaksDF1 = pd.DataFrame({'peaks': peaks1,
                         'intervals': intervals1,
                         },
                        index=peakst1)
timeDF2 = pd.DataFrame({'ECG': ECG2},
                       index=time2)
peaksDF2 = pd.DataFrame({'peaks': peaks2,
                         'intervals': intervals2,
                         },
                        index=peakst2)
timeDF3 = pd.DataFrame({'ECG': ECG3},
                       index=time3)
peaksDF3 = pd.DataFrame({'peaks': peaks3,
                         'intervals': intervals3,
                         },
                        index=peakst3)


# Add the peaks columns to the ECG column, leaving "nan" where there is no
# corresponding data in one or the other of the data frames:
merged1 = pd.merge(timeDF1, peaksDF1,
                   left_index=True, right_index=True, how='outer')
merged1a = timeDF1.combine_first(peaksDF1)
merged2 = pd.merge(timeDF2, peaksDF2,
                   left_index=True, right_index=True, how='outer')
merged3 = pd.merge(timeDF3, peaksDF3,
                   left_index=True, right_index=True, how='outer')

# merged1['peaks'] = [None, ] * len(merged1['peaks'])
# for i in xrange(len(merged1.index.values)):
#     merged1.index.values[i] = 0

# Merge the last two set of data with no repeats:
mergedA = pd.merge(merged1, merged2,
                   on=list(merged1.columns.values),
                   left_index=True, right_index=True, how='outer')
merged1 = merged1.combine_first(merged1)
mergedB = merged1.combine_first(merged2)
mergedB = mergedB.combine_first(merged1.dropna())
# Remove all pre-existing data to leave only the new rows:
# (Using local indexing)
newData = mergedA.iloc[len(merged1.index.values):]

start, mid1, mid2, end = float, float, float, float

start = time.time()
concatA = pd.concat([merged1, merged3])
mid1 = time.time()
appendA = merged1.append(merged3)
mid2 = time.time()
mergedC = pd.merge(merged1, merged3,
                   on=list(merged1.columns.values),
                   left_index=True, right_index=True, how='outer')
mid3 = time.time()
combineA = merged1.combine_first(merged3)
end = time.time()

# # Retain a certain length:
# last10 = mergedA.iloc[-10:]

# # Append a new row:
# mergedA = mergedA.append(pd.DataFrame([[0, None, None], ],
#                                       index=[17, ],
#                                       columns=mergedA.columns.values))

print "merged1:\n", merged1
print "merged1a:\n", merged1a
print "merged2:\n", merged2
# print "newData:\n", newData
# # print "last10:\n", last10
print "mergedA:\n", mergedA
print "mergedA sliced:\n", mergedA.iloc[:3]
print "mergedA sliced:\n", mergedA.iloc[3:]
# print (True * "a") + (True * "b")

# names = mergedA.columns.values
# names = pd.Series(mergedA.columns.values, index=mergedA.columns.values)
names = pd.DataFrame(columns=mergedA.columns.values)
# names = names.rename_axis("time")

# names.index.name = "time"
# string = ""
# for name in names.reset_index().columns.values:
#     string = string + "{:15s},".format(" " + name)
# print string

listDict = pd.DataFrame(columns=['A', 'B'], index=[0, 1, 2.5])
# listDict['A'] = [0, 1, 2]
print listDict
print locals()['listDict']
marker = ""
if marker:
    print marker
# print 'A' in listDict.columns.values
# print list(np.array([1,3])) == list(np.array([2,3]))
# print [] == []
# print np.array([]).size == 0

# print mergedA.iloc[0:0].append(names, ignore_index=True)

# print "concatA:\n", concatA
# print "appendA:\n", appendA
# print "mergedC:\n", mergedC
# print "combineA:\n", combineA

# print "Concat time:", (mid1 - start) * 1000
# print "Append time:", (mid2 - mid1) * 1000
# print "Merge time:", (mid3 - mid2) * 1000
# print "Combine time:", (end - mid3) * 1000

# print "list append:", [] + [None, ] + [0, ] + [1, 2, 3]
# interval = list(np.diff([1, 2, 5]))
# print "list diff:", interval
# print "list inv:", [1.0 / i for i in interval]
# try:
#     result = 1 - [2, ][0]
# except:
#     result = 'Exception'
# print "Result:", result
# print "list non-equality:", [] != []
# print "mergedB:\n", mergedB

# print "peaksT:", list(mergedA['peaks'].dropna().index.values)
# print "peaks: ", list(mergedA['peaks'].dropna())
# lastPeakTlast = merged1['peaks'].dropna().iloc[::-1].index.values[0]
# oldLen = len(merged1.loc[:lastPeakTlast].index.values)
# lastPeakT = mergedA['peaks'].dropna().iloc[::-1].index.values[0]
# print "peaks last index: ", lastPeakT
# print ("mergedA selection up to last new\n" +
#        "peak since last peak in merged1:\n" +
#        str(mergedA.iloc[oldLen:].loc[:lastPeakT]))


# printStr = newData.to_csv(header=False)
# print "printStr:\n", printStr

# # Formatting printing:
# #############################################
# colWidths = [16, 8, 12, 8]  # minimum column widths in characters
# decWidths = [9, 4, 9, 4]  # decimal places per column

# # print (["", ] + list(mergedA.columns.values))

# # Expand columns to fit headers if necessary:
# column = 0
# for key in (["", ] + list(mergedA.columns.values)):
#     colWidths[column] = max(colWidths[column], len(str(key)))
#     column += 1


# def printList(printList, colWidths, decWidths, end="\n", sep=", "):
#     """Takes a list and returns a formatted csv-type string according
#     to the corresponding list of column widths (colWidths) and
#     decimal places per column (decWidths), boths list of ints."""

#     def isfloat(value):
#         try:
#             float(value)
#             return True
#         except ValueError:
#             return False

#     # Initialise print string:
#     printStr = ""
#     # Start with first column width:
#     column = 0
#     for item in list(printList):
#         # Check if the item can be cast as a float:
#         if isfloat(str(item)):
#             if (not np.isfinite(item)):
#                 printStr = printStr + (" " * colWidths[column]) + ", "
#             else:
#                 printStr = (printStr +
#                             "{0:{w}.{d}f}, ".format(item,
#                                                     w=colWidths[column],
#                                                     d=decWidths[column]))
#         # If not a float, assume a string:
#         else:
#             if str(item) == "None":
#                 printStr = printStr + (" " * colWidths[column]) + ", "
#             else:
#                 printStr = (printStr +
#                             "{:>{w}s}, ".format(item, w=colWidths[column]))
#         # Iterate columns:
#         column += 1

#     # printStr += end
#     # print printStr

#     return printStr + end

# printStr = ""
# printStr += printList(["Time", ] + list(mergedA.columns.values),
#                       colWidths, decWidths)
# for i in newData.index.values:
#     # print i, list(mergedA.loc[i])
#     # print ([i, ] + list(mergedA.loc[i]))
#     printStr += printList([i, ] + list(mergedA.loc[i]),
#                           colWidths, decWidths)

# print "printStr:\n", printStr
