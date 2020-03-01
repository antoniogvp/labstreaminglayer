# -*- coding: utf-8 -*-

############################################################################
# Hub script to launch all associated scripts for this online
# ECG-processing project
#
# Each script can be re-launched through user input
#
# - Matthew Wilson, 2016
############################################################################

from subprocess import Popen, PIPE, STDOUT, call, check_output
import time

exe = "python"
plotter = "LivePlotting_Process_Commandline.py"
deviation = "HRV_Standard_Deviation.py"
emulator = "Emulator.py"

ECGPlot = "-p 15 -r 500 -w 5 -T ECG -i -t 2 -c gold -n".split()
HRPlot = "-p 15 -r 500 -w 60 -T RR -t 5 -c red -N -s 60000 -o 32768 -v BPM -m StrMarkers".split()
STDPlot = "-p 15 -r 500 -w 180 -T HRV_STD -t 5 -c blue -m StrMarkers".split()

DETACHED_PROCESS = 0x00000008

if raw_input("\nType 'e' to run emulator,\n"
             "or just <Enter> to continue...\n\n"
             ">>> ").lower() == 'e':
    Emulator = Popen([exe, emulator],
                     # stdout=None, stdin=None, stderr=None,
                     stdout=PIPE, stdin=PIPE, stderr=PIPE,
                     # close_fds=True, creationflags=DETACHED_PROCESS
                     )
    time.sleep(3)

# STDProc     = Popen([exe, deviation],
#                     # stdout=None, stdin=None, stderr=None,
#                     stdout=PIPE, stdin=PIPE, stderr=PIPE,
#                     # close_fds=True, creationflags=DETACHED_PROCESS
#                     )
ECGPlotProc = Popen([exe, plotter] + ECGPlot,
                    # stdout=None, stdin=None, stderr=None,
                    stdout=PIPE, stdin=PIPE, stderr=PIPE,
                    # close_fds=True, creationflags=DETACHED_PROCESS
                    )
HRPlotProc  = Popen([exe, plotter] + HRPlot,
                    # stdout=None, stdin=None, stderr=None,
                    stdout=PIPE, stdin=PIPE, stderr=PIPE,
                    # close_fds=True, creationflags=DETACHED_PROCESS
                    )
STDPlotProc = Popen([exe, plotter] + STDPlot,
                    # stdout=None, stdin=None, stderr=None,
                    stdout=PIPE, stdin=PIPE, stderr=PIPE,
                    # close_fds=True, creationflags=DETACHED_PROCESS
                    )
STDProc     = Popen([exe, deviation],
                    # stdout=None, stdin=None, stderr=None,
                    # stdout=PIPE, stdin=PIPE, stderr=PIPE,
                    stdin=PIPE, stderr=PIPE,
                    # close_fds=True, creationflags=DETACHED_PROCESS
                    )


helpStr = ("\n'e'  : Launch emulator"
           "\n'ecg': Launch ECG plot" +
           "\n'hr' : Launch HR  plot" +
           "\n'std': Launch STD plot" +
           "\n'dev': Launch STD processing" +
           "\n'h'  : show this guide" +
           "\n'exit' to end and close all.\n"
           )
response = raw_input(helpStr + '>>> ')
while response != 'exit':
    if response.lower() == 'h':
        print helpStr

    if response.lower() == 'e':
        try:
            Emulator.terminate()
        except:
            pass
        Emulator = Popen([exe, emulator],
                         # stdout=None, stdin=None, stderr=None,
                         stdout=PIPE, stdin=PIPE, stderr=PIPE,
                         # close_fds=True, creationflags=DETACHED_PROCESS
                         )
        print 'Started emulator'

    if response.lower() == 'ecg':
        try:
            ECGPlotProc.terminate()
        except:
            pass
        ECGPlotProc = Popen([exe, plotter] + ECGPlot, stdout=PIPE, stdin=PIPE, stderr=PIPE)
        print 'Started ECG plot'

    if response.lower() == 'hr':
        try:
            HRPlotProc.terminate()
        except:
            pass
        HRPlotProc = Popen([exe, plotter] + HRPlot, stdout=PIPE, stdin=PIPE, stderr=PIPE)
        print 'Started HR plot'

    if response.lower() == 'std':
        try:
            STDPlotProc.terminate()
        except:
            pass
        STDPlotProc = Popen([exe, plotter] + STDPlot, stdout=PIPE, stdin=PIPE, stderr=PIPE)
        print 'Started STD plot'

    if response.lower() == 'dev':
        try:
            STDProc.terminate()
        except:
            pass
        STDProc = Popen([exe, deviation], stdin=PIPE, stderr=PIPE)
        print 'Started standard deviation processing'

    # Recheck input:
    response = raw_input('\n>>> ')

ECGPlotProc.terminate()
HRPlotProc.terminate()
STDPlotProc.terminate()
STDProc.terminate()
try:  # Emulator may not have been created:
    Emulator.terminate()
except:
    pass