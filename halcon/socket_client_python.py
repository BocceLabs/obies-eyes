# imports
import socket
import re

# define the host and port
HOST = 'localhost'
PORT = 60000

# receive data
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))

    i = 0
    while True:
        data = s.recv(1024)
        data = data.decode('ascii').strip()
        print(data)
        # if "hello from halcon" in data:
        #     print("true")
        #     s.send(b"bocce")
        match = "^P=\[(\S*?)\],A=\[(\S*?);(\S*?);(\S*?);(\S*?)\],B=\[(\S*?);(\S*?);(\S*?);(\S*?)\]\Z"
        r = re.search(match, data)

        # extract the ball coordinates
        try:
            balls_str = [r.group(1), # p
                        r.group(2), # a1
                        r.group(3), # a2
                        r.group(4), # a3
                        r.group(5), # a4
                        r.group(6), # b1
                        r.group(7), # b2
                        r.group(8), # b3
                        r.group(9)] # b4
        except AttributeError:
            s.send(b"error")
            continue

        # extract the coordinates
        balls = []
        for b in balls_str:
            if b == "None":
                balls.append(None)
            else:
                match = "\((\S*?),(\S*?)\)"
                r = re.search(match, b)
                try:
                    x = float(r.group(1))
                    y = float(r.group(2))
                    balls.append((x,y))
                except:
                    balls.append(None)

        # debug
        print(i)
        s.send(b"bocce")
        i += 1


s.close()