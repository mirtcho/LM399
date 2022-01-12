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
		#self.init_array_m3500a()
		#init HP34960A via ethernet dongle
		self.y1 = []		#measurements from Array M3500a USB
		self.t1 = []		#timestamp from Array M3500m samples 
		self.y2 = []		#measurements hp34970a via ethernet
		self.t2 = []		#time stamp hp34970a samples - via ethernet
		self.first_time_plot_flag=True

	def init_array_m3500a(self): 
		self.visa_rm = pyvisa.ResourceManager()
		self.visa_rm.list_resources()
		self.usb_inst = self.visa_rm.open_resource('USB0::0x164E::0x0FA3::TW00004979::INSTR')
		print(self.usb_inst.query("*IDN?"))
		print(self.usb_inst.query("READ?"))
		self.usb_thread = threading.Thread(target=self.socket_rcv_function)
		self.usb_thread.start()

	def usb_rcv_function(self):
		self.usb_rcv_cnt=0
		t0=time.time()	#mark the begin time
		t1=t0
		while True:
			m = inst.query("MEAS:VOLT:DC?")
			#print (m)
			self.usb_rcv_cnt=self.usb_rcv_cnt+1
			t2=time.time()
			y1.append(float(m))		
			x1.append(t2)
			t1=t2

	def socket_rcv_function(self):
		print('Receive socket thread is running:')
		self. socket_rcv_cnt=0
		t0=time.time()	#mark the begin time
		t1=t0
		while True:
			data = self.s.recv(16)
			#print(data)
			if float(data)>7 and float(data)<11:
				#print(data, ' Cnt=',self.socket_rcv_cnt)
				t2=time.time()
				self.socket_rcv_cnt=self.socket_rcv_cnt+1
				self.y2.append(float(data))
				self.t2.append(float(t2))
				#print (self.socket_rcv_cnt,':',float(data),'   dT:',(t2-t1))
				t1=t2
			time.sleep(0.1)
			#if not data: break
		print ('Done Receiving')
	
	def socket_tx_function(self):
		print('Transmit socket thread is running:')
		while True:
			self.s.sendall(b'Read?\r\n')
			time.sleep(1)
		
		
	def init_eth(self):
		HOST='10.0.0.89'	#prologix dongle @PRE
		PORT=1234
		buf_len=10
		self.s=socket.socket(socket.AF_INET,socket.SOCK_STREAM,socket.IPPROTO_TCP)
		a=self.s.connect((HOST,1234))
		self.eth_rx = threading.Thread(target=self.socket_rcv_function)
		self.eth_tx = threading.Thread(target=self.socket_tx_function)
		self.eth_rx.start()		
		self.s.sendall(b'++addr 9\r\n')
		time.sleep(1)
		self.s.sendall(b'++auto\r\n')
		time.sleep(1)
		self.s.sendall(b'Read?\r\n')
		time.sleep(1)
		self.s.sendall(b'Read?\r\n')
		time.sleep(1)		
		self.eth_tx.start()

	def butter_lowpass(self, cutoff, fs, order=5):
		nyq = 0.5 * fs
		normal_cutoff = cutoff / nyq
		b, a = signal.butter(order, normal_cutoff, btype='low', analog=False)
		return b, a

	def butter_lowpass_filter(self, data, cutoff, fs, order=5):
		b, a = self.butter_lowpass(cutoff, fs, order=order)
		y = signal.lfilter(b, a, data)
		zi = signal.lfilter_zi(b, a)		
		y, _ = signal.lfilter(b, a, x=data,zi=zi*((data[0]+data[1]+data[2]+data[3]+data[4]+data[5])/6))
		return y 

	def refresh_plots(self):
		print ('DMM raw data statistics from :',self.socket_rcv_cnt,' Samples')
		print ('----------------------------------------')
		print ('mean=',stat.mean(self.y2),'  stdev=',stat.stdev(self.y2),'  Vpp=',max(self.y2)-min(self.y2))
		dT = self.t2[self. socket_rcv_cnt-1]-self.t2[2]
		print ('execution time=',dT,'sec.   Sample rate[Smpl/sec=',(self.socket_rcv_cnt-1)/dT)
		cutoff=.02						# Fc=0.1Hz
		fs=(self.socket_rcv_cnt-1)/dT	# Sampling frequency
		order=6
		lpf=[self.y2[0]]
		lpf=self.butter_lowpass_filter(self.y2, cutoff, fs, order)
		if (self.first_time_plot_flag==True):
			plt.figure()		
			plt.legend(('DMM samples', 'LPF'), loc='best')
			plt.xlabel('Time [sec]')
			plt.ylabel('U[Volt]')
			plt.title('HP34970A')
			plt.grid(True)
			self.first_time_plot_flag=False
		plt.plot(self.t2,self.y2,'b',self.t2,lpf,'r')
		plt.pause(0.5)
	
	def acq(self):
		self.init_eth()
		x = []
		dx= []
		y1 = [] 	#array M3500A via USB		
		i = 0       # sample counter
		t1= time.time() # begin measurements time in seconds float type
		while True:
			i = i+1
			dT=time.time()-t1
			#y.append(float(m))		
			#x.append(dT)
			#dx.append(dT-x[len(x)-2])
			time.sleep(.2) #poll in main() must be faster that the threads. Otherwise we miss the moment to update the graphs		
			if (self.socket_rcv_cnt/50.0)==int(self.socket_rcv_cnt/50):
				self.refresh_plots()
			if self.socket_rcv_cnt>=25000:
				break

	#strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())