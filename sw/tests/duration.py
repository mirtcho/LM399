import pyvisa

import matplotlib.pyplot as plt
import numpy as np
#from scipy.signal import butter, lfilter,lfilter_zi
from scipy import signal
from scipy.fft import fft, ifft, fftfreq
import math as m
import statistics as stat
import time
import allantools



class t:
def __init__(self):
    self.data = []
	#init Array M3500A @USB
	self.visa_rm = pyvisa.ResourceManager()
	self.visa_rm.list_resources()
	self.usb_inst = rm.open_resource('USB0::0x164E::0x0FA3::TW00004979::INSTR')
	print(self.usb_inst.query("*IDN?"))
	print(self.usb_inst.query("READ?"))
	print(self.usb_inst.query("MEAS:VOLT:DC?"))
	#init HP34960A via ethernet dongle

def butter_lowpass(self, cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def butter_lowpass_filter(self, data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = lfilter(b, a, data)
    zi = lfilter_zi(b, a)
    #print('zi=',zi,'zi*data[0]=',zi*data[0])
    y, _ = lfilter(b, a, x=data,zi=zi*((data[0]+data[1]+data[2]+data[3]+data[4]+data[5])/6))
    return y 

def acq(self):
	x = []
	dx= []
	y1 = []
	i = 0            # sample counter
	t1= time.time() # begin time in seconds float type
	while True:
		i = i+1
		m = inst.query("MEAS:VOLT:DC?")
		#print (m)
		dT=time.time()-t1
		y.append(float(m))		
		x.append(dT)
		dx.append(dT-x[len(x)-2])
		if (i/500.0)==int(i/500):
			print (i)
		if i>=35000:
			break
			
strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())