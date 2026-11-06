import os
import tkinter as tk
import secrets
import hashlib
import hmac
from tkinter import messagebox
import glob
from PIL import Image, ImageTk
import server
import client
import json
import cv2
import base64
import numpy as np
import threading

def server_push_data(namePunc, parameters):
    try:
        data_Client = client.Client(port=6767)
        data = {"Type of inquiry": 6, "function name": namePunc, "parameters": parameters}
        data_str = json.dumps(data) + "\n"
        data_Client.send_only(data_str)
        data_Client.end()
    except Exception as e:
        print(f"Error in server_push_data: {e}")

def server_get_data(namePunc, parameters):
    try:
        data_Client = client.Client(port=6767)
        data = {"Type of inquiry": 6, "function name": namePunc, "parameters": parameters}
        data_str = json.dumps(data) + "\n"
        data_Client.client_socket.settimeout(3.0)
        data_recv = data_Client.sendData(data_str)
        data_Client.end()
        if not data_recv:
            return None
        line = data_recv.decode('utf-8').strip().split("\n")[0]
        res_dict = json.loads(line)
        return res_dict.get("answer")
    except Exception as e:
        print(f"Error in server_get_data: {e}")
        return None


class standartPage:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Draw Together")
        self.root.geometry("1200x800")
        self.root.state("zoomed")
        self.root.configure(bg="#f5f2ec")
        self.root.bind("<Escape>", self.closeWindow)
        self.backgroundImage = None
        self.createBackground()

    def createBackground(self):
        if os.path.exists("background.png"):
            try:
                self.backgroundImage = tk.PhotoImage(file="background.png")
                backgroundLabel = tk.Label(self.root, image=self.backgroundImage, borderwidth=0)
                backgroundLabel.place(relx=0, rely=0, relwidth=1, relheight=1)
            except tk.TclError:
                pass

    def createText(self, text, x, y, width, height, size=20, color="#ff3333"):
        label = tk.Label(self.root, text=text, bg=color, fg="#111111", font=("Arial", size))
        label.place(relx=x, rely=y, relwidth=width, relheight=height)
        return label

    def createButton(self, text, command, x, y, width, height, color="#078844", size=17):
        button = tk.Button(self.root, text=text, command=command, bg=color, fg="#111111", activebackground=color, font=("Arial", size), borderwidth=0)
        button.place(relx=x, rely=y, relwidth=width, relheight=height)
        return button

    def createImageArea(self, text, x, y, width, height, command=None):
        if command is None:
            area = tk.Label(self.root, text=text, bg="#5b18ed", fg="#111111", font=("Arial", 16))
        else:
            area = tk.Button(self.root, text=text, command=command, bg="#5b18ed", fg="#111111", activebackground="#5b18ed", font=("Arial", 14), borderwidth=0)
        area.place(relx=x, rely=y, relwidth=width, relheight=height)
        return area

    def closeWindow(self, event=None):
        try:
            if self.root.winfo_exists():
                self.root.destroy()
        except:
            pass


class ColorButton:
    def __init__(self, parent, color, command, x, y, size):
        self.color = color
        self.command = command
        self.canvas = tk.Canvas(parent, bg="#999999", highlightthickness=0)
        self.canvas.place(relx=x, rely=y, relwidth=size, relheight=size)
        self.circle = self.canvas.create_oval(3, 3, 57, 57, fill=self.color, outline="#555555", width=2)
        self.canvas.tag_bind(self.circle, "<Button-1>", self.press)
        self.canvas.bind("<Configure>", self.resize)

    def resize(self, event):
        space = 4
        diameter = min(event.width, event.height) - space * 2
        self.canvas.coords(self.circle, space, space, space + diameter, space + diameter)

    def press(self, event):
        self.command(self.color)


class BrushSizeButton:
    def __init__(self, parent, command, x, y, size):
        self.command = command
        self.diameter = 28
        self.canvas = tk.Canvas(parent, bg="#999999", highlightthickness=0, cursor="hand2")
        self.canvas.place(relx=x, rely=y, relwidth=size, relheight=size)
        self.circle = self.canvas.create_oval(0, 0, 0, 0, fill="#ffffff", outline="#555555", width=2)
        self.text = self.canvas.create_text(0, 0, text=str(self.diameter), font=("Arial", 10, "bold"), fill="#111111")
        
        self.canvas.bind("<Configure>", self.resize)
        
        # לחיצה שמאלית: הגדלת גודל המכחול
        self.canvas.bind("<Button-1>", self.increaseSize)
        self.canvas.tag_bind(self.circle, "<Button-1>", self.increaseSize)
        self.canvas.tag_bind(self.text, "<Button-1>", self.increaseSize)

        # לחיצה ימנית: הקטנת גודל המכחול
        self.canvas.bind("<Button-3>", self.decreaseSize)
        self.canvas.tag_bind(self.circle, "<Button-3>", self.decreaseSize)
        self.canvas.tag_bind(self.text, "<Button-3>", self.decreaseSize)

        # גלגלת עכבר
        self.canvas.bind("<MouseWheel>", self.changeSizeWheel)
        try:
            self.canvas.bind("<Button-4>", lambda e: self.stepSize(4))
            self.canvas.bind("<Button-5>", lambda e: self.stepSize(-4))
        except Exception:
            pass

    def resize(self, event):
        self.drawCircle()

    def drawCircle(self):
        try:
            width = self.canvas.winfo_width()
            height = self.canvas.winfo_height()
            if width <= 1 or height <= 1:
                return
            maximum = max(8, min(width, height) - 8)
            diameter = min(self.diameter, maximum)
            centerX = width / 2
            centerY = height / 2
            radius = diameter / 2
            self.canvas.coords(self.circle, centerX - radius, centerY - radius, centerX + radius, centerY + radius)
            self.canvas.coords(self.text, centerX, centerY)
            self.canvas.itemconfig(self.text, text=str(self.diameter))
        except Exception:
            pass

    def increaseSize(self, event=None):
        sizes = [6, 12, 18, 24, 28, 36, 46, 56]
        next_sizes = [s for s in sizes if s > self.diameter]
        self.diameter = next_sizes[0] if next_sizes else sizes[0]
        self.drawCircle()
        self.command(self.diameter)

    def decreaseSize(self, event=None):
        sizes = [6, 12, 18, 24, 28, 36, 46, 56]
        prev_sizes = [s for s in sizes if s < self.diameter]
        self.diameter = prev_sizes[-1] if prev_sizes else sizes[-1]
        self.drawCircle()
        self.command(self.diameter)

    def stepSize(self, step):
        self.diameter = max(6, min(56, self.diameter + step))
        self.drawCircle()
        self.command(self.diameter)

    def changeSizeWheel(self, event):
        step = 4 if getattr(event, "delta", 0) > 0 else -4
        self.stepSize(step)


class DrawingTools:
    def __init__(self):
        self.currentColor = "#111111"
        self.currentBrushSize = 28

    def createDrawingTools(self, x, y, width, height):
        toolbar = tk.Frame(self.root, bg="#999999")
        toolbar.place(relx=x, rely=y, relwidth=width, relheight=height)
        colors = ["#e63946", "#ff8c00", "#ffd60a", "#22c55e", "#00b4d8", "#2563eb", "#7c3aed", "#ec4899", "#111111", "#ffffff"]
        left = x + width * 0.02
        buttonSize = min(width * 0.07, height * 0.58)
        gap = width * 0.01
        for index, color in enumerate(colors):
            ColorButton(self.root, color, self.chooseColor, left + index * (buttonSize + gap), y + height * 0.08, buttonSize)
        self.brushSizeButton = BrushSizeButton(self.root, self.changeBrushSize, x + width * 0.88, y + height * 0.08, buttonSize)
        self.createText("COLORS", x + width * 0.25, y + height * 0.76, width * 0.22, height * 0.20, 15, "#f5f2ec")
        self.createText("BRUSH SIZE", x + width * 0.82, y + height * 0.76, width * 0.17, height * 0.20, 13, "#f5f2ec")

    def chooseColor(self, color):
        self.currentColor = color

    def changeBrushSize(self, value):
        self.currentBrushSize = value


class pageStart(standartPage):
    def __init__(self):
        super().__init__()
        self.buttons = {}
        self.createText("WELCOME", 0.125, 0.035, 0.53, 0.17, 45)
        self.buttons["buttonLogIn"] = self.createButton("LOG IN", self.logIn, 0.055, 0.245, 0.14, 0.25)
        self.buttons["buttonSignUp"] = self.createButton("SIGN UP", self.signUp, 0.055, 0.565, 0.14, 0.25)
        self.createImageArea("ROTATING WEEKLY GAME IMAGES", 0.26, 0.24, 0.71, 0.73)
        self.root.mainloop()

    def logIn(self):
        self.closeWindow()
        pageLogIn()

    def signUp(self):
        self.closeWindow()
        pageSignUp()

class pageLogIn(standartPage):
    def __init__(self):
        super().__init__()
        self.createText("USERNAME", 0.755, 0.235, 0.20, 0.15, 19)
        self.createText("PASSWORD", 0.755, 0.48, 0.20, 0.15, 19)
        self.userName = tk.Entry(self.root, font=("Arial", 23), bg="#b36a4d", borderwidth=0)
        self.userName.place(relx=0.275, rely=0.237, relwidth=0.415, relheight=0.15)
        self.password = tk.Entry(self.root, font=("Arial", 23), bg="#b36a4d", show="*", borderwidth=0)
        self.password.place(relx=0.275, rely=0.48, relwidth=0.415, relheight=0.15)
        self.buttonLogIn = self.createButton("LOG IN", self.logInButtonAction, 0.415, 0.795, 0.17, 0.15)
        self.root.mainloop()

    def hashPassword(self, password, salt):
        return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 600_000).hex()

    def checkPassword(self, password, salt, savedHash):
        newHash = self.hashPassword(password, salt)
        return hmac.compare_digest(newHash, savedHash)

    def logInButtonAction(self):
        entered_username = self.userName.get().strip()
        password_value = self.password.get()

        if not entered_username or not password_value:
            messagebox.showerror("Error", "Please fill in all fields")
            return

        result = server_get_data("get_hash_and_salt_users", entered_username)
        if result is None:
            messagebox.showerror("Error", "The nickname or password is wrong")
            return

        hash_password, salt_hex = result
        salt = bytes.fromhex(salt_hex)

        if self.checkPassword(password_value, salt, hash_password):
            self.closeWindow()
            pageMain(entered_username)
        else:
            messagebox.showerror("Error", "The nickname or password is wrong")

class pageSignUp(standartPage):
    def __init__(self):
        super().__init__()
        self.categoryVariables = []
        self.createCategoryArea()
        labels = ["USERNAME", "PASSWORD", "RE-ENTER PASSWORD", "AGE"]
        entries = []
        for index, labelText in enumerate(labels):
            y = 0.055 + index * 0.15
            self.createText(labelText, 0.762, y, 0.20, 0.10, 16)
            showValue = "*" if "PASSWORD" in labelText else ""
            entry = tk.Entry(self.root, font=("Arial", 19), bg="#b36a4d", show=showValue, borderwidth=0)
            entry.place(relx=0.31, rely=y + 0.003, relwidth=0.415, relheight=0.097)
            entries.append(entry)
        self.userName, self.password, self.rePassword, self.age = entries
        self.buttonSignUp = self.createButton("SIGN UP", self.signUpButtonAction, 0.415, 0.795, 0.17, 0.15)
        self.root.mainloop()

    def createCategoryArea(self):
        categoryFrame = tk.Frame(self.root, bg="#c13dde")
        categoryFrame.place(relx=0.02, rely=0.035, relwidth=0.27, relheight=0.925)
        title = tk.Label(categoryFrame, text="CHOOSE FAVORITE CATEGORIES", bg="#c13dde", fg="#111111", font=("Arial", 15, "bold"))
        title.pack(pady=(15, 8))
        self.categories = ["Animals", "Nature", "Love", "Fantasy",
                           "Food", "Sports", "Music", "Space",
                            "Cities", "Vehicles", "People", "Clothes",
                             "Flowers", "History", "Sea", "Technology"]
        checksFrame = tk.Frame(categoryFrame, bg="#c13dde")
        checksFrame.pack(fill=tk.BOTH, expand=True, padx=12, pady=5)
        for index, category in enumerate(self.categories):
            variable = tk.IntVar()
            self.categoryVariables.append(variable)
            check = tk.Checkbutton(checksFrame, text=category, variable=variable, bg="#c13dde", activebackground="#c13dde", anchor="w", font=("Arial", 15))
            check.grid(row=index % 8, column=index // 8, sticky="nsew", padx=5, pady=5)
        for row in range(8):
            checksFrame.grid_rowconfigure(row, weight=1)
        for column in range(2):
            checksFrame.grid_columnconfigure(column, weight=1)

    def strongPassword(self, password):
        checkStrong = [0, 0, 0]
        for ch in password:
            if ch.isdigit():
                checkStrong[0] = 1
            if ch.islower():
                checkStrong[1] = 1
            if ch.isupper():
                checkStrong[2] = 1
        return sum(checkStrong) == 3

    def creatSalt(self):
        return secrets.token_bytes(16)

    def hashPassword(self, password):
        salt = self.creatSalt()
        return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 600_000).hex(), salt

    def signUpButtonAction(self):
        if self.password.get() == self.rePassword.get():
            if not self.strongPassword(self.password.get()):
                messagebox.showerror("Error", "weak password (must contain uppercase, lowercase and numbers)")
                return
            
            age_str = self.age.get().strip()
            if not age_str.isdigit():
                messagebox.showerror("Error", "Please enter a valid numeric age")
                return

            ageNum = int(age_str)
            if ageNum < 5 or ageNum > 120:
                messagebox.showerror("Error", "Please enter a realistic age")
                return

            selected_categories = [
                category
                for category, variable in zip(self.categories, self.categoryVariables)
                if variable.get() == 1
            ]

            password_hash, salt = self.hashPassword(self.password.get())
            server_push_data("add_user_users", [self.userName.get(), password_hash, salt.hex(), selected_categories])
            
            user = self.userName.get()
            self.closeWindow()
            pageMain(user)
        else:
            messagebox.showerror("Error", "the password and the repassword not identical")


class pageOneDraw(standartPage, DrawingTools):
    def __init__(self, pictureNumber, category, roomNumber, username):
        standartPage.__init__(self)
        DrawingTools.__init__(self)
        self.username = username
        self.category = category
        self.pictureNumber = pictureNumber
        
        self.buttonBack = self.createButton("BACK", self.back, 0.16, 0.017, 0.075, 0.18)
        self.createDrawingTools(0.27, 0.027, 0.60, 0.16)
        self.drawingCanvas = tk.Canvas(self.root, bg="#ffffff", highlightthickness=0)
        self.drawingCanvas.place(relx=0.16, rely=0.235, relwidth=0.71, relheight=0.735)
        
        self.root.after(100, self.loadCanvasBackground)

        self.drawingCanvas.bind("<B1-Motion>", self.draw)
        self.last_x, self.last_y = None, None
        self.drawingCanvas.bind("<Button-1>", self.reset_coords)
        self.root.mainloop()

    def loadCanvasBackground(self):
        try:
            search_roots = [
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "arts"),
                os.path.join(os.getcwd(), "arts"),
                os.path.join(r"C:\Users\bugom\Downloads\פרויקט גמר 5 יחל מחשבים DRAW TOGETHER", "arts")
            ]
            matches = []
            for root in search_roots:
                if not os.path.isdir(root):
                    continue
                category_folder = os.path.join(root, str(self.category))
                matches = glob.glob(os.path.join(category_folder, f"pic{self.pictureNumber}.*"))
                if not matches:
                    matches = glob.glob(os.path.join(root, "**", f"pic{self.pictureNumber}.*"), recursive=True)
                if matches:
                    break
            if not matches:
                print(f"Artwork pic{self.pictureNumber} not found for category {self.category}")
                return

            image = Image.open(matches[0]).convert("RGBA")
            width = max(1, self.drawingCanvas.winfo_width())
            height = max(1, self.drawingCanvas.winfo_height())
            if width < 50 or height < 50:
                self.root.after(100, self.loadCanvasBackground)
                return
            scale = min((width - 40) / image.width, (height - 40) / image.height, 1.0)
            size = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
            resampling = getattr(Image, "Resampling", Image)
            image = image.resize(size, getattr(resampling, "LANCZOS", Image.BICUBIC))
            self.bg_photo = ImageTk.PhotoImage(image, master=self.root)

            old_id = getattr(self, "bg_image_id", None)
            if old_id:
                self.drawingCanvas.delete(old_id)
            self.bg_image_id = self.drawingCanvas.create_image(
                width / 2, height / 2, anchor=tk.CENTER, image=self.bg_photo
            )
            self.drawingCanvas.tag_lower(self.bg_image_id)
        except Exception as e:
            print("Error loading background image:", e)

    def on_canvas_resize(self, event):
        if getattr(self, "bg_image_id", None):
            self.drawingCanvas.coords(self.bg_image_id, event.width / 2, event.height / 2)
    def back(self):
        self.closeWindow()
        pageMain(self.username)

    def reset_coords(self, event):
        self.last_x, self.last_y = event.x, event.y

    def draw(self, event):
        if self.last_x and self.last_y:
            self.drawingCanvas.create_line(
                self.last_x, self.last_y, event.x, event.y,
                fill=self.currentColor, width=self.currentBrushSize, capstyle=tk.ROUND, smooth=True
            )
        self.last_x, self.last_y = event.x, event.y


class pageTowDraw(standartPage, DrawingTools):
    def __init__(self, pictureNumber, category, roomNumber, username):
        standartPage.__init__(self)
        DrawingTools.__init__(self)
        self.username = username
        self.category = category
        try:
            self.pictureNumber = int(pictureNumber)
        except Exception:
            self.pictureNumber = pictureNumber
        self.roomNumber = roomNumber
        self.partner_connected = False  
        self.is_running = True
        
        self.buttonBack = self.createButton("BACK", self.back, 0.01, 0.02, 0.073, 0.18)
        self.createDrawingTools(0.09, 0.027, 0.60, 0.16)
        
        self.videoLabel1 = tk.Label(self.root, bg="black", text="My Camera", fg="white")
        self.videoLabel1.place(relx=0.745, rely=0.02, relwidth=0.11, relheight=0.18)
        self.videoLabel2 = tk.Label(self.root, bg="black", text="Waiting Partner...", fg="white")
        self.videoLabel2.place(relx=0.875, rely=0.02, relwidth=0.11, relheight=0.18)

        self.drawingCanvas = tk.Canvas(self.root, bg="#ffffff", highlightthickness=0)
        self.drawingCanvas.place(relx=0.02, rely=0.235, relwidth=0.71, relheight=0.735)
        
        # Load the selected artwork after Tk computes the canvas dimensions.
        self.root.after(100, self.loadCanvasBackground)
        self.drawingCanvas.bind("<Configure>", self.on_canvas_resize)
        
        self.drawingCanvas.bind("<B1-Motion>", self.draw)
        self.last_x, self.last_y = None, None
        self.drawingCanvas.bind("<Button-1>", self.reset_coords)

        chatFrame = tk.Frame(self.root, bg="#777777")
        chatFrame.place(relx=0.76, rely=0.255, relwidth=0.23, relheight=0.715)
        
        self.chatText = tk.Text(chatFrame, bg="#777777", fg="#f5f2ec", font=("Arial", 12), borderwidth=0)
        self.chatText.place(relx=0.03, rely=0.03, relwidth=0.86, relheight=0.73)
        self.chatText.config(state=tk.DISABLED)

        self.messageEntry = tk.Entry(chatFrame, bg="#b36a4d", font=("Arial", 14), borderwidth=0)
        self.messageEntry.place(relx=0.03, rely=0.78, relwidth=0.73, relheight=0.18)
        self.messageEntry.bind("<Return>", lambda event: self.sendMessage())

        self.buttonSend = tk.Button(chatFrame, text="SEND", command=self.sendMessage, bg="#078844", activebackground="#078844", borderwidth=0)
        self.buttonSend.place(relx=0.78, rely=0.78, relwidth=0.18, relheight=0.18)

        try:
            self.net_client = client.Client(port=6767)
        except Exception as e:
            print("Network connection error:", e)
            self.net_client = None

        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                self.cap = None
        except Exception:
            self.cap = None
            
        self.current_image = None
        self.partner_image = None

        # התחלת האזנה לתקשורת מהשרת והצטרפות לחדר
        if self.net_client:
            threading.Thread(target=self.listen_to_partner, daemon=True).start()
            self.send_join_room()

        self.update_video()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def send_join_room(self):
        if not self.is_running or not self.net_client:
            return
        if not self.partner_connected:
            packet = {
                "Type of inquiry": 6,
                "function name": "join_pair_room",
                "parameters": [self.username, self.category, self.pictureNumber]
            }
            self.net_client.send_only(json.dumps(packet) + "\n")
            self.root.after(3000, self.send_join_room)

    def unlock_drawing(self):
        if self.partner_connected:
            return
        self.partner_connected = True
        self.videoLabel2.configure(text="Partner Connected", bg="green")
        self.loadCanvasBackground()

    def lock_drawing(self):
        self.partner_connected = False
        self.videoLabel2.configure(image="", text="Waiting Partner...", bg="black")
        self.send_join_room()

    def loadCanvasBackground(self):
        try:
            search_roots = [
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "arts"),
                os.path.join(os.getcwd(), "arts"),
                os.path.join(r"C:\Users\bugom\Downloads\פרויקט גמר 5 יחל מחשבים DRAW TOGETHER", "arts")
            ]
            matches = []
            for root in search_roots:
                if not os.path.isdir(root):
                    continue
                category_folder = os.path.join(root, str(self.category))
                matches = glob.glob(os.path.join(category_folder, f"pic{self.pictureNumber}.*"))
                if not matches:
                    matches = glob.glob(os.path.join(root, "**", f"pic{self.pictureNumber}.*"), recursive=True)
                if matches:
                    break
            if not matches:
                print(f"Artwork pic{self.pictureNumber} not found for category {self.category}")
                return

            image = Image.open(matches[0]).convert("RGBA")
            width = max(1, self.drawingCanvas.winfo_width())
            height = max(1, self.drawingCanvas.winfo_height())
            if width < 50 or height < 50:
                self.root.after(100, self.loadCanvasBackground)
                return
            scale = min((width - 40) / image.width, (height - 40) / image.height, 1.0)
            size = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
            resampling = getattr(Image, "Resampling", Image)
            image = image.resize(size, getattr(resampling, "LANCZOS", Image.BICUBIC))
            self.bg_photo = ImageTk.PhotoImage(image, master=self.root)

            old_id = getattr(self, "bg_image_id", None)
            if old_id:
                self.drawingCanvas.delete(old_id)
            self.bg_image_id = self.drawingCanvas.create_image(
                width / 2, height / 2, anchor=tk.CENTER, image=self.bg_photo
            )
            self.drawingCanvas.tag_lower(self.bg_image_id)
        except Exception as e:
            print("Error loading background image:", e)

    def on_canvas_resize(self, event):
        if getattr(self, "bg_image_id", None):
            self.drawingCanvas.coords(self.bg_image_id, event.width / 2, event.height / 2)
    def update_video(self):
        if not self.is_running:
            return

        frame_to_send = None

        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_rgb = cv2.flip(frame_rgb, 1)
                frame_rgb = cv2.resize(frame_rgb, (160, 130))
                
                self.current_image = ImageTk.PhotoImage(image=Image.fromarray(frame_rgb), master=self.root)
                self.videoLabel1.configure(image=self.current_image, text="")
                frame_to_send = frame
        else:
            try:
                sim_frame = np.zeros((130, 160, 3), dtype=np.uint8)
                sim_frame[:] = (70, 40, 30)
                cv2.putText(sim_frame, str(self.username)[:8], (10, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(sim_frame, "CAM", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                frame_rgb = cv2.cvtColor(sim_frame, cv2.COLOR_BGR2RGB)
                self.current_image = ImageTk.PhotoImage(image=Image.fromarray(frame_rgb), master=self.root)
                self.videoLabel1.configure(image=self.current_image, text="")
                frame_to_send = sim_frame
            except Exception:
                pass

        if self.partner_connected and self.net_client and frame_to_send is not None:
            try:
                success, encoded_img = cv2.imencode('.jpg', frame_to_send, [cv2.IMWRITE_JPEG_QUALITY, 35])
                if success:
                    img_bytes_str = base64.b64encode(encoded_img).decode('utf-8')
                    packet = {
                        "Type of inquiry": 7,
                        "action": "video",
                        "category": self.category,
                        "pictureNumber": self.pictureNumber,
                        "data": img_bytes_str
                    }
                    self.net_client.send_only(json.dumps(packet) + "\n")
            except Exception:
                pass

        self.root.after(150, self.update_video)

    def show_partner_frame(self, pil_img):
        try:
            self.partner_image = ImageTk.PhotoImage(image=pil_img, master=self.root)
            self.videoLabel2.configure(image=self.partner_image, text="")
        except Exception:
            pass

    def listen_to_partner(self):
        buffer = ""
        while self.is_running and self.net_client and self.net_client.client_socket:
            try:
                data = self.net_client.client_socket.recv(65536)
                if not data:
                    break
                buffer += data.decode('utf-8', errors='ignore')
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if not line.strip():
                        continue
                    try:
                        packet = json.loads(line)
                    except Exception:
                        continue
                    
                    action = packet.get("action")
                    if action == "room_ready" or packet.get("answer") is True:
                        self.root.after(0, self.unlock_drawing)

                    elif action == "partner_disconnected":
                        self.root.after(0, self.lock_drawing)

                    elif action == "draw":
                        coords = packet.get("coords")
                        if coords and len(coords) == 6:
                            x1, y1, x2, y2, color, size = coords
                            self.root.after(0, lambda x1=x1, y1=y1, x2=x2, y2=y2, c=color, s=size: 
                                self.drawingCanvas.create_line(x1, y1, x2, y2, fill=c, width=s, capstyle=tk.ROUND, smooth=True))

                    elif action == "draw_dot":
                        coords = packet.get("coords")
                        if coords and len(coords) == 4:
                            x, y, color, size = coords
                            r = max(1, size // 2)
                            self.root.after(0, lambda x=x, y=y, r=r, c=color: 
                                self.drawingCanvas.create_oval(x - r, y - r, x + r, y + r, fill=c, outline=c))

                    elif action == "chat":
                        sender = packet.get("sender", "Partner")
                        msg = packet.get("message", "")
                        self.root.after(0, lambda s=sender, m=msg: self.append_chat(f"{s}: {m}"))

                    elif action == "video":
                        raw_data = packet.get("data")
                        if raw_data:
                            try:
                                img_data = base64.b64decode(raw_data)
                                np_arr = np.frombuffer(img_data, np.uint8)
                                decoded_frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                                if decoded_frame is not None:
                                    decoded_frame = cv2.cvtColor(decoded_frame, cv2.COLOR_BGR2RGB)
                                    pil_img = Image.fromarray(decoded_frame)
                                    self.root.after(0, lambda img=pil_img: self.show_partner_frame(img))
                            except Exception:
                                pass
            except Exception as e:
                print("Error listening to partner:", e)
                break

    def on_closing(self):
        self.is_running = False
        if self.cap and self.cap.isOpened():
            try:
                self.cap.release()
            except:
                pass
        if self.net_client:
            try:
                packet = {
                    "Type of inquiry": 6,
                    "function name": "leave_pair_room",
                    "parameters": [self.username, self.category, self.pictureNumber]
                }
                self.net_client.send_only(json.dumps(packet) + "\n")
            except:
                pass
            try:
                self.net_client.end()
            except:
                pass
        self.closeWindow()

    def back(self):
        self.is_running = False
        if self.cap and self.cap.isOpened():
            try:
                self.cap.release()
            except:
                pass
        if self.net_client:
            try:
                packet = {
                    "Type of inquiry": 6,
                    "function name": "leave_pair_room",
                    "parameters": [self.username, self.category, self.pictureNumber]
                }
                self.net_client.send_only(json.dumps(packet) + "\n")
            except:
                pass
            try:
                self.net_client.end()
            except:
                pass
        self.closeWindow()
        pageMain(self.username)

    def reset_coords(self, event):
        if not self.partner_connected:
            return
        self.last_x, self.last_y = event.x, event.y
        r = max(1, self.currentBrushSize // 2)
        self.drawingCanvas.create_oval(
            event.x - r, event.y - r, event.x + r, event.y + r,
            fill=self.currentColor, outline=self.currentColor
        )
        if self.net_client:
            packet = {
                "Type of inquiry": 7,
                "action": "draw_dot",
                "category": self.category,
                "pictureNumber": self.pictureNumber,
                "coords": (event.x, event.y, self.currentColor, self.currentBrushSize)
            }
            self.net_client.send_only(json.dumps(packet) + "\n")

    def draw(self, event):
        if not self.partner_connected:
            return  
        
        if self.last_x and self.last_y:
            self.drawingCanvas.create_line(
                self.last_x, self.last_y, event.x, event.y,
                fill=self.currentColor, width=self.currentBrushSize, capstyle=tk.ROUND, smooth=True
            )
            
            if self.net_client:
                packet = {
                    "Type of inquiry": 7,
                    "action": "draw",
                    "category": self.category,
                    "pictureNumber": self.pictureNumber,
                    "coords": (self.last_x, self.last_y, event.x, event.y, self.currentColor, self.currentBrushSize)
                }
                self.net_client.send_only(json.dumps(packet) + "\n")
            
        self.last_x, self.last_y = event.x, event.y

    def sendMessage(self):
        msg = self.messageEntry.get().strip()
        if msg:
            self.append_chat(f"{self.username}: {msg}")
            self.messageEntry.delete(0, tk.END)

            if self.net_client:
                packet = {
                    "Type of inquiry": 7,
                    "action": "chat",
                    "category": self.category,
                    "pictureNumber": self.pictureNumber,
                    "sender": self.username,
                    "message": msg
                }
                self.net_client.send_only(json.dumps(packet) + "\n")

    def append_chat(self, text):
        self.chatText.config(state=tk.NORMAL)
        self.chatText.insert(tk.END, text + "\n")
        self.chatText.config(state=tk.DISABLED)
        self.chatText.see(tk.END)


class ScrollableFrame(tk.Frame):
    def __init__(self, parent, bg):
        super().__init__(parent, bg=bg)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.content = tk.Frame(self.canvas, bg=bg)
        self.contentWindow = self.canvas.create_window((0, 0), window=self.content, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.content.bind("<Configure>", self.updateScrollRegion)
        self.canvas.bind("<Configure>", self.updateContentWidth)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def updateScrollRegion(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def updateContentWidth(self, event):
        self.canvas.itemconfigure(self.contentWindow, width=event.width)


class pageMain(standartPage):
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.pictureButtons = []
        self.pictureImages = []

        self.createText(f"HELLO {username.upper()}", 0.385, 0.04, 0.31, 0.075, 18)

        self.menuButton = tk.Menubutton(self.root, text="PAGE MENU", bg="#222222", fg="#f5f2ec", activebackground="#222222", font=("Arial", 17), borderwidth=0)
        self.menuButton.place(relx=0.73, rely=0.035, relwidth=0.23, relheight=0.085)

        self.pageMenu = tk.Menu(self.menuButton, tearoff=0)
        self.pageMenu.add_command(label="Personal Area", command=self.openPersonal)
        self.pageMenu.add_command(label="Voting", command=self.openVote)
        self.pageMenu.add_command(label="Log Out", command=self.logOut)
        self.menuButton.configure(menu=self.pageMenu)

        self.pairDrawingButton = tk.Button(self.root, text="PAIR\nDRAWING", command=self.choosePairDraw, bg="#5b18ed", fg="#111111", font=("Arial", 16), borderwidth=0)
        self.pairDrawingButton.place(relx=0.072, rely=0.082, relwidth=0.133, relheight=0.19)

        self.singleDrawingButton = tk.Button(self.root, text="SINGLE\nDRAWING", command=self.chooseOneDraw, bg="#5b18ed", fg="#111111", font=("Arial", 14), borderwidth=0)
        self.singleDrawingButton.place(relx=0.224, rely=0.082, relwidth=0.09, relheight=0.19)

        self.userListArea = ScrollableFrame(self.root, "#777777")
        self.userListArea.place(relx=0.05, rely=0.32, relwidth=0.267, relheight=0.61)

        self.galleryArea = ScrollableFrame(self.root, "#999999")
        self.galleryArea.place(relx=0.34, rely=0.27, relwidth=0.615, relheight=0.66)
        self.galleryFrame = self.galleryArea.content

        self.loadTopics()
        self.loadPictures()
        self.loadUsers()

        self.root.mainloop()

    def loadTopics(self):
        try:
            topics = server_get_data("get_hobbies_users", self.username)
        except Exception:
            topics = []

        if topics is None:
            topics = []

        if isinstance(topics, int):
            categoryNames = ["Animals", "Nature", "Love", "Fantasy", "Food", "Sports", "Music", "Space", "Cities", "Vehicles", "People", "Clothes", "Flowers", "History", "Sea", "Technology"]
            topics = [category for index, category in enumerate(categoryNames) if topics & (1 << index)]

        self.topics = topics if topics else ["Animals", "Nature", "Food", "Sports"]
        self.selectedTopic = tk.StringVar(master=self.root, value=self.topics[0])

        self.topicMenu = tk.OptionMenu(self.root, self.selectedTopic, *self.topics, command=self.photoChanged)
        self.topicMenu.config(font=("Arial", 17), bg="#ff3333", fg="#111111", borderwidth=0)
        self.topicMenu["menu"].config(font=("Arial", 15))
        self.topicMenu.place(relx=0.50, rely=0.17, relwidth=0.275, relheight=0.07)

    def loadPictures(self):
        for widget in self.galleryFrame.winfo_children():
            widget.destroy()

        self.pictureButtons.clear()
        self.pictureImages.clear()
        category = self.selectedTopic.get()

        if category == "No topics selected":
            self.showListMessage(self.galleryFrame, "No topic selected")
            return

        imagesFolder = os.path.join(r"C:\Users\bugom\Downloads\פרויקט גמר 5 יחל מחשבים DRAW TOGETHER\arts", category)
        
        for pictureNumber in range(1, 21):
            matchingFiles = glob.glob(os.path.join(imagesFolder, f"pic{pictureNumber}.*"))

            if matchingFiles:
                try:
                    with Image.open(matchingFiles[0]) as image:
                        image.thumbnail((180, 140))
                        photo = ImageTk.PhotoImage(image.copy(), master=self.root)
                    self.pictureImages.append(photo)

                    button = tk.Button(
                        self.galleryFrame, image=photo,
                        command=lambda num=pictureNumber, cat=category: self.choosePicture(num, cat),
                        bg="#5b18ed", borderwidth=0
                    )
                except Exception:
                    button = tk.Button(
                        self.galleryFrame, text=f"Pic {pictureNumber}",
                        command=lambda num=pictureNumber, cat=category: self.choosePicture(num, cat),
                        bg="#5b18ed", fg="#f5f2ec", font=("Arial", 12), borderwidth=0
                    )
            else:
                button = tk.Button(
                    self.galleryFrame, text=f"{category}\nPic {pictureNumber}",
                    command=lambda num=pictureNumber, cat=category: self.choosePicture(num, cat),
                    bg="#5b18ed", fg="#f5f2ec", font=("Arial", 12), borderwidth=0
                )

            button.grid(row=(pictureNumber - 1) // 4, column=(pictureNumber - 1) % 4, sticky="nsew", padx=12, pady=12)
            self.pictureButtons.append(button)

        for column in range(4):
            self.galleryFrame.grid_columnconfigure(column, weight=1)

    def loadUsers(self):
        for widget in self.userListArea.content.winfo_children():
            widget.destroy()
        try:
            usernames = server_get_data("get_usernames_users", self.username)
        except Exception:
            usernames = []

        if not usernames:
            self.showListMessage(self.userListArea.content, "No other users")
            return

        for selectedUsername in usernames:
            if selectedUsername != self.username:
                userButton = tk.Button(self.userListArea.content, text=selectedUsername, command=lambda name=selectedUsername: self.chat(self.username, name), bg="#078844", fg="#111111", font=("Arial", 14), borderwidth=0)
                userButton.pack(fill=tk.X, padx=12, pady=6)

    def showListMessage(self, parent, text):
        label = tk.Label(parent, text=text, bg="#777777", fg="#f5f2ec", font=("Arial", 14))
        label.pack(fill=tk.X, padx=8, pady=8)

    def photoChanged(self, topic):
        self.loadPictures()

    def choosePicture(self, pictureNumber, cat):
        choiceWindow = tk.Toplevel(self.root)
        choiceWindow.geometry("250x300")
        choiceWindow.title("Choose drawing mode")
        choiceWindow.transient(self.root)

        tk.Button(choiceWindow, text="ציור לבד (Single)", font=("Arial", 14), command=lambda: self.startDrawing(choiceWindow, pictureNumber, cat, 1)).pack(fill=tk.X, padx=15, pady=20, ipady=10)
        tk.Button(choiceWindow, text="ציור ביחד (Pair)", font=("Arial", 14), command=lambda: self.startDrawing(choiceWindow, pictureNumber, cat, 3)).pack(fill=tk.X, padx=15, pady=10, ipady=10)

    def startDrawing(self, choiceWindow, pictureNumber, category, roomNumber):
        choiceWindow.destroy()
        self.closeWindow()
        if roomNumber in (1, 2):
            pageOneDraw(pictureNumber, category, roomNumber, self.username)
        else:
            pageTowDraw(pictureNumber, category, roomNumber, self.username)

    def chat(self, currentUsername, selectedUsername):
        messagebox.showinfo("Chat", f"Opening chat with {selectedUsername}")

    def openPersonal(self):
        self.closeWindow()
        pagePersonal(self.username)

    def openVote(self):
        self.closeWindow()
        pageVote(self.username)

    def logOut(self):
        self.closeWindow()
        pageStart()

    def choosePairDraw(self):
        self.choosePicture(1, "Animals")

    def chooseOneDraw(self):
        self.choosePicture(1, "Animals")


class pagePersonal(standartPage):
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.buttonBack = self.createButton("BACK", self.back, 0.74, 0.018, 0.245, 0.09)
        self.createText("NUMBER OF WINS", 0.055, 0.24, 0.17, 0.30, 16)
        self.createText("NUMBER OF DRAWINGS", 0.055, 0.585, 0.17, 0.30, 16)
        self.root.mainloop()

    def back(self):
        self.closeWindow()
        pageMain(self.username)


class pageVote(standartPage):
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.buttonBack = self.createButton("BACK", self.back, 0.74, 0.018, 0.245, 0.09)
        self.root.mainloop()

    def back(self):
        self.closeWindow()
        pageMain(self.username)


if __name__ == "__main__":
    pageStart()