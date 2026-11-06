import socket
import json
import threading

class Client:#test
    def __init__(self, host='127.0.0.1', port=6767):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((host, port))
        self.lock = threading.Lock() 
        self.working = True

    def sendData(self, data_str):
        with self.lock:
            self.client_socket.sendall(data_str.encode('utf-8'))
        return self.recv()

    def send_only(self, data_str):
        """שליחת נתונים בלבד מבלי לחכות לתשובה (מתאים לצ'אט, ציור ומצלמה)"""
        with self.lock:
            try:
                self.client_socket.sendall(data_str.encode('utf-8'))
            except Exception as e:
                print(f"Error in send_only: {e}")

    def recv(self):
        try:
            data = self.client_socket.recv(65536)
            return data
        except:
            return b""

    def end(self):
        self.working = False
        try:
            self.client_socket.close()
        except:
            pass