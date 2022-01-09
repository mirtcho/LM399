import pyvisa

import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import butter, lfilter,lfilter_zi
from scipy import signal
import math as m
import statistics as stat
import time
import allantools
from scipy.fft import fft, ifft, fftfreq

def init_array_m3500a(): 
	rm = pyvisa.ResourceManager()
	rm.list_resources()
	inst = rm.open_resource('USB0::0x164E::0x0FA3::TW00004979::INSTR')
	print(inst.query("*IDN?"))
	print(inst.query("READ?"))
	print(inst.query("MEAS:VOLT:DC?"))

def butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def butter_lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = lfilter(b, a, data)
    zi = lfilter_zi(b, a)
    print('zi=',zi,'zi*data[0]=',zi*data[0])
    y, _ = lfilter(b, a, x=data,zi=zi*((data[0]+data[1]+data[2]+data[3]+data[4]+data[5])/6))
    return y 

def plot_graph():
	rm = pyvisa.ResourceManager()
	rm.list_resources()
	inst = rm.open_resource('USB0::0x164E::0x0FA3::TW00004979::INSTR')
	print(inst.query("*IDN?"))
	print(inst.query("READ?"))
	print(inst.query("MEAS:VOLT:DC?"))
	x=[]
	dx=[]
	y=[]
	i=0            # sample counter
	t1=time.time() # begin time in seconds float type
	while True:
		i=i+1
		m=inst.query("MEAS:VOLT:DC?")
		#print (m)
		dT=time.time()-t1
		y.append(float(m))		
		x.append(dT)
		dx.append(dT-x[len(x)-2])
		if (i/500.0)==int(i/500):
			print (i)
		if i>=35000:
			break
	print ('DMM raw data statistics')
	print ('-----------------------')
	print ('mean=',stat.mean(y),'  stdev=',stat.stdev(y),'  Vpp=',max(y)-min(y))
	print ('execution time=',dT,'sec.   Sample rate[Smpl/sec=',i/dT)
	#print ('dT=',dx)
	cutoff=0.1
	fs=i/dT
	order=6
	lpf=[y[0]]
	lpf=butter_lowpass_filter(y, cutoff, fs, order)
	print ('Sample-LPF statistics')
	print ('---------------------')
	print ('mean=',stat.mean(y-lpf),'  stdev=',stat.stdev(y-lpf),'  Vpp=',max(y-lpf)-min(y-lpf))
#plot in time domain	
	plt.figure()
	plt.plot(x,y,'b',x,lpf,'r')
	plt.legend(('DMM samples', 'LPF'), loc='best')
	plt.xlabel('Time [sec]')
	plt.ylabel('U[Volt]')
	plt.title('Noise Array M3500A 100mv 1PLC')
	plt.grid(True)
	plt.show()
#allan deviation plot
	a = allantools.Dataset(data=y)
	a.compute("mdev")
	t = np.logspace(0, 4, 50)  # tau values from 1 to 10000
	r = 35  # sample rate in Hz of the input data
	(t2, ad, ade, adn) = allantools.oadev(y, rate=r, data_type="freq", taus=t)  # Compute the overlapping ADEV
	a2 = allantools.Dataset(data=(y-lpf))
	a2.compute("mdev")
	(t22, ad2, ade2, adn2) = allantools.oadev(y-lpf, rate=r, data_type="freq", taus=t)  # Compute the overlapping ADEV
	fig = plt.loglog(t2, ad,t2,ad2) # Plot the results
	plt.title('Array M3500A 100mV Overlaping ADEV noise')
	plt.xlabel('Time [sec]')
	plt.ylabel('U')
	plt.grid(True)
	plt.show()
#FFT plots
	N=35000
	# sample spacing
	T = 1.0 / 35.0
	x = np.linspace(0.0, N*T, N, endpoint=False)
	yf = fft(y)
	yf_lpf= fft(y-lpf)
	xf = fftfreq(N, T)[:N//2]
	plt.plot(xf, 2.0/N * np.abs(yf[0:N//2]))
	plt.title('Array M3500A 100mV noise spectrum')
	plt.xlabel('F[Hz]')
	plt.ylabel('Amplitude')
	plt.grid()
	plt.show()
	#spectrum with removed low freq
	plt.plot(xf, 2.0/N * np.abs(yf_lpf[0:N//2]))
	plt.title('Array M3500A 100mV noise spectrum. LF removed')
	plt.xlabel('F[Hz]')
	plt.ylabel('Amplitude')
	plt.grid()
	plt.show()