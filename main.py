import GUY
import server
import threading
import time

def start_server_data():
    server_data = server.Server(port=6767)

def newPlayer():
    s = GUY.pageStart()

def newPlayer1():
    s = GUY.pageStart()

if __name__ == '__main__':
    # הפעלת שרת הנתונים והחדרים
    t1 = threading.Thread(target=start_server_data, daemon=True)
    t1.start()

    # המתנה קצרה כדי לוודא שהשרת פתח את הסוקט ומאזין
    time.sleep(0.5)

    # הפעלת שחקן 1
    t3 = threading.Thread(target=newPlayer)
    t3.start()

    # המתנה קצרה והפעלת שחקן 2
    time.sleep(0.3)
    t4 = threading.Thread(target=newPlayer1)
    t4.start()