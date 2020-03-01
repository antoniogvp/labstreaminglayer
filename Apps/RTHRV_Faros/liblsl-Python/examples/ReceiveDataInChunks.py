import sys; sys.path.append('..') # help python find pylsl relative to this example program
from pylsl import StreamInlet, resolve_stream

# first resolve an EEG stream on the lab network
# print("looking for an ECG stream...")
# streams = resolve_stream('type','ECG')
print("looking for a marker stream...")
streams = resolve_stream('type','Markers')
print("Found.")

# create a new inlet to read from the stream
inlet = StreamInlet(streams[0])

while True:
	# get a new sample (you can also omit the timestamp part if you're not interested in it)
	chunk,timestamps = inlet.pull_chunk()
	if timestamps:
		print(timestamps, chunk)
