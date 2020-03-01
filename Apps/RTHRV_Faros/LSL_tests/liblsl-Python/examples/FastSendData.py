import sys; sys.path.append('..') # help python find pylsl relative to this example program
from pylsl import StreamInfo, StreamOutlet, local_clock
import random
import time

# first create a new stream info (here we set the name to BioSemi, the content-type to EEG, 8 channels, 100 Hz, and float-valued data)
# The last value would be the serial number of the device or some other more or less locally unique identifier for the stream as far as available (you could also omit it but interrupted connections wouldn't auto-recover).
info = StreamInfo('FastStream','Stream',1,5,'float32');

# next make an outlet
outlet = StreamOutlet(info)

# Set a counter that will be sent
counter = 0.0
counter = -1.0

print("now sending data...")
# while True:
# 	# make a new random 8-channel sample; this is converted into a pylsl.vectorf (the data type that is expected by push_sample)
# 	counter += 1
# 	# now send it and wait for a bit
# 	outlet.push_sample([counter])
# 	time.sleep(0.2)
stampprev = 0.0
while True:
	# make a new random 8-channel sample; this is converted into a pylsl.vectorf (the data type that is expected by push_sample)

	stamp = local_clock()
	# now send it and wait for a bit
	# outlet.push_sample([counter],stampprev)
	outlet.push_sample([counter+1], stamp)
	time.sleep(0.005)
	# update:
	# counter += 1.1
	counter *= -1
	stampprev = stamp