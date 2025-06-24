import socket
from PySide6.QtCore import QSize, Qt, Signal, QObject, QRect
from PySide6.QtGui import QPaintEvent, QPainter, QTextOption
from PySide6.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QVBoxLayout, QWidget, QScrollArea, QLineEdit, QStyle, QPushButton, QLabel, QSizePolicy, QFrame, QTextEdit, QStyleOption
import sys
import chars
import json
from threading import Thread
import pyaudio

audio = pyaudio.PyAudio()

import random
username = "skibidi" + str(random.randint(0, 9999))

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

port = 44375
mic_send_port = 44376
audio_recv_port = 44377+5
buffsize = 1024

FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
CHUNK = 512

class MicrophoneStreamer:
    def __init__(self):
        
        
        self.streaming = True

        self.frames = []
    
    def stream_send_loop(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        while self.streaming:
            if len(self.frames) > 0:
                self.socket.sendto(self.frames.pop(0), ("127.0.0.1", mic_send_port))

        self.socket.close()

    def mic_read_loop(self):
        self.stream = audio.open(RATE, CHANNELS, FORMAT, input=True, frames_per_buffer=CHUNK)
        while self.streaming:
            self.frames.append(self.stream.read(CHUNK))

        self.stream.close()

class AudioStreamer:
    def __init__(self):
        
        
        self.streaming = True

        self.frames = []

        self.BUFFER_SIZE = 10
    
    def stream_recv_loop(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(("127.0.0.1", audio_recv_port))
        self.socket.settimeout(1)
        while self.streaming:
            try:
                self.frames.append(self.socket.recv(CHUNK * CHANNELS * 2))
            except TimeoutError:
                print("Audio recv timed out.")
        self.socket.close()

    
    def audio_play_loop(self):
        self.stream = audio.open(RATE, CHANNELS, FORMAT, output=True, frames_per_buffer=CHUNK)
        while self.streaming:
            if len(self.frames) == self.BUFFER_SIZE:
                while self.streaming:
                    if len(self.frames) > 0:
                        self.stream.write(self.frames.pop(0), CHUNK)
        self.stream.close()

class Emitter(QObject):
    new_message_signal = Signal(str, str)
    room_update_signal = Signal(dict)

    def new_message(self, sender, message):
        self.new_message_signal.emit(sender, message)

    def room_update(self, data):
        self.room_update_signal.emit(data)

class MessageContent(QLabel):

    def __init__(self, *args, **kwargs):
        super(MessageContent, self).__init__(*args, **kwargs)  

        self.textalignment = Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWrapAnywhere
        self.isTextLabel = True
        self.align = None
    
    def paintEvent(self, event: QPaintEvent) -> None:
        opt = QStyleOption()
        opt.initFrom(self)
        painter = QPainter(self)

        self.style().drawPrimitive(QStyle.PrimitiveElement.PE_Widget, opt, painter, self)

        self.style().drawItemText(painter, self.rect(),
                                  self.textalignment, self.palette(), True, self.text())


class Window(QMainWindow):
    waiting_for_voice = False

    def __init__(self):
        super().__init__() 

        self.mic_streamer = MicrophoneStreamer()
        self.audio_streamer = AudioStreamer()

        self.setWindowTitle("Shriek")
        self.setGeometry(50, 50, 500, 100)

        self.register_widgets()

        self.connect_sock()
        self.send_data("join", {"username": username})

        self.emitter = Emitter()
        self.emitter.new_message_signal.connect(self.add_message)
        self.emitter.room_update_signal.connect(self.room_update)

        self.user_list_stretch = None

        self.in_call = False

    def start_call_threads(self):
        if self.in_call: return
        self.waiting_for_voice = True
        self.send_data("join_voice", {})
        while self.waiting_for_voice: pass
        self.in_call = True
        self.mic_streamer.streaming = True
        self.audio_streamer.streaming = True
        self.mic_read_thread = Thread(target=self.mic_streamer.mic_read_loop)
        self.stream_send_thread = Thread(target=self.mic_streamer.stream_send_loop)
        self.stream_recv_thread = Thread(target=self.audio_streamer.stream_recv_loop)
        self.audio_play_thread = Thread(target=self.audio_streamer.audio_play_loop)

        self.mic_read_thread.start()
        self.stream_send_thread.start()
        self.stream_recv_thread.start()
        self.audio_play_thread.start()
    
    def end_call_threads(self):
        
        if not self.in_call: return
        self.waiting_for_voice = True
        self.send_data("leave_voice", {})
        while self.waiting_for_voice: pass
        self.in_call = False
        self.mic_streamer.streaming = False
        self.audio_streamer.streaming = False
        print("joining mic")
        self.mic_read_thread.join()
        print("joining stream send")
        self.stream_send_thread.join()
        print("joining stream recieve")
        self.stream_recv_thread.join()
        print("joining audio play")
        self.audio_play_thread.join()

    def handle_message(self, data: dict):
        print(data)
        name = data["type"]
        if name == "user_message":
            self.emitter.new_message(data["from"], data["message"])
        elif name == "room_update":
            self.emitter.room_update(data)
        elif name in ["joined_voice", "left_voice"]:
            self.waiting_for_voice = False

    def server_thread(self):
        while True:
            disconnected = False
            got_to_end = False
            data = b""
            while not got_to_end:
                print("RECV")
                message = sock.recv(buffsize)

                print(message)
                data += message

                if not message: 
                    disconnected = True
                    break

                if data.endswith(chars.END): got_to_end = True
            
            data = data.removesuffix(chars.END)
            print("server says", data)
            
            if disconnected: break

            self.handle_message(json.loads(data))
            
        sock.close()

    
    def connect_sock(self):
        sock.connect(("127.0.0.1", port))
        self.socket_thread = Thread(target=self.server_thread)
        self.socket_thread.start()

    def send_message(self):
        message = self.message_typing_box.text()
        self.message_typing_box.setText("")
        self.send_data("send_message", {
            "message": message
        })

    def send_data(self, name, data: dict):
        data["type"] = name
        data_text = json.dumps(data).encode("utf-8") + chars.END
        sock.send(data_text)
    
    def register_widgets(self):
        self.main_layout = QHBoxLayout()

        # Left side of the screen
        self.message_view_layout = QVBoxLayout()
        
        ## Message list
        self.message_list_widget = QTextEdit()
        self.message_list_widget.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.message_list_widget.setWordWrapMode(QTextOption.WrapMode.WrapAnywhere)
        self.message_list_widget.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.message_list_widget.setReadOnly(True)

        self.message_list_widget.insertPlainText("Welcome to the chat room.")
        

        ## Typing area
        self.message_typing_container_layout = QHBoxLayout()
        self.message_typing_box = QLineEdit(placeholderText="Message...")
        self.message_typing_box.returnPressed.connect(self.send_message)
        self.message_send_button = QPushButton("Send")
        self.message_send_button.clicked.connect(self.send_message)
        self.message_typing_container_layout.addWidget(self.message_typing_box)
        self.message_typing_container_layout.addWidget(self.message_send_button)
        
        ### Add to left side of the screen
        self.message_view_layout.addWidget(self.message_list_widget, 1)
        self.message_view_layout.addLayout(self.message_typing_container_layout)

        # Right side of the screen
        self.user_list_container_layout = QVBoxLayout()

        ## Phone call indicator
        self.call_indicator_layout = QHBoxLayout()
        self.toggle_call_button = QPushButton("Join Call")
        self.toggle_call_button.clicked.connect(self.toggle_call)
        self.call_indicator_layout.addWidget(self.toggle_call_button)
        self.user_list_container_layout.addLayout(self.call_indicator_layout)

        ### User list
        self.user_list_scroll = QScrollArea()
        self.user_list_scroll.horizontalScrollBar().setVisible(False)
        self.user_list_layout = QVBoxLayout()
        
        self.user_list_widget = QWidget()
        self.user_list_scroll.setWidget(self.user_list_widget)
        self.user_list_scroll.setWidgetResizable(True)
        self.user_list_widget.setLayout(self.user_list_layout)
        self.user_list_container_layout.addWidget(self.user_list_scroll, 1)

        # Add sublayouts
        self.main_layout.addLayout(self.message_view_layout)
        self.main_layout.addLayout(self.user_list_container_layout)

        self.main_widget = QWidget()
        self.main_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.main_widget)
    
    def toggle_call(self):
        if not self.in_call:
            self.toggle_call_button.setText("Leave Call")
            self.toggle_call_button.setEnabled(False)
            self.start_call_threads()
            self.toggle_call_button.setEnabled(True)
        else:
            self.toggle_call_button.setText("Join Call")
            self.toggle_call_button.setEnabled(False)
            self.end_call_threads()
            self.toggle_call_button.setEnabled(True)

    def remove_users(self):
        print("REMOVING ALL USERS")
        for user_list_widget in self.user_list_layout.children():
            print(user_list_widget)
            user_list_widget.deleteLater()

    def add_user(self, name):
        if self.user_list_stretch != None:
            self.user_list_layout.removeItem(self.user_list_stretch)
        
        user_widget = QLabel(name)
        user_widget.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.user_list_layout.addWidget(user_widget)
        self.user_list_layout.addStretch(1)

    def add_message(self, sender, message):
        self.message_list_widget.insertHtml("<br><strong>" + sender + "</strong> ")
        self.message_list_widget.setAutoFormatting(QTextEdit.AutoFormattingFlag.AutoAll)
        self.message_list_widget.insertPlainText(message)
        self.message_list_widget.verticalScrollBar().setValue(self.message_list_widget.maximumHeight())

    def room_update(self, data):
        print(data)
        self.remove_users()
        for user in data["user_list"]:
            self.add_user(user["name"])

app = QApplication(sys.argv)
window = Window()
window.show()
app.exec()
window.end_call_threads()
sock.shutdown(socket.SHUT_RDWR)
window.socket_thread.join()
sock.close()