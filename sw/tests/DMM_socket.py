import socket
import threading

def receive_data(sock):
    buffer_size = 1  # Adjust the buffer size as needed was 1024
    partial_data = b''  # Initialize an empty bytes object

    while True:
        try:
            data_chunk = sock.recv(buffer_size)
            if not data_chunk:
                break  # Break the loop if the connection is closed
            # Check if the received data indicates the end of a message
            if is_end_of_message(data_chunk):
                process_data(partial_data)
                partial_data = b''  # Reset partial_data for the next message
            else
                partial_data += data_chunk
        except Exception as e:
            print(f"Error receiving data: {e}")
            break

def is_end_of_message(data):
    # Implement your logic to determine if the received data is a complete message
    # You might check for specific termination characters or patterns in your data
    # For example, if the message ends with '\n', you can use: return data.endswith(b'\n')
    if data ==  b'\r' or  data ==b'\n':
    return True  # Replace with your actual logic

def process_data(data):
    # Implement your data processing logic here
    print(f"Received data: {data.decode('utf-8')}")

def main():
    # Set up your socket connection
    server_address = ('127.0.0.1', 12345)  # Adjust the address and port accordingly
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(server_address)
    sock.listen(1)

    print("Waiting for a connection...")
    connection, client_address = sock.accept()

    # Create and start the receive thread
    receive_thread = threading.Thread(target=receive_data, args=(connection,))
    receive_thread.start()

    try:
        # Your main program logic goes here
        while True:
            # Main program loop, can perform other tasks
            pass
    except KeyboardInterrupt:
        print("Exiting program.")
    finally:
        # Clean up
        connection.close()
        receive_thread.join()

if __name__ == "__main__":
    main()
