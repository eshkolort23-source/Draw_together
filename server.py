import socket
import json 
import base
import threading

class Server:
    def __init__(self, host='127.0.0.1', port=6767):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.running = True
        
        self.rooms = {}  # {room_key: [client_socket1, client_socket2]}
        self.socket_rooms = {}  # {client_socket: (category, pic_num, username)}
        self.lock = threading.Lock()

        # איפוס חדרים ישנים במסד הנתונים בעת הפעלת השרת
        try:
            if hasattr(base, 'reset_rooms'):
                base.reset_rooms()
        except Exception as e:
            print(f"Error resetting rooms: {e}")

        self.listen_thread = threading.Thread(target=self.start_listening, daemon=True)
        self.listen_thread.start()

    def start_listening(self):
        self.server_socket.listen()
        print(f"Server is listening continuously on {self.host}:{self.port}")
        while self.running:
            try:
                client_socket, client_address = self.server_socket.accept()
                threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True).start()
            except Exception as e:
                break

    def handle_client(self, client_socket):
        buffer = ""
        try:
            while self.running:
                data = client_socket.recv(65536)
                if not data:
                    break
                
                buffer += data.decode('utf-8', errors='ignore')
                
                # Handling multiple JSON messages in a single packet stream
                while "\n" in buffer:
                    message, buffer = buffer.split("\n", 1)
                    if not message.strip():
                        continue
                    try:
                        data_dec = json.loads(message)
                        inquiry_type = data_dec.get("Type of inquiry")

                        if inquiry_type == 6:  # פקודות DB
                            self.data_base(data_dec, client_socket)
                        elif inquiry_type == 7:  # העברת נתונים בחדר משותף (ציור, צ'אט, וידאו)
                            self.handle_room_broadcast(data_dec, client_socket)
                    except Exception as ex:
                        print("JSON parse error:", ex)
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            self.remove_client_from_rooms(client_socket)
            client_socket.close()

    def remove_client_from_rooms(self, client_socket):
        with self.lock:
            if client_socket in self.socket_rooms:
                category, pic_num, username = self.socket_rooms.pop(client_socket)
                room_key = f"{category}_{pic_num}"
                
                try:
                    if hasattr(base, 'leave_pair_room'):
                        base.leave_pair_room(username, category, pic_num)
                except Exception as e:
                    print("Error calling base.leave_pair_room:", e)

                if room_key in self.rooms and client_socket in self.rooms[room_key]:
                    self.rooms[room_key].remove(client_socket)
                    # הודעה לשאר השחקנים בחדר שהשותף התנתק
                    disconnect_msg = (json.dumps({
                        "Type of inquiry": 7,
                        "action": "partner_disconnected"
                    }) + "\n").encode('utf-8')
                    for sock in list(self.rooms[room_key]):
                        try:
                            sock.sendall(disconnect_msg)
                        except Exception:
                            pass
                    if not self.rooms[room_key]:
                        del self.rooms[room_key]

    def data_base(self, data, client_socket):
        parameters = data.get("parameters")
        issue = data.get("function name")

        if issue == "add_user_users":
            if isinstance(parameters, list):
                base.add_user_users(*parameters)
            else:
                base.add_user_users(parameters)
            response = json.dumps({"answer": "OK"}) + "\n"
            client_socket.sendall(response.encode('utf-8'))

        elif issue == "get_usernames_users":
            param = parameters[0] if isinstance(parameters, list) else parameters
            res = base.get_usernames_users(param)
            response = json.dumps({"answer": res}) + "\n"
            client_socket.sendall(response.encode('utf-8'))

        elif issue == "get_hash_and_salt_users":
            param = parameters[0] if isinstance(parameters, list) else parameters
            res = base.get_hash_and_salt_users(param)
            response = json.dumps({"answer": res}) + "\n"
            client_socket.sendall(response.encode('utf-8'))

        elif issue == "get_hobbies_users":
            param = parameters[0] if isinstance(parameters, list) else parameters
            res = base.get_hobbies_users(param)
            response = json.dumps({"answer": res}) + "\n"
            client_socket.sendall(response.encode('utf-8'))

        elif issue == "join_pair_room":
            if isinstance(parameters, list) and len(parameters) == 3:
                username, category, pic_num = parameters
                try:
                    pic_num = int(pic_num)
                except Exception:
                    pass
                room_key = f"{category}_{pic_num}"
                
                with self.lock:
                    if room_key not in self.rooms:
                        self.rooms[room_key] = []
                    if client_socket not in self.rooms[room_key]:
                        self.rooms[room_key].append(client_socket)
                    self.socket_rooms[client_socket] = (category, pic_num, username)
                    client_count = len(self.rooms[room_key])

                res = base.join_pair_room(username, category, pic_num)

                is_pair_ready = client_count >= 2

                response = json.dumps({"answer": is_pair_ready}) + "\n"
                try:
                    client_socket.sendall(response.encode('utf-8'))
                except Exception:
                    pass

                # אם יש 2 שחקנים בחדר, שידור הודעת room_ready לכל המשתתפים
                if is_pair_ready:
                    ready_msg = (json.dumps({
                        "Type of inquiry": 7,
                        "action": "room_ready",
                        "category": category,
                        "pictureNumber": pic_num,
                        "status": "ready"
                    }) + "\n").encode('utf-8')
                    with self.lock:
                        for sock in list(self.rooms.get(room_key, [])):
                            try:
                                sock.sendall(ready_msg)
                            except Exception:
                                pass
            else:
                response = json.dumps({"answer": False}) + "\n"
                try:
                    client_socket.sendall(response.encode('utf-8'))
                except Exception:
                    pass

        elif issue == "leave_pair_room":
            if isinstance(parameters, list) and len(parameters) == 3:
                username, category, pic_num = parameters
                try:
                    pic_num = int(pic_num)
                except Exception:
                    pass
                if hasattr(base, 'leave_pair_room'):
                    res = base.leave_pair_room(username, category, pic_num)
                else:
                    res = True
                room_key = f"{category}_{pic_num}"
                with self.lock:
                    if client_socket in self.socket_rooms:
                        del self.socket_rooms[client_socket]
                    if room_key in self.rooms and client_socket in self.rooms[room_key]:
                        self.rooms[room_key].remove(client_socket)
                        disconnect_msg = (json.dumps({
                            "Type of inquiry": 7,
                            "action": "partner_disconnected"
                        }) + "\n").encode('utf-8')
                        for sock in list(self.rooms[room_key]):
                            try:
                                sock.sendall(disconnect_msg)
                            except Exception:
                                pass
                        if not self.rooms[room_key]:
                            del self.rooms[room_key]

                response = json.dumps({"answer": res}) + "\n"
                try:
                    client_socket.sendall(response.encode('utf-8'))
                except Exception:
                    pass
            else:
                response = json.dumps({"answer": False}) + "\n"
                try:
                    client_socket.sendall(response.encode('utf-8'))
                except Exception:
                    pass

    def handle_room_broadcast(self, data, sender_socket):
        """שידור הודעה (ציור, צ'אט, מצלמה) לכל שאר המשתתפים בחדר"""
        category = data.get("category")
        pic_num = data.get("pictureNumber")
        try:
            pic_num = int(pic_num)
        except Exception:
            pass
        room_key = f"{category}_{pic_num}"

        msg_bytes = (json.dumps(data) + "\n").encode('utf-8')

        with self.lock:
            target_sockets = []
            if room_key in self.rooms:
                target_sockets = self.rooms[room_key]
            elif sender_socket in self.socket_rooms:
                cat, pnum, _ = self.socket_rooms[sender_socket]
                target_sockets = self.rooms.get(f"{cat}_{pnum}", [])

            for sock in list(target_sockets):
                if sock != sender_socket:
                    try:
                        sock.sendall(msg_bytes)
                    except Exception:
                        if sock in target_sockets:
                            target_sockets.remove(sock)

    def end(self):
        self.running = False
        try:
            self.server_socket.close()
        except:
            pass