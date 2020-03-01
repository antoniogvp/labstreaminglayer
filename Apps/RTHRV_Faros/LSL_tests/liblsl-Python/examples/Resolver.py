# -*- coding: utf-8 -*-
import sys; sys.path.append('..') # help python find pylsl relative to this example program
from pylsl import StreamInlet, resolve_stream, ContinuousResolver
import time

# first resolve an EEG stream on the lab network
print("Looking for streams...")
resolver = ContinuousResolver()
streams = []

while True:
    try:
        resolved = resolver.results()
        names = [x.name() for x in resolved]
        if names != streams:  # if it has changed:
            streams = names
            if streams == []:
                print '\nLSL empty...\nLooking for streams...'
            else:
                print "Found:"
                for stream in streams:
                    print stream
    except KeyboardInterrupt: sys.exit(0)
    time.sleep(0.1)

# -- THE END --