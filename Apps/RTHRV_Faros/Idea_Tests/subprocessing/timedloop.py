# -*- coding: utf-8 -*-

# Script running a slow loop

import time

# print raw_input('type: ')

for i in xrange(3):
    print 'time loop:', i
    time.sleep(1.0)

print 'time loop done'