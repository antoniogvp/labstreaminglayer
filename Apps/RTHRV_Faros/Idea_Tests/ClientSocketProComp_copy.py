# -*- coding: cp1252 -*-
# !/usr/bin/env python
###############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#    for any question or remark, plz contact : thibault.cake at gmail dot fr
#    version 0.1
#
###############################################################################

"""
#### NOTE:
#### Need to write in an exit command to close the ports.
"""

# Rudimentary definition of a network client
# which communicates with an ad hoc server
# /
# Définition d'un client réseau rudimentaire
# Ce client dialogue avec un serveur ad hoc
import socket
import sys
# import struct
import Decoding


# TCP_Host = '10.161.8.17'
# # TCP_Host = '127.0.0.1'
TCP_Host = 'localhost'
TCP_Port = 1001
# # UDP_Host = '0.0.0.0'  # Automatic
# UDP_Host = '10.161.8.88'
UDP_Host = 'localhost'

############################################
#  User run parameters:                    #
############################################
askConfirmation = False
writeOutput = True

# Output-writing algorithm for if writeOutput = True
# Writes to date-stamped subfolder of the output folder
# (which it creates if non-existant)
if writeOutput:
    from datetime import datetime
    import re
    import os

# Put date and time into underscored format e.g. 01_02_2016:
    dateString = re.sub('[.!,;: -]', '_', str(datetime.now()))
    # Create an output folder if one doesn't exist:
    if not os.path.exists("output"):
        os.makedirs("output")
    dateString = "output/"+dateString   # Create a string for naming output
raw_input("GO ?")


# Define function for creating and testing TCP socket:
def sendConnectionTCPSocketRequest(TCP_Host, TCP_Port):
    # 1) create socket:
    # Socket object called "mySocket" contains all necessary
    # properties and can be used to send, receive, etc.
    mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Parameters from the socket library
    if askConfirmation:  # Basically a "press any key" prompt
        raw_input("confirm initialisation ?")

    # 2) Send a connection request to the server /
    #    envoi d'une requête de connexion au serveur :
    try:
        mySocket.connect((TCP_Host, TCP_Port))
        mySocket.settimeout(1)   # 1sec
    except socket.error:
        print "The connection has failed / La connexion a echoue."
        sys.exit()
    print """Connection established with the server /
    Connexion etablie avec le serveur."""

    # 3) Retrieve data from the server / Dialogue avec le serveur :
    msgServeur = mySocket.recv(1024)
    print "RECEIVED: \n"+msgServeur  # Displays receive message.
    return mySocket


# Define function for creating UDP socket:
# http://searchsoa.techtarget.com/definition/UDP :
# UDP (User Datagram Protocol) is an alternative communications protocol to
# Transmission Control Protocol (TCP) used primarily for establishing
# low-latency and loss tolerating connections between applications on the
# Internet. Both UDP and TCP run on top of the Internet Protocol (IP) and are
# sometimes referred to as UDP/IP or TCP/IP. Both protocols send short packets
# of data, called datagrams.
def createUDPSocket(UDP_Host, UDP_ServerPort):
    print 'opening UDP TCP_Port: \n'
    if askConfirmation:  # Basically a "press any key" prompt
        raw_input("confirm initialisation ?")
# other socket
    mySocketUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # mySocketUDP = socket.socket(socket.AF_INET,
    #                             socket.SOCK_RAW, socket.IPPROTO_UDP)
    mySocketUDP.settimeout(1)  # 1sec
    mySocketUDP.bind((UDP_Host, UDP_ServerPort))
    return mySocketUDP


# Define function for a connection acknowledgement send (TCP: mySocket)
def sendAckConnectionFrom1001(mySocket):
    msgInit = '21 88 39 7E 36 00 00 00 0F 27 00 00 09 00 00 00\
 00 00 00 00 41 43 4B 4E 4F 57 4C 45 44 47 45 44\
 5F 46 52 4F 4D 20 31 32 37 2E 30 2E 30 2E 31 20\
 31 30 30 31 20 00'
    msgInitHex = msgInit.replace(' ', '')
# 2188397E360000000F270000090000000000000041434B4E4F574C45444745445F46524F4D203
# 132372E302E302E3120313030312000
    msgInitHex = msgInitHex.decode('hex')
# "!\x889~6\x00\x00\x00\x0f'\x00\x00\t\x00\x00\x00\x00\x00
# \x00\x00ACKNOWLEDGED_FROM 127.0.0.1 1001 \x00"
    print 'SENDING: HEADER ACKNOWLEDGED_FROM 127.0.0.1 1001'
# ACKNOWLEDGED_FROM ...
    if askConfirmation:
        raw_input("confirm send acknowledge?")
    mySocket.send(msgInitHex)


# Define function for a header connection acknowledgement send (TCP: mySocket)
def sendConfirmation(mySocket):
    msgConnAck = '21 00 00 00 2A 00 00 00 07 00 00 00 00 00 00 00\
 00 00 00 00 43 6F 6E 6E 65 63 74 69 6F 6E 20 61\
 6B 6E 6F 77 6C 65 64 67 65 64'
    msgConnAckHex = msgConnAck.replace(' ', '')
    msgConnAckHex = msgConnAckHex.decode('hex')
    # print 'SENDING: \n'+msgConnAckHex
    print 'SENDING: HEADER Connection aknowledged'
    if askConfirmation:
        raw_input("confirm ?")
    mySocket.send(msgConnAckHex)


# Define function to begin a UDP transmission
def beginUPDTransmission(mySocket):
    msgRdy = '21 01 93 00 1A 00 00 00 0F 27 00 00 09 00 00 00\
 01 00 00 00 52 45 41 44 59 00'
    msgRdyHex = msgRdy.replace(' ', '')
    msgRdyHex = msgRdyHex.decode('hex')
    # print 'SENDING: \n'+str(msgRdyHex)
    print 'SENDING: HEADER READY TAIL'
    if askConfirmation:
        raw_input("confirm ? UDP info coming after")
    mySocket.send(msgRdyHex)

    msgDist = mySocket.recv(1024)
    print "msg received: "+str(msgDist.encode('hex'))+"("+msgDist+")"


# Define sub-function to receive the requisite variables via UDP
def launchReceptionFromUDP(mySocketUDP, lUDPMsgBrut, lAllFloats, fileOut,
                           writeOutput):
    # mySocketUDP.connect((UDP_Host,PORT_UDP_DIST))
    print str(mySocketUDP.getsockname())
    # print str(mySocketUDP.getpeername())
    mySocketUDP.settimeout(10)

    # Initialise loop:
    lastMsgHex = ''  # A comparison variable to flag the message end.
    continueFlag = True
    repetitionCount = 0
    # Run loop:
    while continueFlag:
        try:
            # Try to receieve:
            # max size for a UDP packet / taille max paquet UDP:
            msgUDP, (addr, TCP_Port) = mySocketUDP.recvfrom(65535)
            # # max size for a UDP packet / taille max paquet UDP
            # msgUDP, (addr,TCP_Port) = mySocketUDP.recvfrom(1024)

            # print "msgUDP: "+msgUDP
            lUDPMsgBrut.append(msgUDP)
            # Put whatever was received into Hex format:
            msgUDPHex = msgUDP.encode('hex')
            # print "msgUDPHex: "+msgUDPHex
            if not lastMsgHex == msgUDPHex:  # if a new value comes through
                # update the "last message" variable:
                lastMsgHex = msgUDPHex
                # and decode the current package:
                lFloats = Decoding.decodeUDPPackage(msgUDPHex)
                # print "UPD:"+str(lFloats)
                # Find and write the required variable from the received
                # package:
                for f in lFloats:
                    lAllFloats.append(f)
                    print str(f)  # Comment out for latency +++++++++++++++++++
                    if writeOutput:
                        fileOut.writelines(str(f))
                        ##################################################
                        # Insert another function here if you want to do #
                        # anything else with the received value          #
                        ##################################################
            else:
                # print "alreadyRec:" + msgUDPHex
                repetitionCount += 1

        except socket.timeout:  # Quit the receive protocol when timeout.
            print "UDP socket timed out"
            continueFlag = False

            # res = raw_input("UDP socket timed out, retry y/[n] ?")
            # if res == 'Y' or res == 'y':
            #     continueFlag = True
            # else:
            #     continueFlag = False


# Define function to reinitialise the reception of variables via UDP
# (Uses the above launchReceptionFromUDP function)
def restartReceptionFromUDP(mySocketUDP, lUDPMsgBrut, lAllFloats, fileOut,
                            writeOutput, hostUDP):
    mySocketUDP.close()
    UDP_ServerPort = 1001
    UDP_Host = hostUDP
    mySocketUDP = createUDPSocket(UDP_Host, UDP_ServerPort)
    launchReceptionFromUDP(mySocketUDP, lUDPMsgBrut, lAllFloats, fileOut,
                           writeOutput)

"""
###############################################################################
############                      MAIN BLOCK                       ############
###############################################################################
"""

# raw_input("GO ?")

mySocket = sendConnectionTCPSocketRequest(TCP_Host, TCP_Port)

# TCP_Port where procomp sends UDP data (cf sendAckConnectionFrom1001):
UDP_ServerPort = 1001
mySocketUDP = createUDPSocket(UDP_Host, UDP_ServerPort)
sendAckConnectionFrom1001(mySocket)
sendConfirmation(mySocket)

# Send/Receive
beginUPDTransmission(mySocket)
raw_input("confirm PORT_UDP_DIST OPENED")
# PORT_UDP_DIST = 1052
lUDPMsgBrut = []
lAllFloats = []
# Creates a date-stamped .txt file to which it writes all the ECG data that
# it receives:
fileOut = open(dateString + "_ECG.txt", 'a')
launchReceptionFromUDP(mySocketUDP, lUDPMsgBrut, lAllFloats, fileOut,
                       writeOutput)


print "reset UDP connection"
continueFlag = True
while continueFlag:
    print "nbFloatsReceived: "+str(len(lAllFloats))
    res = raw_input("UDP socket timed out, reset connection [y]/n ?")
    if res == 'Y' or res == 'y' or res == '':
        restartReceptionFromUDP(mySocketUDP, lUDPMsgBrut, lAllFloats, fileOut,
                                writeOutput, UDP_Host)
    else:
        continueFlag = False

"""########################!  Synced up to HERE  !########################"""

mySocketUDP.close()
mySocket.close()

fileOut.close()

# And they all lived happily ever after.
#              THE END
