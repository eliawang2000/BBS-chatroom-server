#!/usr/bin/python3
# hw1 client
import socket
import sys
import threading
import select
import time

host = sys.argv[1]
port = int(sys.argv[2])

client_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_tcp.connect((host, port))
as_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

welcome_message = ("********************************\n"
                       "** Welcome to the BBS server. **\n"
                       "********************************\n")
print(welcome_message)
chatroom_welcome_message = ("********************************\n"
                       "** Welcome to the chatroom. **\n"
                       "********************************\n")
UID =  "-1"
user = ""
client_socket=[]
inputs=[sys.stdin]
flag = True
comeback = False
exit_or_not = False
q = []

def autoserver():
    global comeback
    global q
    while True:
        if (comeback == True):
            break
        else:
            readable, _, _ = select.select(inputs, [], [], 0.1)
            for sck in readable:
                if (sck is sys.stdin):
                    continue
                else:
                    message = sck.recv(1024)
                    for mate in client_socket:
                        if (mate is not sck):
                            mate.sendall(message) 
                        tmp_message = message.decode()
                    if (tmp_message[0] == 's' and tmp_message[1] == 'y' and tmp_message[2] == 's'):
                        continue
                    else:
                        q.append(tmp_message)
                        #q.append("???")

def chatroom_accept():
    print(chatroom_welcome_message.strip())
    global client_socket
    global inputs
    global q
    global exit_or_not
    global as_server
    while exit_or_not == False:
        readable, _, _ = select.select([exit_or_not, as_server], [], [], 0.1)
        for sck in readable:
            if sck is as_server:
                conn, addr = as_server.accept()
                init = ""
                if (len(q) >= 3):
                    for i in q[-3:]:
                        init += i.strip() + "\n"
                else:
                    for i in q:
                        init += i.strip() + "\n"
                conn.sendall(init.encode())
                conn.setblocking(0)
                client_socket.append(conn)
                inputs.append(conn)
            else:
                exit_or_not = True
        
def chat_server(user, request):
    global client_socket
    global inputs
    global flag
    global comeback
    global q
    comeback = True
    if (request.strip() == "attach"):
        print(chatroom_welcome_message.strip())
        for i in range(len(q)-3, len(q)):
            print(q[i].strip())
    while flag:
        readable, _, _ = select.select(inputs, [], [], 0.1)
        for sck in readable:
            if (sck is sys.stdin):
                t = time.localtime()
                result = time.strftime("%H:%M", t)
                message = user + "[" + result + "]:"
                command = sys.stdin.readline()
                message += command
                if (command.strip() == "detach"):
                    flag = False
                    comeback = False
                    t = threading.Thread(target = autoserver)
                    t.start()
                    print("Welcome back to BBS.")
                    break
                elif (command.strip() == "leave-chatroom"):
                    for mate in client_socket:
                        mate.sendall(command.encode())
                    flag = False
                    comeback = True
                    print("Welcome back to BBS.")
                    client_tcp.sendall(command.encode())
                    break
                else :    
                    for mate in client_socket:
                        mate.sendall(message.encode())
                    q.append(message)
                    #q.append("!!!")
            else:
                message = sck.recv(1024)
                print(message.decode().strip())
                for mate in client_socket:
                    if (mate is not sck):
                        mate.sendall(message) 
                message = message.decode()
                if (message[0] == 's' and message[1] == 'y' and message[2] == 's'):
                    continue
                else:
                    if (message[0] == 's' and message[1] == 'y' and message[2] == 's'):
                            continue
                    else:
                        q.append(message)
                        #q.append("~~~")
            
def chat_client(as_client, user):
    global client_tcp
    leave_or_not = False
    print(chatroom_welcome_message.strip())
    t = time.localtime()
    result = time.strftime("%H:%M", t)
    sys_str = "sys[" + result +"]:" + user + " join us."
    as_client.sendall(sys_str.encode())
    while leave_or_not == False:
        readable, _, _ = select.select([sys.stdin, as_client], [], [], 0.1)
        for sck in readable:
            if (sck is sys.stdin):
                t = time.localtime()
                result = time.strftime("%H:%M", t)
                message = user + "[" + result + "]:"
                command = sys.stdin.readline()
                message += command
                if (command.strip() == "leave-chatroom"):
                    leave_or_not = True
                    print("Welcome back to BBS.")
                    t = time.localtime()
                    result = time.strftime("%H:%M", t)
                    sys_str = "sys[" + result +"]:" + user + " leave us."
                    as_client.sendall(sys_str.encode())
                    break
                else:
                    as_client.sendall(message.encode())
            else:
                message = sck.recv(1024)
                if (message.decode().strip() == "leave-chatroom"):
                    leave_or_not = True
                    t = time.localtime()
                    result = time.strftime("%H:%M", t)
                    print("sys[" + result + "]: the chatroom is close.")
                    print("Welcome back to BBS.")
                    break
                else:
                    print(message.decode().strip())

        
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
        UID = "-1"
    elif (request[0] == "login") :
        client_tcp.sendall(cmd.encode())
        response = client_tcp.recv(1024)
        tmp = response.decode().split()
        if (tmp[0] == "Welcome,"):
            print(tmp[0] + " " + tmp[1])
            UID = tmp[2]
            user = request[1].replace(".", "")
        else :
            print(response.decode())
    elif (request[0] == "logout"):
        cmd = cmd + " " + UID
        client_tcp.sendall(cmd.encode())
        response = client_tcp.recv(1024)
        res = response.decode().split()
        if (res[0] == "do"):
            print("Please do “attach” and “leave-chatroom” first.")
        else:
            print(response.decode())
    elif (request[0] == "create-board" or request[0] == "list-board" or request[0] == "list-user" or request[0] == "create-post" or request[0] == "update-list" or request[0] == "read" or request[0] == "delete-post" or request[0] == "update-post" or request[0] == "comment" or request[0] == "list-post") :
        client_tcp.sendall(cmd.encode())
        response = client_tcp.recv(1024)
        print(response.decode())
    elif (request[0] == "exit"):
        client_tcp.sendall(cmd.encode())
        exit_or_not = True
        break
    elif (request[0] == "create-chatroom"):
        client_tcp.sendall(cmd.encode())
        response = client_tcp.recv(1024)
        print(response.decode().strip())
        as_server.bind((host, int(request[1])))
        as_server.listen(5)
        thread = threading.Thread(target = chatroom_accept)
        thread.start()
        flag = True
        chat_server(user, request[0])
    elif (request[0] == "list-chatroom"):
        if (UID == "-1"):
            print("Please login first.")
        else:
            client_udp.sendto(cmd.encode(), (host, port))
            response, addr = client_udp.recvfrom(1024)
            print(response.decode())
    elif (request[0] == "join-chatroom"):
        client_tcp.sendall(cmd.encode())
        response = client_tcp.recv(1024)
        tmp = response.decode().split()
        if (tmp[0] == "None" or tmp[0] == "Usage:" or tmp[0] == "Please"):
            print(response.decode())
        else :
            as_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)    
            as_client.connect((host, int(tmp[0])))
            chat_client(as_client, user)
    elif (request[0] == "attach"):
        client_tcp.sendall(cmd.encode())
        response = client_tcp.recv(1024).decode()
        tmp = response.split()
        if (tmp[0] != "Welcome"):
            print(response)
        else:
            flag = True
            chat_server(user, request[0])
    elif (request[0] == "restart-chatroom"):
        client_tcp.sendall(cmd.encode())
        response = client_tcp.recv(1024).decode()
        res = response.split()
        if (len(res) == 1):
            print("start to create chatroom...")
            print(chatroom_welcome_message.strip())
            for i in range(len(q)-3, len(q)):
                print(q[i].strip())
            flag = True
            chat_server(user, request[0])
        else:
            print(response.strip())
        

client_tcp.close()
client_udp.close()
    
#ln -s client.py client
        


    
