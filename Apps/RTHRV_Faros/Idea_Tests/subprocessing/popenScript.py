# -*- coding: utf-8 -*-

# Script Testing launching scripts with arguments

from subprocess import Popen, PIPE, STDOUT, call, check_output
import os
import time


# proc = Popen(['python', 'CommandArgsScript.py', '-o', 'file.txt'], stdout=PIPE)
# data = proc.communicate()[0]
# print data

"""
Run timedloop.py with the input specified in communicate():
"""
proc2 = Popen(['python', 'timedloop.py'], stdout=PIPE, stdin=PIPE)
# print check_output(["ipconfig"])
time.sleep(3)
print 'local time ended...'
data2 = proc2.communicate('This is the input text via subprocess...')[0]
print data2

# proc3 = call('python timedloop.py', shell=True)
# print 'here'

# os.system("python CommandArgsScript.py -h")
# os.system('python timedloop.py')
# os.system('python timedloop.py')
# os.system('python F:\Project\mwilson\Code\ECG_soft\RTHRV_Faros\FarosLauncherGUI.py')

