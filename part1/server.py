# hw1 server.py
import socket
import sys
import sqlite3
import threading


def tcpconnect():
    while True:
        client_socket, client_addr = server_tcpsocket.accept()
        print('New Connection From', client_addr)
        thread = threading.Thread(target = handle, args = (client_socket,))
        thread.start()
        #print("tcp conn")

def handle(client_socket):
    #print("handle")
    loginstatus = False
    while True:
        cmd = client_socket.recv(1024)
        #print(cmd)
        request = cmd.decode().split()
        if (request[0] == "login"):
            if (loginstatus == True):
                if (len(request) == 3):
                    client_socket.send("Please logout first.".encode())
                else:
                    client_socket.sendall("Usage: login <username> <password>".encode())
            elif (len(request) == 3 and loginstatus == False):
                loginstatus = login(client_socket, request[1], request[2])
            else:
                client_socket.sendall("Usage: login <username> <password>".encode())
        elif (request[0] == "logout"):
            # print(request)
            if (loginstatus == False):
                client_socket.send("Please login first.".encode())
            else:
                logout(client_socket, request[1])
                loginstatus = False
        elif (request[0] == "list-user"):
            list_user(client_socket)
        elif (request[0] == "exit"):
            client_socket.close()
            break


def udpconnect():
    while True:
        #print("start dealing with udp request")
        cmd, address = server_udpsocket.recvfrom(1024)
        request = cmd.decode().split()
        # register
        if (request[0] == "register"):
            if (len(request) == 4) :
                register(address, request[1], request[2], request[3])
            else:
                server_udpsocket.sendto("Usage: register <username> <email> <password>".encode(), address)
        elif (request[0] == "whoami"):
            if (len(request) == 2):
                whoami(address, request[1])
        

def register(address, name, mail, password):
    connect = sqlite3.connect("BBS.db")
    cursor = connect.cursor()
    num = cursor.execute("select count(*) from USERS as user where user.Username== (?)", (name,))
    n = num.fetchone()
    if (n[0] == 0) :
        sql = """INSERT INTO USERS (Username, Email, Password) VALUES (?, ?, ?)"""
        cursor.execute(sql, (name, mail, password))
        connect.commit()
        connect.close()
        server_udpsocket.sendto("Register successfully.".encode(), address)
    else :
        server_udpsocket.sendto("Username is already used.".encode(), address)

def login(client_socket, name, password):
    connect = sqlite3.connect("BBS.db")
    cursor = connect.cursor()
    user = cursor.execute("""select count(*) from USERS as user where user.Username == (?)""", (name,))
    n = user.fetchone()
    if (n[0] == 0):
        client_socket.sendall("Login failed.".encode())
        return False
    else :
        checkpw = cursor.execute("""select count(*) from USERS as user where user.Username == (?) AND user.Password = (?)""", (name, password,))
        n = checkpw.fetchone()
        if (n[0] == 0):
            client_socket.sendall("Login failed.".encode())
            return False
        else:
            sql = """INSERT INTO LoginStatus (Username) VALUES (?)"""
            cursor.execute(sql, (name,))
            UID = cursor.execute("""select UID from Loginstatus as user where user.Username == (?) order by UID desc""", (name,))
            UID = UID.fetchone()
            user = cursor.execute("""select * from LoginStatus""")
            n = user.fetchall()
            # print(n)
            connect.commit()
            connect.close()
            client_socket.send(("Welcome, " + name + ". " + str(UID[0])).encode())
            return True

def logout(client_socket, UID):
    connect = sqlite3.connect("BBS.db")
    cursor = connect.cursor()
    user = cursor.execute("""select Username from LoginStatus where UID == (?)""", (int(UID),))
    n = user.fetchone()
    bye_message = "Bye, " + n[0] + "."
    client_socket.send(bye_message.encode())
    cursor.execute("""Delete from LoginStatus where UID == (?)""", (int(UID),))
    user = cursor.execute("""select * from LoginStatus""")
    n = user.fetchall()
    # print(n)
    connect.commit()
    connect.close()

def whoami(address, UID):
    connect = sqlite3.connect("BBS.db")
    cursor = connect.cursor()
    user = cursor.execute("""select Username from LoginStatus where UID== (?)""", (int(UID),))
    n = user.fetchone()
    if (not n):
        server_udpsocket.sendto("Please login first.".encode(), address)
    else:
        server_udpsocket.sendto(n[0].encode(), address)

def list_user(client_socket):
    connect = sqlite3.connect("BBS.db")
    cursor = connect.cursor()
    usernum = cursor.execute("""select count(*) from USERS""")
    usernum = usernum.fetchone()
    if (usernum[0] == 0):
        client_socket.send("No users so far.".encode())
    else:
        client_list = cursor.execute("""select  Username, Email from USERS""")
        client_list = client_list.fetchall()
        user_list = "Name       Email\n"
        for i in client_list:
            user_list += i[0]
            user_list += "      "
            user_list += i[1]
            user_list += "\n"
        client_socket.send(user_list.encode())

# main
host = "127.0.0.1"
port = int(sys.argv[1])

#create database
connect = sqlite3.connect("BBS.db")
cursor = connect.cursor()
sql = """CREATE TABLE IF NOT EXISTS USERS(
            UID INTEGER PRIMARY KEY AUTOINCREMENT,
            Username TEXT NOT NULL UNIQUE,
            Email TEXT NOT NULL,
            Password TEXT NOT NULL
            );"""
cursor.execute(sql)
connect.commit()

sql = """CREATE TABLE IF NOT EXISTS LoginStatus(
            UID INTEGER PRIMARY KEY AUTOINCREMENT,
            Username TEXT NOT NULL 
            );"""
cursor.execute(sql)
connect.commit()
connect.close()

server_udpsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_tcpsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_udpsocket.bind((host, port))
server_tcpsocket.bind((host, port))
server_tcpsocket.listen(5)
server_tcpsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

#while True:
tcpthread = threading.Thread(target = tcpconnect)
tcpthread.start()
udpthread = threading.Thread(target = udpconnect)
udpthread.start()

