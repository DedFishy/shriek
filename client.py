import socket
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QVBoxLayout, QWidget, QScrollArea, QLineEdit, QPushButton, QLabel
import sys
import chars
import json

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

port = 44375

buffsize = 1024

class Window(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Shriek")

        self.register_widgets()

        self.connect_sock()
    
    def connect_sock(self):
        sock.connect(("127.0.0.1", port))

    def send_message(self):
        message = self.message_typing_box.text()
        self.message_typing_box.setText("")
        self.send_data({
            "message": message
        })

    def send_data(self, data: dict):
        data_text = json.dumps(data).encode("utf-8") + chars.END
        sock.send(data_text)
    
    def register_widgets(self):
        self.main_layout = QHBoxLayout()

        # Left side of the screen
        self.message_view_layout = QVBoxLayout()
        
        ## Message list
        self.message_list_scroll_area = QScrollArea()
        self.message_list_layout = QVBoxLayout()
        self.message_list_widget = QWidget()
        self.message_list_widget.setLayout(self.message_list_layout)
        self.message_list_scroll_area.setWidget(self.message_list_widget)

        ## Typing area
        self.message_typing_container_layout = QHBoxLayout()
        self.message_typing_box = QLineEdit(placeholderText="Message...")
        self.message_typing_box.returnPressed.connect(self.send_message)
        self.message_send_button = QPushButton("Send")
        self.message_send_button.clicked.connect(self.send_message)
        self.message_typing_container_layout.addWidget(self.message_typing_box)
        self.message_typing_container_layout.addWidget(self.message_send_button)
        
        ### Add to left side of the screen
        self.message_view_layout.addWidget(self.message_list_widget)
        self.message_view_layout.addLayout(self.message_typing_container_layout)

        # Right side of the screen
        self.user_list_container_layout = QVBoxLayout()

        ## Phone call indicator
        self.call_indicator_layout = QHBoxLayout()
        self.toggle_call_button = QPushButton("Join Call")
        self.indicator_text = QLabel("Not connected")
        self.call_indicator_layout.addWidget(self.toggle_call_button)
        self.call_indicator_layout.addWidget(self.indicator_text)
        self.user_list_container_layout.addLayout(self.call_indicator_layout)

        ### User list
        self.user_list_layout = QVBoxLayout()
        self.user_list_container_layout.addLayout(self.user_list_layout, 1)

        # Add sublayouts
        self.main_layout.addLayout(self.message_view_layout)
        self.main_layout.addLayout(self.user_list_container_layout)

        self.main_widget = QWidget()
        self.main_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.main_widget)

    def remove_users(self):
        for user_list_widget in self.user_list_layout.children():
            user_list_widget.deleteLater()

    def add_user(self, name):
        user_widget = QLabel(name)
        self.user_list_layout.addWidget(user_widget)

app = QApplication(sys.argv)
window = Window()
window.show()
app.exec()

sock.close()