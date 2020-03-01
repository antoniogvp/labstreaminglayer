import sys; sys.path.append('..') # help python find pylsl relative to this example program
from pylsl import StreamInfo, StreamOutlet, StreamInlet, resolve_stream
import time

# resolve the stream and open an inlet
results = resolve_stream("type","ECG")
inlet = StreamInlet(results[0])
# get the full stream info (including custom meta-data) and dissect it
inf = inlet.info()
print "The stream's XML meta-data is: "
print inf.as_xml()
print "The manufacturer is: " + inf.desc().child_value("manufacturer")
print "The cap circumference is: " + inf.desc().child("cap").child_value("size")
print "The channel labels are as follows:" 
ch = inf.desc().child("channels").child("channel")
for k in range(info.channel_count()):
    print "  " + ch.child_value("label")
    ch = ch.next_sibling()

time.sleep(3)