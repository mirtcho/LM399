import socket
import numpy as np
import time
import csv


class eth():
    def __init__(self):
        self.data = []
        file_header=['time','sample']
        f1=open('array3500.csv', 'w', encoding='UTF8')
        self.y1_writer= csv.writer(f1)
        self.y1_writer.writerow(file_header)

    def init_eth(self,ip_addr='10.0.0.102'):
        HOST=ip_addr	#prologix dongle @PRE
        PORT=1234
        buf_len=10
        self.s=socket.socket(socket.AF_INET,socket.SOCK_STREAM,socket.IPPROTO_TCP)
        a=self.s.connect((HOST,1234))
           
        self.s.sendall(b'++addr 9\r\n')
        time.sleep(1)
        self.s.sendall(b'++auto\r\n')
        time.sleep(1)
        self.s.sendall(b'Read?\r\n')
        time.sleep(1)
        #self.s.sendall(b'Read?\r\n')
        #time.sleep(1)

    def rcv_str(self):
        tmp = []
        ch = self.s.recv(1)
        while ch != b'\n':
            tmp.append (ch)
            ch = self.s.recv(1)
        st=b''.join(tmp).decode('utf-8')
        return st

    def read (self):
        self.s.sendall(b'Read?\r\n') 
        ret_val = self.rcv_str()
        print ('read=',float(ret_val))
        time.sleep(0.2)
        return ret_val

    def read_float(self):
        st = self.read()
        try:
            ret_val = float (st)
        except:
            ret_val = 'NaN'
        return ret_val
    
    def example(self, ip_addr='10.0.0.67', f_name='TC_data.csv', nr_of_samples=100):
        self.y1 = []		#measurements from Array M3500a USB
        self.t1 = []		#timestamp from Array M3500m samples 
        self.init_eth(ip_addr)
        file_header=['time','sample']
        f1 = open(f_name, 'w', encoding='UTF8')
        self.y1_writer= csv.writer(f1)
        self.y1_writer.writerow(file_header)
        for i in range (int(nr_of_samples)):
            t0 = time.time()
            data0  = self.read_float()
            print ('Float data=',data0)
            self.y1.append(data0)
            self.t1.append(float(t0))
            self.y1_writer.writerow([t0,data0])
        f1.close()
