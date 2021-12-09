# imports
import socket


# define the host and port
HOST = 'localhost'
PORT = 60000

# receive data
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))

    while True:
        data = s.recv(1024)
        data = data.decode('ascii').strip()
        print(data)
        if "hello from halcon" in data:
            print("true")
            s.send(b"bocce")

s.close()