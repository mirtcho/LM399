import numpy as np
from scipy import signal
from scipy.fft import fft, ifft, fftfreq
import math as m
#import statistics as stat
import time
import csv
#import bool

import prologix as p
import bm869usb as b
import serial


class cts():
    def __init__ (self):
        #init com prot to 192.Kbps 8 bit ODD, data flow=none
        self.ser = serial.Serial("COM5", 19200,bytesize=8,parity=serial.PARITY_ODD,timeout=1)
        #self.ser = serial.Serial("COM5", 19200,bytesize=8,parity=serial.PARITY_NONE,timeout=1)
        # serial.Serial('/dev/ttyS1', 19200, timeout=1)
        self.STX = 0x02  # Start of Text. ToDo shod be 0x02 or 0x82
        self.ETX = 0x03  # End of Text
        self.ADDR =0x81  # address 0x81....0xA0' represent addr 0x..0x20
        # Packet format "STX""Data" "CHK" "ETX"
        # CHK - XOR of data excludion STX and ETX 

    def analog(self):
        # 'STX' 'ADR' 'A' x 'CHK' 'ETX'
        # STX=0x2 #ADR=1->0x81 'A'=0xC1  Channel=0->0xB0 CHK=0xF0 ETX=0x03
        #send->  STX+ADDR+'A0'+CHK+ETX
        self.tx_packet = b'\x02\x81\xC1\xB0\xF0\x03'
        self.ser.write(self.tx_packet)
        self.rx_packet = self.ser.readline()
        #print ('Answer=',self.rx_packet)
        self.Tact, self.Tset = self.an_decode(self.rx_packet)

    def analog_all(self):
        # 'STX' 'ADR' 'A' 'a' 'CHK' 'ETX' 
        #example for ADDR = 1
        self.tx_packet = b'\x02\x81\xC1\xE1\xA1\x03'
        self.ser.write(self.tx_packet)
        self.rx_packet = self.ser.readline()
        #print ('RAW Answer=',self.rx_packet)
        self.Tset, self.Tact = self.an_decode(self.rx_packet)
        #print ('Answer=',self.rx_packet)

    def set_analog(self,Tset=14.5):
        tx_packet =np.zeros(12,dtype=np.ubyte)
        tx_packet[0] = self.STX
        tx_packet[1] = self.ADDR
        tx_packet[2] = ord('a') + 0x80            # command
        tx_packet[3] = ord('0') + 0x80            # channel 0 is Tset channel
        tx_packet[4] = ord(' ') + 0x80            # space
        #tmp_val = "{:3.1f}".format(Tset)
        tmp_val = "%05.1f" %(Tset)
        st =  str(tmp_val)
        print ('st=',st)
        for i in range (int(st.__len__())):
            tx_packet[5+i]=ord(st[i]) + 0x80
        #Calc CHK
        chk_len=int(st.__len__()) + 4
        chk_sum=0
        for ii in range (chk_len):
            chk_sum = chk_sum ^ tx_packet[ii+1]
        tx_packet[6+i] = chk_sum
        tx_packet[7+i]=self.ETX
        #print (tx_packet)
        self.ser.write(tx_packet)
        return 0
    
    def sa(self):
        #function for test purpose
        tx_packet=b'\x02\x81\xE1\xB0\xA0\xAD\xB1\xB4\xAE\xB5\xC3\x03'
        self.ser.write(tx_packet)
     
    def an_decode(self,rx_packet):
        #decodes the answer message from analog all
        #rx_packet = b'\xb0\xa0\xb0\xb5\xb5\xae\xb3\xa0\xb0\xb5\xb5\xae\xb0\xf3\x03\x02\x81\xc1\xb1\xa0\xad\xb0\xb0\xae\xb9\xa0\xb0\xb1\xb0\xae\xb0\xe4\x03'
        self.tmp = list(rx_packet)
        # reset 8-th bits        
        for i in range (rx_packet.__len__()):
            self.tmp[i]=self.tmp[i] &0x7f
        self.tmp2 = bytearray(self.tmp)
        try:
            Tset = float(self.tmp2[5:10]) #was [2:7]
        except:
            Tset = -273.15
        try:
            Tact = float(self.tmp2[11:16]) #was [8:13]
        except:
            Tact = -273.15
        #print ('decoded answer - Tset=',Tset,'  Tact=',Tact)
        return Tset,Tact


    def __del__(self):
        self.ser.close()


class tc():
    def __init__(self):
        self.bm = b.bm869()
        self.bm.init_win11()
        self.e = p.eth()
        self.e.init_eth('10.0.0.67')
        self.cts = cts()

    def tst(self,nr_samples=50):
        for Toffset in range (200):
            self.cts.set_analog(20+Toffset/10)
            self.cts.analog() #dumm.y read to solve issu with wrong read after Tset        
            for i in range (int(nr_samples)):
                array_data = self.e.read()
                bm_data = self.bm.read()
                self.cts.analog() 
                print ('array=',array_data,'  bm869=',bm_data,'Tset=',self.cts.Tset,'Tact=',self.cts.Tact)
            
