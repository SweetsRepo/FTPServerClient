__author__ = "Christopher Sweet"
__doc__ = "Develop a custom concurrent FTP Server and it's associated FTP client"

import socket
import threading
import os
import sys

SOCKETPORT = 8000

class Client():
    def __init__(self):
        self.logged_in = False
        self.cookie = None

    def connect(self, address:str, user:str, password:str):
        self.socket.connect((address, SOCKETPORT))
        self.socket.send(str.encode(user+','+password))
        if eval(self.socket.recv(1024).decode()):
            print("Connection successful")
            return True
        else:
            print("Connection Unsuccessful")
            return False

    def quit(self):
        self.socket.close()

    def run(self):
        while True:
            #Python requires a socket to be reinstantiated to be used for multiple connections
            self.socket = socket.socket()
            print("Enter an FTP command")
            argstring = input()
            command = argstring.split(" ")
            cookie = self.cookie
            if self.logged_in:
                #Reconnect with the cookie so the host doesn't get tied up
                self.connect(self.cookie[1], self.cookie[2], self.cookie[3])
            else:
                if len(command) == 4 and command[0] == 'rftp':
                    #Connect to verify and set cookie
                    self.logged_in = self.connect(command[1], command[2], command[3])
                    self.cookie = command
                else:
                    print("Usage: rftp <host> <user> <password>")
            #Hackey way to check if this is the first pass
            if cookie != self.cookie:
                print("Enter an FTP command")
                argstring = input()
                command = argstring.split(" ")
            if command[0] == 'rput' and self.logged_in:
                if len(command) == 2:
                    self.socket.send(str.encode('rput,'+command[1]))
                    try:
                        with open(command[1], 'rb') as f:
                            packet = f.read(1024)
                            while(packet):
                                self.socket.send(packet)
                                packet = f.read(1024)
                        self.socket.send(str.encode("EOF"))
                        print("Done sending data")
                    except FileNotFoundError as e:
                        print(e)
                else:
                    print("Usage: rput <filename>")
            elif command[0] == 'rget' and self.logged_in:
                if len(command) == 2:
                    self.socket.send(str.encode('rget,'+command[1]))
                    data = self.socket.recv(1024).decode()
                    if data == "FileNotFoundError":
                        print("Error: File not found")
                    else:
                        with open(os.path.splitext(command[1])[0]+"_local.txt", 'w') as f:
                            while('EOF' not in data):
                                f.write(data)
                                data = self.socket.recv(1024).decode()
                            f.write(data.strip("EOF"))
                        print("Downloaded File")
                else:
                    print("Usage: rget <filename>")
            #Terminate the connection until we need it again (Cookie for reconnect)
            self.quit()

CLIENT = Client()
CLIENT.run()
