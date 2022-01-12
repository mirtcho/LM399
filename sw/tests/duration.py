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
import socket
import threading

class t:
	def __init__(self):
		self.data = []
		#init Array M3500A @USB
		#self.visa_c
		#self.visa_rm.list_resources()
		#self.usb_inst = rm.open_resource('USB0::0x164E::0x0FA3::TW00004979::INSTR')
		#print(self.usb_inst.query("*IDN?"))
		#print(self.usb_inst.query("READ?"))
		#print(self.usb_inst.query("MEAS:VOLT:DC?"))
		#init HP34960A via ethernet dongle
		self.y2 = []#measurements hp34970a via ethernet
		self.t2 = []#time scale   hp34970a via ethernet

	def socket_rcv_function(self):
		print('Receive thread is running:')
		self. socket_rcv_cnt=0
		t0=time.time()	#mark the begin time
		t1=t0
		while True:
			data = self.s.recv(16)			
			#print (repr(data))
			#print ('RAW data:', data, '  str data:', str(data),'   float:', float(data))
			if float(data)>7 and float(data)<11:
				t2=time.time()
				self.socket_rcv_cnt=self.socket_rcv_cnt+1
				self.y2.append(float(data))
				print (self.socket_rcv_cnt,':',float(data),'   dT:',(t2-t1))
				t1=t2
			if not data: break
		print ('Done Receiving')
	
	def init_eth(self):
		HOST='10.0.0.89'	#prologix dongle @PRE
		PORT=1234
		buf_len=10
		self.s=socket.socket(socket.AF_INET,socket.SOCK_STREAM,socket.IPPROTO_TCP)
		a=self.s.connect((HOST,1234))
		x = threading.Thread(target=self.socket_rcv_function)  # , args=(0,))
		x.start()
		self.s.sendall(b'++addr 9\r\n')
		time.sleep(1)
		self.s.sendall(b'++auto\r\n')
		time.sleep(1)
		self.s.sendall(b'Read?\r\n')
		time.sleep(1)
		self.s.sendall(b'Read?\r\n')
		time.sleep(1)		

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
		self.init_eth()
		x = []
		dx= []
		y1 = [] 	#array M3500A via USB
		#self.y2 = []#hp34970a via ethernet
		i = 0       # sample counter
		t1= time.time() # begin measurements time in seconds float type
		while True:
			i = i+1
			self.s.sendall(b'Read?\r\n')
			time.sleep(1)
			#print (m)
			dT=time.time()-t1
			#y.append(float(m))		
			#
			x.append(dT)
			dx.append(dT-x[len(x)-2])
			if (i/50.0)==int(i/50):
				print (i)
			if i>=350:
				break
		print ('DMM raw data statistics')
		print ('-----------------------')
		print ('mean=',stat.mean(self.y2),'  stdev=',stat.stdev(self.y2),'  Vpp=',max(self.y2)-min(self.y2))
		print ('execution time=',dT,'sec.   Sample rate[Smpl/sec=',i/dT)
		cutoff=.1	# Fc=0.1Hz
		fs=i/dT		# Sampling frequency
		order=6
		lpf=[self.y2[0]]
		lpf=butter_lowpass_filter(self.y2, cutoff, fs, order)
		plt.figure()
		plt.plot(x,self.y2,'b',x,lpf,'r')
		plt.legend(('DMM samples', 'LPF'), loc='best')
		plt.xlabel('Time [sec]')
		plt.ylabel('U[Volt]')
		plt.title('Noise Array M3500A 100mv 1PLC')
		plt.grid(True)
		plt.show()
				
	#strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())