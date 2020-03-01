# -*- coding: cp1252 -*-
# Définition d'un client réseau rudimentaire
# Ce client dialogue avec un serveur ad hoc
import socket, sys
import Decoding
##HOST = '10.161.8.47'
##HOST = '127.0.0.1'
HOST = 'localhost'
PORT = 1000
##HOST_UDP = '0.0.0.0'
HOST_UDP = 'localhost'
HOST = 'localhost'
PORT_UDP_HOST = 1003
PORT_UDP_DEST = 1001

import struct
import time

raw_input("GO ?")
mySocketServerUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    #mySocketUDP = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_UDP)
mySocketServerUDP.settimeout(1)

mySocketServerUDP.bind((HOST_UDP,PORT_UDP_HOST))


def getArtifMsg(i):
    hs = '21 44 19 01 24 00 00 00 00 00 00 00 03 00 00 00 04 00 00 00'
    hs = hs.replace(' ','')
    f1 = 5.1234 + i
    f1Hex = Decoding.testingHexConversion('<f',f1)[1]
    f1Hex = f1Hex.replace(' ','')
    print (f1Hex)
    pkg=hs+f1Hex
    pkgUDP = pkg.decode('hex')
    return pkgUDP

mySocketServerUDP.connect((HOST_UDP,PORT_UDP_DEST))
print "sockName:"+str(mySocketServerUDP.getsockname())
print "sockName:"+str(mySocketServerUDP.getpeername())
raw_input("confirm PORT_UDP_DIST OPENED")


for i in range (0,500):
    #time.sleep(1)
    pkgUDP = getArtifMsg(i)
    print "sending:"+str(pkgUDP.encode('hex'))
    mySocketServerUDP.send(pkgUDP)




#mySocketServerUDP.close()





