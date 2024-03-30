import socket
import threading
import time
import numpy as np
import pandas as pd
import pickle as pkl

class DMM():
    def __init__(self,ip='10.0.0.85'):
                # Set up your socket connection
        self.server_address = (ip, 1234)  # Adjust the address and port accordingly port 5025 for DMM6500  Prologix:1234
        #sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock  = socket.socket(socket.AF_INET, socket.SOCK_STREAM,socket.IPPROTO_TCP)
        self.sock.connect(self.server_address)
        self.f = fast_file()
        #sock.listen(1)
        print("Waiting for a connection...")
        #connection, client_address = sock.accept()
        # Create and start the receive thread
        self.receive_semaphor = False
        self.rcv_thread_enable = True
        self.answer_type = 'str'
        self.receive_thread = threading.Thread(target=self.receive_data)
        self.receive_thread.start()
        #prologix init code
        #self.sock.sendall(b'++addr 9\r\n')
        time.sleep(1)
        #self.sock.sendall(b'++auto\r\n')
        time.sleep(1)
        self.answer_type = 'float'
        self.sock.sendall(b'Read?\r\n')
        time.sleep(1)
        self.sock.sendall(b'Read?\r\n')
        time.sleep(1)
    def __dell__(self):
        self.close()
    def close(self):
        self.rcv_thread_enable = False  # thread should be auto terminated by function exit         
        self.sock.shutdown(socket.SHUT_RDWR) #shutdown both otherwise SHUT_RD or SHUT_WR

    def receive_data(self):
        buffer_size = 1  # Adjust the buffer size as needed was 1024
        partial_data = b''  # Initialize an empty bytes object

        while self.rcv_thread_enable:
            try:
                data_chunk = self.sock.recv(buffer_size)
                if not data_chunk:
                    break  # Break the loop if the connection is closed
                # Check if the received data indicates the end of a message
                if self.is_end_of_message(data_chunk):
                    self.process_data(partial_data)
                    partial_data = b''  # Reset partial_data for the next message
                else:
                    partial_data += data_chunk
            except Exception as e:
                print(f"Error receiving data: {e}")
                break

    def is_end_of_message(self,data):
        # Implement your logic to determine if the received data is a complete message
        # You might check for specific termination characters or patterns in your data
        # For example, if the message ends with '\n', you can use: return data.endswith(b'\n')
        if data ==  b'\r' or  data ==b'\n':
            return True  # Replace with your actual logic
        else:
            return False

    def process_data(self,data):
        # Implement your data processing logic here
        if (self.answer_type == 'float'):
            try:
                float_data=float (data.decode('utf-8'))
                self.rcv_float = float_data
                self.receive_semaphor=True
            except:
                #do nothing skip wrong data
                self.a=1
                print ('answer is not numeric ANS=',data)

    def SCPIread(self):
        while self.receive_semaphor == False:
            time.sleep(0.01)
        self.answer_type       = 'float'
        self.receive_semaphor  = False
        self.sock.sendall(b'Read?\r\n')
        while self.receive_semaphor == False:
            time.sleep(0.1)
        return self.rcv_float
    
    def find_resolution (self,plc):
        # this function is based HP34970a documentation 
        # resoltion and PLC settings are only checked at HP349700a
        resolution = 0
        c= {"PLC":       [0.02,   0.2,     1,        2,        10,       20,       100,       200],
            "Resolution":[0.0001, 0.00001, 0.000003, 0.0000022, 0.000001, 0.0000008, 0.0000003, 0.00000022 ],
            'Digit':     [4.5,    5.5,     5.5,      6.5,      6.5,      6.5,       6.5,       6.5],
            'Bits':      [15,     18,      20,       21,       24,       25,       26,         26 ] }
        i = 0
        for ind in c['PLC']:
            if ind == plc:
                resolution = c['Resolution'][i]
                #print ('Resolution =',resolution)
            i = i+1
        return resolution

    def MeasDC(self, range, plc,channel):
        res = self.find_resolution(plc)
        res = res * range   # scale the resolution to range - note HP manuals says that range is not scaled!
        cmd = b'MEAS:VOLT:DC? '+ str(range).encode('utf-8') + b',' + str(res).encode('utf-8') + b', (@' + str(channel).encode('utf-8') + b')\r\n'
        # print ('CMD=',cmd)
        #while self.receive_semaphor == False:
        #    time.sleep(0.01)
        self.answer_type       = 'float'
        self.receive_semaphor  = False
        self.sock.sendall(cmd)
        while self.receive_semaphor == False:
            time.sleep(0.1)
        return self.rcv_float
    
    def MeasNTC(self, channel):
        cmd = b'MEAS:TEMP? THER,10000, (@'+ str(channel).encode('utf-8') + b')\r\n'  # takes 0.2sec
        self.answer_type       = 'float'
        self.receive_semaphor  = False
        self.sock.sendall(cmd)  # takes 0.2sec
        while self.receive_semaphor == False:
            time.sleep(0.01)
        return self.rcv_float

    def main(self, f_name='array3500.pkl'):
        #self.eth_tx.start()
        try:
            # Your main program logic goes here
            while True:
                # Main program loop, can perform other tasks
                self.receive_semaphor  = False
                self.sock.sendall(b'Read?\r\n')
                #semaphor for HP34970
                while self.receive_semaphor == False:
                    time.sleep(0.01)		
                #Array fast delay because hi answer imediatly with lates value
                #time.sleep(0.5)		                
        except KeyboardInterrupt:
            print("Exiting program.")
        finally:
            # Clean up
            #connection.close()
            self.rcv_thread_enable = False #terminate the receive thread
            self.sock.shutdown(socket.SHUT_RDWR) #shutdown both otherwise SHUT_RD or SHUT_WR
            self.f.save (fileName=f_name, arrayInput=self.samples)
    def main2(self,f_name):
        try:
            for i in range(3):
                self.receive_semaphor  = False
                #self.sock.sendall(b'MEAS:VOLT:DC? 0.1,0.00000003, (@101)\r\n')  # takes 4,1sec=100PLC+AZ?
                #self.sock.sendall(b'MEAS:VOLT:DC? 0.1,0.00000008, (@101)\r\n')  # takes 1.0sec = 20PLC
                self.sock.sendall(b'MEAS:VOLT:DC? 0.1,0.0000001, (@101)\r\n')  # takes 0.6sec = 10PLC
                #self.sock.sendall(b'MEAS:VOLT:DC? 0.1,0.0000003, (@101)\r\n')  # takes 0.25sec 1PLC but slow. Use 10PLC!!
                while self.receive_semaphor == False:
                    time.sleep(0.01)
                time.sleep(0.5)

                self.receive_semaphor  = False
                self.sock.sendall(b'MEAS:VOLT:DC? 100.0,0.0001, (@201)\r\n')  # takes 0.6sec = 10PLC
                while self.receive_semaphor == False:
                    time.sleep(0.01)
                time.sleep(0.5)

                self.receive_semaphor  = False
                #self.sock.sendall(b'Read?\r\n')
                self.sock.sendall(b'MEAS:TEMP? THER,10000, (@102)\r\n')  # takes 0.2sec
                while self.receive_semaphor == False:
                    time.sleep(0.01)
                time.sleep(0.5)
                self.receive_semaphor  = False
                #self.sock.sendall(b'Read?\r\n')
                self.sock.sendall(b'MEAS:TEMP? THER,10000, (@103)\r\n')  # takes 0.2sec
                while self.receive_semaphor == False:
                    time.sleep(0.01)
                time.sleep(0.5)
                self.sock.sendall(b'MEAS:TEMP? THER,10000, (@104)\r\n')  # takes 0.2sec
                while self.receive_semaphor == False:
                    time.sleep(0.01)
                time.sleep(0.5)
        except :
            print("Exiting program error.")

class fast_file():
  def __init__(self):
    self.dummy=12
    # empty constructor for now!

  def save(self,fileName='scope.pkl',arrayInput = np.random.rand(4,50000000)): #Trial input
    t0=time.time()
    fileObject = open(fileName, 'wb')
    pkl.dump(arrayInput, fileObject)
    fileObject.close()
    print ('Write time=',time.time()-t0,'[sec.]')
    
  def load (self, fileName='scope.pkl'):
    t0=time.time()
    fileObject2 = open(fileName, 'rb')
    read_data = pkl.load(fileObject2)    
    fileObject2.close()    
    print ('Read time=',time.time()-t0,'[sec.]')
    return (read_data)

class test():
  def __init__(self,ip='192.168.1.127',f_name='hp34970_tc1.pkl'):
      self.df  = pd.DataFrame([],columns=['time','dV','Tamb','Tref','Tdmm','Vdc'])
      self.dmm = DMM(ip)
      self.f   = fast_file()
      self.f_name = f_name
  def add_row(self,time,sample,Tamb,Tref,Tdmm,Vdc):
      new_row = {'time':time, 'dV':sample, 'Tamb':Tamb, 'Tref':Tref, 'Tdmm':Tdmm, 'Vdc':Vdc}
      print (new_row)
      self.df.loc[len(self.df.index)] = new_row
  def main(self):
        try:
            # Your main program logic goes here
            t1 = time.time()-10000  #get timestamp from long time ago
            v  = self.dmm.MeasDC( range=0.1, plc=10,channel=101)
            while True:
                # Main program loop, can perform other tasks
                v  = self.dmm.SCPIread()
                t  = time.time()
                if (t - t1) >= 600:    #difference is in seconds. 10 min
                    print ("===================== NEW MUX REFRESH =====================")
                    t1 = t
                    Tamb = self.dmm.MeasNTC (102)
                    Tref = self.dmm.MeasNTC (103)
                    Tdmm = self.dmm.MeasNTC (104)
                    Vdc  = self.dmm.MeasDC (range=100.0, plc=10,channel=201)
                    v  = self.dmm.MeasDC( range=0.1, plc=10,channel=101)    # keep this line last. The main loop use fater Read? cmd
                self.add_row(time=t, sample=v,Tamb=Tamb, Tref=Tref, Tdmm=Tdmm, Vdc=Vdc)
                #time.sleep(0.5)		                
        except KeyboardInterrupt:
            print("Exiting program.")
        finally:
            # Clean up
            #connection.close()
            self.dmm.close()
            self.f.save (fileName=self.f_name, arrayInput=self.df)
