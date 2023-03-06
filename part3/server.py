# hw1 server.py
import socket
import sys
import sqlite3
import threading
import datetime

board_list = []
board_name = []
post_name = []
post_num = 0
chatroom_port = {}
chatroom_status = {}
mutex = threading.Lock()
loginstatus = False

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
    user = "-1"
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
                user = request[1]
            else:
                client_socket.sendall("Usage: login <username> <password>".encode())
        elif (request[0] == "logout"):
            if (loginstatus == False):
                client_socket.send("Please login first.".encode())
            else:
                loginstatus = logout(client_socket, request[1])
        elif (request[0] == "list-user"):
            list_user(client_socket)
        elif (request[0] == "exit"):
            client_socket.close()
            break
        elif (request[0] == "create-board"):
            if (len(request) != 2):
                client_socket.send("Usage: create-board <name>.".encode())
            elif (loginstatus == False):
                client_socket.send("Please login first.".encode())
            else:
                create_board(client_socket ,request[1], user)
        elif (request[0] == "create-post"):
            if ("--title" in request):
                if ("--content" in request):
                    if (request.index("--title") == 2):
                        if (request.index("--content") != len(request)-1):
                            if (request.index("--title")+1 != request.index("--content")):
                                create_post(client_socket, request, loginstatus, user)
            else :
                client_socket.sendall("Usage: create-post <board-name> --title <title> --content <content>.".encode())
            
        elif (request[0] == "list-board"):
            list_board(request ,client_socket)
        elif (request[0] == "list-post"):
            list_post(client_socket, request)
        elif (request[0] == "read"):
            read(client_socket, request)
        elif (request[0] == "delete-post"):
            delete_post(loginstatus, client_socket, request, user)
        elif (request[0] == "update-post"):
            update_post(client_socket, request, user, loginstatus)
        elif (request[0] == "comment"):
            comment(client_socket, request, loginstatus, user)
        elif (request[0] == "create-chatroom"):
            create_chatroom(client_socket, request, loginstatus, user)
        elif (request[0] == "join-chatroom"):
            join_chatroom(client_socket, request, loginstatus)
        elif (request[0] == "leave-chatroom"):
            leave_chatroom(client_socket, request, user)
        elif (request[0] == "restart-chatroom"):
            restart_chatroom(client_socket, request, loginstatus, user)
        elif (request[0] == "attach"):
            attach(client_socket, request, loginstatus, user)
                

def udpconnect():
    while True:
        #print("start dealing with udp request")
        cmd, address = server_udpsocket.recvfrom(1024)
        request = cmd.decode().split()
        # register
        if (request[0] == "register"):
            if (len(request) == 4):
                register(address, request[1], request[2], request[3])
            else:
                server_udpsocket.sendto("Usage: register <username> <email> <password>".encode(), address)
        elif (request[0] == "whoami"):
            if (len(request) == 2):
                whoami(address, request[1])
        elif (request[0] == "list-chatroom"):
            list_chatroom(address, request)
        
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
    global chatroom_status
    state = "None"
    state = chatroom_status.get(n[0], "None")
    if (state == "open"):
        client_socket.sendall("do attach!".encode())
        connect.commit()
        connect.close()
        return True
    else:
        bye_message = "Bye, " + n[0] + "."
        client_socket.send(bye_message.encode())
        cursor.execute("""Delete from LoginStatus where UID == (?)""", (int(UID),))
        connect.commit()
        connect.close()
        return False

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

def create_board(client_socket, board_create, user):
    global board_name
    global board_list
    global mutex
    mutex.acquire()
    board = []
    if board_create in board_name:
        client_socket.send("Board already exists.".encode())
    else:
        board_name.append(board_create)
        board.append(board_create)
        board.append(user)
        board_list.append(board)
        client_socket.send("Create board successfully.".encode())
    mutex.release()

def list_board(request ,client_socket):
    global board_list
    global mutex
    mutex.acquire()
    if (len(request) != 1):
        client_socket.send("Usage: list-board".encode())
    else:
        cnt = 1
        s = "Index  Name    Moderator\n"
        for i in board_list:
            s += str(cnt)
            s += "  "
            s += i[0]
            s += "  "
            s += i[1]
            s += "\n"
            cnt += 1
        client_socket.send(s.encode())
    mutex.release()

def create_post(client_socket, request, loginstatus, user):
    global board_name
    global board_list
    global post_list
    global mutex
    mutex.acquire()
    if (loginstatus == False):
        client_socket.sendall("Please login first.".encode())
    elif (request[1] not in board_name):
        client_socket.sendall("Board does not exist.".encode())
    else:
        title = ""
        content = ""
        temp = ""
        for i in range(3, request.index("--content")):
            title += request[i] + " "

        for i in range(request.index("--content")+1, len(request)):
            if "<br>" in request[i]:
                temp = request[i].split("<br>")
                for j in range(0, len(temp)-1):
                    content += temp[j]
                    content += "\n"
                content += temp[len(temp)-1] + " "
            else:
                content += request[i] + " "
        global post_num
        post = []
        post_num = post_num + 1
        post.append(post_num)
        post.append(title)
        post.append(user)
        post.append(datetime.date.today().strftime("%m/%d"))
        post.append(content)
        #post.append(request[1])
        post_name.append(post)
        j = 0
        for i in board_list:
            if (i[0] == request[1]):
                board_list[j].append(post)
                client_socket.sendall("Create post successfully.".encode())
                break
            j += 1
    mutex.release()

def list_post(client_socket, request):
    global mutex
    mutex.acquire()
    if (len(request) != 2):
        client_socket.sendall("list-post <board-name>".encode())
    else:
        global board_name
        global board_list
        s = "S/N    Title   Author  Date\n"
        if request[1] in board_name:
            for i in board_list:
                if (i[0] == request[1]):
                    for j in range(2, len(i)):
                        s += str(i[j][0]) + "       " + str(i[j][1]) + "     " + str(i[j][2]) + "    " + str(i[j][3]) + "\n"
            client_socket.sendall(s.encode())
        else :
            client_socket.sendall("Board does not exist.".encode())
    mutex.release()
        
def read(client_socket, request):
    global post_name
    global mutex
    mutex.acquire()
    if (len(request) != 2):
        client_socket.sendall("Usage: read <post-S/N>".encode())
    elif(len(post_name) == 0):
        client_socket.sendall("Post does not exist.".encode())
    else:
        s = ""
        for i in post_name:
            if (i[0] == int(request[1])):
                s += "Author: " +  i[2]  + "\n" + "Title: " + i[1] + "\n" + "Date: " + i[3] + "\n--\n" + i[4]  + "\n--\n" 
                if (len(i) == 5):
                    break
                else:
                    for j in range(5, len(i)):
                        s += i[j]
                    break
        else:
            s = "Post does not exist."
        client_socket.sendall(s.encode())
    mutex.release()

def delete_post(loginstatus, client_socket, request, user):
    global mutex
    mutex.acquire()
    if (len(request) != 2):
        client_socket.sendall("Usage: delete-post <post-S/N>".encode())
    elif (loginstatus == False):
        client_socket.sendall("Please login first.".encode())
    else:
        global post_name
        global board_list
        s = ""
        cnt = 0
        for i in post_name:
            if (i[0] == int(request[1])):
                if (i[2] == user):
                    del post_name[cnt]
                    cnt2 = 0
                    for j in board_list:
                        for k in range(2, len(j)):
                            if(int(j[k][0]) == int(request[1])):
                                del board_list[cnt2][k]
                                s = "Delete successfully."
                                break
                        cnt2 = cnt2 + 1   
                else:
                    s = "Not the post owner."
                break
            else:
                s = "Post does not exist."
            cnt = cnt + 1
        client_socket.sendall(s.encode())
    mutex.release()
        
def update_post(client_socket, request, user, loginstatus):
    global mutex
    mutex.acquire()
    if (loginstatus == False):
        client_socket.sendall("Please login first.".encode())
    elif (len(request) < 4):
        client_socket.sendall("Usage: update-post <post-S/N> --title/content <new>.".encode())
    else:
        global post_name
        global board_list
        s = ""
        for i in post_name:
            if (int(request[1]) == i[0]):
                if (user == str(i[2])):
                    if(request[2] == "--title"):
                        tmp = ""
                        for j in range(3, len(request)):
                            tmp += str(request[j]) + " "
                        i[1] = tmp
                        s = "Update successfully."
                        break
                    elif (request[2] == "--content"):
                        content = ""
                        for k in range(3, len(request)):
                            if "<br>" in request[k]:
                                temp = request[k].split("<br>")
                                for j in range(0, len(temp)-1):
                                    content += temp[j]
                                    content += "\n"
                                content += temp[len(temp)-1] + " "
                            else:
                                content += request[k] + " "
                        # tmp = ""
                        # for j in range(3, len(request)):
                        #     tmp += str(request[j]) + " "
                        i[4] = content
                        # #i[3] = datetime.date.today().strftime("%m/%d")
                        s = "Update successfully."
                        break
                    else:
                        s = "Usage: update-post <post-S/N> --title/content <new>."
                else: 
                    s = "Not the post owner."
                break
            else:
                s = "Post does not exist."
        client_socket.sendall(s.encode())
    mutex.release()

def comment(client_socket, request, loginstatus, user):
    global mutex
    mutex.acquire()
    if (len(request) < 3):
        client_socket.sendall("Usage: comment <post-S/N> <comment>".encode())
    elif (loginstatus == False):
        client_socket.sendall("Please login first.".encode())
    else:
        global post_name
        for i in post_name:
            s = ""
            if (i[0] == int(request[1])):
                tmp = user + ": "
                for j in range(2, len(request)):
                    tmp += request[j] + " "
                tmp += "\n"
                i.append(tmp)
                s = "Comment successfully."
                break
            else:
                s = "Post does not exist."
        client_socket.sendall(s.encode())
    mutex.release()

def create_chatroom(client_socket, request, loginstatus, user):
    if (len(request) != 2):
        client_socket.sendall("Usage: create-chatroom <port>.".encode())
    elif (loginstatus == False):
        client_socket.sendall("Please login first.".encode())
    else:
        global chatroom_port
        global chatroom_status
        find = "None"
        find = chatroom_port.get(user, "None")
        if (find == "None"):
            chatroom_port[user] = request[1]
            chatroom_status[user] = "open"
            client_socket.sendall("start to create chatroom...".encode())
        else:
            client_socket.sendall("User has already created the chatroom.".encode())

def list_chatroom(address, request):
    if (len(request) != 1):
        server_udpsocket.sendto("Usage: list-chatroom.".encode())
    else:
        global chatroom_status
        response = "chatroom-name status\n"
        for key, value in chatroom_status.items():
            response += key + "     " + value + "\n"
        server_udpsocket.sendto(response.encode(), address)

def join_chatroom(client_socket, request, loginstatus):
    if (len(request) != 2):
        client_socket.sendall("Usage: join-chatroom <chatroom_name>".encode())
    elif (loginstatus == False):
        client_socket.sendall("Please login first.".encode())
    else:
        search = "None"
        search = chatroom_port.get(request[1], "None")
        if (search == "None"):
            client_socket.sendall("The chatroom does not exist or the chatroom is close.".encode())
        else :
            client_socket.sendall(str(search).encode())

def leave_chatroom(client_socket, request, user):
    if (len(request) != 1):
        client_socket.sendall("Usage: leave_chatroom".encode())
    else:
        global chatroom_status
        chatroom_status[user] = "close"

def restart_chatroom(client_socket, request, loginstatus, user):
    if (len(request) != 1):
        client_socket.sendall("Usage: restart-chatroom".encode())
    elif (loginstatus == False):
        client_socket.sendall("Please login first.".encode())
    else:
        global chatroom_status
        global chatroom_port
        find = "None"
        find = chatroom_port.get(user, "None")
        if (find == "None"):
            client_socket.sendall("Please create-chatroom first.".encode())
        else:
            state = chatroom_status[user]
            if (state == "open"):
                client_socket.sendall("Your chatroom is still running.".encode())
            else:
                chatroom_status[user] = "open"
                client_socket.sendall(find.encode())

def attach(client_socket, request, loginstatus, user):
    global chatroom_port
    global chatroom_status
    if (len(request) != 1):
        client_socket.sendall("Usage: attach".encode())
    elif (loginstatus == False):
        client_socket.sendall("Please login first.".encode())
    else:
        find = "None"
        find = chatroom_port.get(user, "None")
        if (find == "None"):
            client_socket.sendall("Please create-chatroom first.".encode())
        else:
            state = chatroom_status[user]
            if (state == "close"):
                client_socket.sendall("Please restart-chatroom first.".encode())
            else:
                client_socket.sendall("Welcome to the chatroom.".encode())

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

