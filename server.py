__author__ = "Christopher Sweet"
__doc__ = "Develop a custom concurrent FTP Server and it's associated FTP client"

import socket
import threading
import os
import sys

class Server():
    def __init__(self, port_num:int):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #Bind to an address
        self.socket.bind(('localhost', port_num))
        #Listen and allow for a backlog of 5 connections
        self.socket.listen(5)
        #Store data as it's uploaded
        self.data = []
        #Store all the server threads for cleanup when done
        self.threads = []

    def run_server(self):
        while True:
            print('Awaiting Connection')
            connection, address = self.socket.accept()
            print('Connected to ', address)
            #Log the user in
            user, password = connection.recv(1024).decode().split(',')
            if user in USERS:
                if password != USERS[user]:
                    connection.send(str.encode("False"))
            connection.send(str.encode("True"))
            s = ServerThread(connection)
            self.threads.append(s)

        for t in self.threads:
            t.join()

class ServerThread(threading.Thread):
    def __init__(self, connection):
        #Connection for this client
        self.connection = connection
        #Store all the get and put threads for cleanup when done
        self.threads = []
        super().__init__()

    def run(self):
        while True:
            #Begin taking commands from client
            cmd, fname = self.connection.recv(1024).decode().split(',')
            if cmd == 'rget':
                g = GetThread(self.connection, fname)
                g.start()
                self.threads.append(g)
            elif cmd == 'rput':
                p = PutThread(self.connection, fname)
                p.start()
                self.threads.append(p)
            else:
                print("Error: Encountered unexpected command")

        for t in self.threads:
            t.join()

class GetThread(threading.Thread):
    def __init__(self, socket, fname):
        super().__init__()
        self.socket = socket
        self.fname = fname

    def run(self):
        try:
            with open(self.fname, 'rb') as f:
                packet = f.read(1024)
                while(packet):
                    self.socket.send(packet)
                    packet = f.read(1024)
            #Alert the client that they have received their file in full
            self.socket.send(str.encode("EOF"))
        except FileNotFoundError as e:
            self.socket.send(str.encode("FileNotFoundError"))

    def quit(self):
        self.socket.close()

class PutThread(threading.Thread):
    def __init__(self, socket, fname):
        super().__init__()
        self.socket = socket
        self.fname = fname

    def run(self):
        with open(os.path.splitext(self.fname)[0]+"_server.txt", 'w') as f:
            data = self.socket.recv(1024).decode()
            while('EOF' not in data):
                f.write(data)
                data = self.socket.recv(1024).decode()
            f.write(data.strip("EOF"))
        print("Downloaded File")

    def quit(self):
        self.socket.close()


# Global value for starting Client and Sever Port Numbers
SOCKETPORT = 8000
USERS = {}
with open('passwords_plain.txt', 'r') as f:
    for line in f:
        username, password = line.strip('\n',).split(",")
        USERS[username] = password

SERVER = Server(SOCKETPORT)
SERVER.run_server()
