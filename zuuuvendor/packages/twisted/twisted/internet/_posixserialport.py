# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.


"""
Serial Port Protocol
"""

# system imports
import os, errno

# dependent on pyserial ( http://pyserial.sf.net/ )
# only tested w/ 1.18 (5 Dec 2002)
import serial
from serial import PARITY_NONE, PARITY_EVEN, PARITY_ODD
from serial import STOPBITS_ONE, STOPBITS_TWO
from serial import FIVEBITS, SIXBITS, SEVENBITS, EIGHTBITS

from serialport import BaseSerialPort

# twisted imports
from twisted.internet import abstract, fdesc, main

class SerialPort(BaseSerialPort, abstract.FileDescriptor):
    """
    A select()able serial device, acting as a transport.
    """

    connected = 1

    def __init__(self, protocol, deviceNameOrPortNumber, reactor, 
        baudrate = 9600, bytesize = EIGHTBITS, parity = PARITY_NONE,
        stopbits = STOPBITS_ONE, timeout = 0, xonxoff = 0, rtscts = 0):
        abstract.FileDescriptor.__init__(self, reactor)
        self._serial = serial.Serial(deviceNameOrPortNumber, baudrate = baudrate, bytesize = bytesize, parity = parity, stopbits = stopbits, timeout = timeout, xonxoff = xonxoff, rtscts = rtscts)
        self.reactor = reactor
        self.flushInput()
        self.flushOutput()
        self.protocol = protocol
        self.protocol.makeConnection(self)
        self.startReading()

    def fileno(self):
        return self._serial.fd

    def writeSomeData(self, data):
        """
        Write some data to the serial device.
        """
        return fdesc.writeToFD(self.fileno(), data)

    def doRead(self):
        """
        Some data's readable from serial device.
        """
        return fdesc.readFromFD(self.fileno(), self.protocol.dataReceived)

    def connectionLost(self, reason):
        abstract.FileDescriptor.connectionLost(self, reason)
        self._serial.close()
