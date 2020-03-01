import sys; sys.path.append('..') # help python find pylsl relative to this example program
from pylsl import StreamInlet, resolve_stream
import pdb

# first resolve a stream on the lab network
print("looking for a RR stream...")
streams= resolve_stream('type','RR')
# create a new inlet to read from the stream
inlet = StreamInlet(streams[0])

while True:
	# get a new sample (you can also omit the timestamp part if you're not interested in it)
	sample,timestamp = inlet.pull_sample()
	print(timestamp, sample)
	
