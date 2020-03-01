#!/usr/bin/env python
#
##    This program is free software: you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation, either version 3 of the License, or
##    (at your option) any later version.
##
##    This program is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License
##    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##    for any question or remark, plz contact : thibault.cake at gmail dot fr
##    version 0.1


import struct
#class Decoding():
def split_len(seq, length):
	return [seq[i:i+length] for i in range(0, len(seq), length)]

def hexDumpExt(seq):
	l = split_len(seq.upper(), 2)
	res=""
	for c in l:
		res +=c+" "
	return res[0:-1]
	

def testingHexConversion(optionFormat,val):
	valPacked = struct.pack(optionFormat, val)
	h = valPacked.encode('hex')
	return val,hexDumpExt(h)


def revertHexConversion(optionFormat,valHexa):
	valHexaSpace = valHexa
	valHexa = valHexa.replace(' ','')
	return struct.unpack(optionFormat, valHexa.decode('hex'))[0],valHexaSpace


def decodeUDPPackage(msg):
	msg = msg.replace(' ','')

	#HeaderShortMsg:4 float following
	hs = '21 44 19 01 24 00 00 00 00 00 00 00 03 00 00 00 04 00 00 00'
	#HeaderLongMsg:8 float following
	hl = '21 6B 72 0E 34 00 00 00 00 00 00 00 03 00 00 00 08 00 00 00'
	hs = hs.replace(' ','')
	hl = hl.replace(' ','')
        headerType = 'unknown'
	if msg[0:len(hs)].lower() == hs.lower():
		nbFloat = 4
		headerType = 'hs'
		
	elif msg[0:len(hs)].lower() == hl.lower():
		nbFloat = 8
		headerType = 'hl'
                
#	print "decodeUDPPackage:"+headerType

	lFloats = []
	lHexFloats = split_len(msg[len(hs):],8)
	for hexFloat in lHexFloats:
		lFloats.append(revertHexConversion('<f', hexFloat)[0])
	return lFloats

