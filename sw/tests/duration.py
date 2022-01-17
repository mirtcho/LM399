#import pyvisa
#import usbtmc

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
import csv

class t:
	def __init__(self):
		self.data = []
		#init Array M3500A @USB
		self.init_array_m3500a()
		#init HP34960A via ethernet dongle
		self.y1 = []		#measurements from Array M3500a USB
		self.t1 = []		#timestamp from Array M3500m samples 
		self.y2 = []		#measurements hp34970a via ethernet
		self.t2 = []		#time stamp hp34970a samples - via ethernet
		self.first_time_plot_flag=True
		#initialize the file outputs - CSV format
		file_header=['time','sample']
		f1=open('array3500.csv', 'w', encoding='UTF8')
		self.y1_writer= csv.writer(f1)
		self.y1_writer.writerow(file_header)
		f2=open('hp34970.csv', 'w', encoding='UTF8')
		self.y2_writer= csv.writer(f2)
		self.y2_writer.writerow(file_header)

	def init_array_m3500a(self): 
		#self.visa_rm = pyvisa.ResourceManager()
		#self.visa_rm.list_resources()
		#self.usb_inst = self.visa_rm.open_resource('USB0::0x164E::0x0FA3::TW00004979::INSTR')
		self.usb_inst=usbtmc.Instrument(5710,4003)
		print(self.usb_inst.ask("*IDN?"))
		print(self.usb_inst.ask("READ?"))
		self.usb_thread = threading.Thread(target=self.usb_rcv_function)
		self.usb_thread.start()
		self.lock=threading.Lock()

	def usb_rcv_function(self):
		print('USB Tx/Rx thread is running ')
		self.usb_rcv_cnt=0
		t0=time.time()	#mark the begin time		
		while True:
			m = self.usb_inst.ask("MEAS:VOLT:DC?")
			#print (m)
			t=time.time()
			self.lock.acquire()
			self.usb_rcv_cnt=self.usb_rcv_cnt+1			
			self.y1.append(float(m))		
			self.t1.append(t)
			#write to file timestamp, sample data
			self.y1_writer.writerow([time.time(),float(m)])	
			self.lock.release()

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
				self.lock.acquire()
				self.socket_rcv_cnt=self.socket_rcv_cnt+1
				self.y2.append(float(data))
				self.t2.append(float(t2))
				#write to file timestamp, sample data
				self.y2_writer.writerow([time.time(),float(data)])
				self.lock.release()
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
		
		
		
		time.sleep(0.3)
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

	def print_usb_statistics(self):
		print ('Array M3500A raw data statistics from :',self.usb_rcv_cnt,' Samples')
		print ('----------------------------------------')
		self.lock.acquire()
		print ('mean=',stat.mean(self.y1),'  stdev=',stat.stdev(self.y1),'  Vpp=',max(self.y1)-min(self.y1))
		self.lock.release()
		dT = self.t1[self.usb_rcv_cnt-1]-self.t1[2]
		print ('execution time=',dT,'sec.   Sample rate[Smpl/sec=',(self.usb_rcv_cnt-1)/dT)
	
	def refresh_plots(self):
		print ('HP34970A raw data statistics from :',self.socket_rcv_cnt,' Samples')
		print ('----------------------------------------')
		self.lock.acquire()
		print ('mean=',stat.mean(self.y2),'  stdev=',stat.stdev(self.y2),'  Vpp=',max(self.y2)-min(self.y2))
		self.lock.release()
		dT = self.t2[self.socket_rcv_cnt-1]-self.t2[2]
		print ('execution time=',dT,'sec.   Sample rate[Smpl/sec=',(self.socket_rcv_cnt-1)/dT)
		self.print_usb_statistics()
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
		#plt.plot(self.t2,self.y2,'b',self.t2,lpf,'r')
		plt.plot(self.t2,self.y2,'b',self.t2,lpf,'r',self.t1,self.y1)
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
			time.sleep(.2) #poll in main() must be faster that the threads. Otherwise we miss the moment to update the graphs		
			if (self.socket_rcv_cnt/50.0)==int(self.socket_rcv_cnt/50):
				self.refresh_plots()
			if self.socket_rcv_cnt>=25000:
				#ToDo 
				#close csv files
				#stop threads
				#release sockets
				break


class gr:
	def __init__(self):
		#f1=open('array3500.csv', 'r', encoding='UTF8')
		#f2=open('hp34970.csv', 'r', encoding='UTF8')		
		#self.y1_reader= csv.reader(f1)
		#self.y2_reader= csv.reader(f2)
		self.x1 = []
		self.y1 = []
		self.n1 = 0 #nr of samples
		self.sr1= 0 #sample rate
		self.x2 = []
		self.y2 = []
		self.n2 = 0
		self.sr2= 0
		
	def read(self):
		with open('array3500.csv', encoding='UTF8') as csvfile:
			y1_reader = csv.reader(csvfile)
			for row in y1_reader:
				if (self.n1==0):
					self.x1.append(float(0.0))
					self.y1.append(float(0.0))
				if (self.n1==1):
					t10=float(row[0])-0.25
					self.x1.append(float(0.25))
					self.y1.append(float(row[1]))
				if (self.n1>1):
					self.x1.append(float(row[0])-t10)
					self.y1.append(float(row[1]))
				self.n1=self.n1+1
			self.sr1=(self.n1-2)/(float(self.x1[(self.n1-2)])-float(self.x1[1]))
			print ('read array3500.csv finished. ',self.n1, 'lines read with Sample Rate:',self.sr1)
			#fake the first sample
			self.y1[0]=self.y1[1]
		with open('hp34970.csv', encoding='UTF8') as csvfile:
			y2_reader = csv.reader(csvfile)
			for row in y2_reader:
				if (self.n2==0):
					self.x2.append(float(0.0))
					self.y2.append(float(0.0))
				if (self.n2==1):
					t20=float(row[0])-0.25
					self.x2.append(float(0.25))
					self.y2.append(float(row[1]))
				if (self.n2>1):
					self.x2.append(float(row[0])-t20)
					self.y2.append(float(row[1]))
				self.n2=self.n2+1
			self.sr2=(self.n2-2)/(float(self.x2[self.n2-2])-float(self.x2[1]))
			print ('read hp34970.csv finished. ',self.n2, 'lines read with Sample Rate:',self.sr2)
			
	def pl(self):
		self.read()
		#process Array M3500A
		Y1 = fft(self.y1)
		N  = len(Y1)
		n1 = np.arange(N)
		T  = N/self.sr1
		freq = n1/T
		
		plt.figure(figsize = (12, 6))
		plt.subplot(121)
		#remove the DC component /zero harmonics
		plt.stem(freq[1:], np.abs(Y1[1:]), 'b', markerfmt=" ", basefmt="-b")		
		plt.xlabel('Freq (Hz)')
		plt.ylabel('FFT Amplitude |Y1(freq)|')
		plt.xlim(0, 4)
		plt.title('Array M3500A')
		plt.subplot(122)
		plt.plot(self.x1[1:(self.n1-2)], self.y1[1:(self.n1-2)], 'r')
		plt.xlabel('Time (s)')
		plt.ylabel('Amplitude')
		plt.tight_layout()
		plt.show()
		
		#process the HP34970A
		Y2 = fft(self.y2[2:])
		N  = len(Y2)
		n2 = np.arange(N)
		T  = N/self.sr2
		freq = n2/T
		print (Y2)
		
		plt.figure(figsize = (12, 6))
		plt.subplot(121)
		#remove the DC component. It is zero harmonics
		plt.stem(freq[1:], np.abs(Y2[1:]), 'b', markerfmt=" ", basefmt="-b")		
		plt.xlabel('Freq (Hz)')
		plt.ylabel('FFT Amplitude |Y1(freq)|')
		plt.xlim(0, 1.1)
		plt.title('HP34970A')
		plt.subplot(122)
		plt.plot(self.x2[1:(self.n2-2)], self.y2[1:(self.n2-2)], 'r')
		plt.xlabel('Time (s)')
		plt.ylabel('Amplitude')
		plt.tight_layout()
		plt.show()

		
		

	#strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())
