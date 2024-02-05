import socket
import threading
import time
import numpy as np
import pickle as pkl

class DMM():
    def __init__(self):
                # Set up your socket connection
        self.server_address = ("10.0.0.80", 1234)  # Adjust the address and port accordingly
        #sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock  = socket.socket(socket.AF_INET, socket.SOCK_STREAM,socket.IPPROTO_TCP)
        self.sock.connect(self.server_address)
        self.f = fast_file()
        #sock.listen(1)
        print("Waiting for a connection...")
        #connection, client_address = sock.accept()
        # Create and start the receive thread
        self.T1=time.time()
        self.sample_nr = 0
        self.samples = np.array([],dtype=float)
        self.dT      = np.array([],dtype=float)
        self.rcv_thread_enable = True
        self.receive_thread = threading.Thread(target=self.receive_data)
        self.receive_thread.start()
        #prologix init code
        self.sock.sendall(b'++addr 9\r\n')
        time.sleep(1)
        self.sock.sendall(b'++auto\r\n')
        time.sleep(1)
        self.sock.sendall(b'Read?\r\n')
        time.sleep(1)
        self.sock.sendall(b'Read?\r\n')
        time.sleep(1)        

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
        try:
            float_data=float (data.decode('utf-8'))
            T2=time.time()
            dT = T2-self.T1
            self.sample_nr = self.sample_nr + 1
            self.samples = np.append(self.samples,float_data)
            self.dT      = np.append(self.dT,dT)
            print(self.sample_nr, ". V:",float_data, " dT=%.3f" %dT )
            self.receive_semaphor=True
            self.T1=T2
        except:
            #do nothing skip wrong data
            self.a=1
    def main(self):
        #self.eth_tx.start()
        try:
            # Your main program logic goes here
            while True:
                # Main program loop, can perform other tasks
                self.receive_semaphor  = False
                self.sock.sendall(b'Read?\r\n')
                while self.receive_semaphor == False:
                    time.sleep(0.1)		
                #pass
        except KeyboardInterrupt:
            print("Exiting program.")
        finally:
            # Clean up
            #connection.close()
            self.rcv_thread_enable = False #terminate the receive thread
            self.sock.shutdown(socket.SHUT_RDWR) #shutdown both otherwise SHUT_RD or SHUT_WR
            self.f.save (fileName='hp34970.pkl',arrayInput=self.samples)


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
    print ('Rrite time=',time.time()-t0,'[sec.]')
    return (read_data)
