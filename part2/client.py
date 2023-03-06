#!/usr/bin/python3
# hw1 client
import socket
import sys

host = sys.argv[1]
port = int(sys.argv[2])

client_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_tcp.connect((host, port))
welcome_message = ("********************************\n"
                       "** Welcome to the BBS server. **\n"
                       "********************************\n")
print(welcome_message)
UID =  "-1"

while True:
    cmd = input("% ")
    request = cmd.split()
    if (request[0] == "register"):
        client_udp.sendto(cmd.encode(), (host, port))
        response, addr = client_udp.recvfrom(1024)
        print(response.decode())
    elif (request[0] == "whoami"):
        cmd = cmd + " " + UID
        client_udp.sendto(cmd.encode(), (host, port))
        response, addr = client_udp.recvfrom(1024)
        print(response.decode())
    elif (request[0] == "login") :
        client_tcp.sendall(cmd.encode())
        response = client_tcp.recv(1024)
        tmp = response.decode().split()
        
        if (tmp[0] == "Welcome,"):
            print(tmp[0] + " " + tmp[1])
            UID = tmp[2]
        else :
            print(response.decode())
    elif (request[0] == "logout"):
        cmd = cmd + " " + UID
        client_tcp.sendall(cmd.encode())
        response = client_tcp.recv(1024)
        print(response.decode())
    elif (request[0] == "create-board" or request[0] == "list-board" or request[0] == "list-user" or request[0] == "create-post" or request[0] == "update-list" or request[0] == "read" or request[0] == "delete-post" or request[0] == "update-post" or request[0] == "comment" or request[0] == "list-post") :
        client_tcp.sendall(cmd.encode())
        response = client_tcp.recv(1024)
        print(response.decode())
    elif (request[0] == "exit"):
        client_tcp.sendall(cmd.encode())
        break
        

client_tcp.close()
client_udp.close()
    
#ln -s client.py client
        


    
