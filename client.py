import socket
import sys

from PySide6.QtCore import (
    Qt,
    Signal,
    QObject
)
from PySide6.QtGui import (
    QTextOption,
    QIcon,
    QPixmap
)
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QHBoxLayout,
    QDialog,
    QVBoxLayout,
    QWidget,
    QLineEdit,
    QPushButton,
    QLabel,
    QSizePolicy,
    QTextEdit,
)
import json
from threading import Thread
import markdown
import html

END = "␃".encode("utf-8")

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

port = 44375
buffsize = 1024

class Emitter(QObject):
    new_message_signal = Signal(str, str)
    room_update_signal = Signal(dict)

    def new_message(self, sender: str, message: str):
        self.new_message_signal.emit(sender, message)

    def room_update(self, data: dict):
        self.room_update_signal.emit(data)

class Window(QMainWindow):
    waiting_for_voice: bool = False
    socket_thread = None
    is_connected = False

    def __init__(self):
        super().__init__() 

        # Setup window
        self.setWindowIcon(QIcon("icon.png"))
        self.setGeometry(50, 50, 500, 100)

        # Create widgets
        self.register_widgets()

        
        

        # Setup Qt Emitters (for multithreading)
        self.emitter = Emitter()
        self.emitter.new_message_signal.connect(self.add_message)
        self.emitter.room_update_signal.connect(self.room_update)

        self.hide()

        # Start up socket
        self.connect_sock()

        # Setup window title
        self.setWindowTitle("Shriek - Connected to " + self.ip_input.text() + " as " + self.name_input.text())

        if not self.is_connected: sys.exit(0)

    def handle_message(self, data: dict):
        name = data["type"] # What type of message this is
        if name == "user_message":
            self.emitter.new_message(data["from"], data["message"])
        elif name == "system_message":
            self.emitter.new_message("System", data["message"])
        elif name == "room_update":
            self.emitter.room_update(data)
        elif name == "join_deny":
            print("Denied!")
            self.connection_error.setText(data["message"])
        elif name == "join_accept":
            self.connection_dialog.hide()

    def server_thread(self):
        while True:
            disconnected = False
            got_to_end = False
            data = b""
            # While data is still available
            
            while not got_to_end:
                message = sock.recv(buffsize)
                data += message

                if not message: # Connection has closed
                    disconnected = True
                    break

                if data.endswith(END): got_to_end = True
            
            data = data.removesuffix(END)
            if disconnected: break
            self.handle_message(json.loads(data))
        
        sock.close()
    
    def connect_sock(self):
        # Setup dialog
        self.connection_dialog = QDialog()
        self.connection_dialog.setWindowTitle("Connect to Server")
        self.connection_dialog.setWindowIcon(QIcon("icon.png"))

        connection_dialog_layout = QVBoxLayout()
        connection_dialog_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Setup title image
        connection_dialog_image = QLabel()
        connection_dialog_image.setPixmap(QPixmap("icon.png"))
        connection_dialog_layout.addWidget(connection_dialog_image, alignment=Qt.AlignmentFlag.AlignCenter)

        # Setup instructions
        connection_dialog_layout.addWidget(QLabel("Put in the information to connect to a server"))

        # Setup error message label
        self.connection_error = QLabel("")

        connection_dialog_layout.addWidget(self.connection_error)
        
        # Setup inputs
        self.ip_input = QLineEdit(placeholderText="IP Address", text="iamdying.boyne.dev")
        self.port_input = QLineEdit(text="44375", placeholderText="Port")
        self.name_input = QLineEdit(placeholderText="Username", text="Michael")
        self.connect_sock_button = QPushButton("Connect")
        self.connect_sock_button.clicked.connect(self.connect_sock_callback)

        connection_dialog_layout.addWidget(self.ip_input)
        connection_dialog_layout.addWidget(self.port_input)
        connection_dialog_layout.addWidget(self.name_input)
        connection_dialog_layout.addWidget(self.connect_sock_button)

        # Register layout
        self.connection_dialog.setLayout(connection_dialog_layout)

        # Setup and start view
        self.connection_dialog.setFixedSize(300, 275)
        self.connection_dialog.exec()
    
    def connect_sock_callback(self):
        try:
            # Validate input
            if len(self.name_input.text()) < 3:
                raise Exception("Username too short")
            
            if not self.is_connected:
            
            
                # Connect to server
                sock.connect((self.ip_input.text(), int(self.port_input.text())))

            

                # Start server thread
                self.socket_thread = Thread(target=self.server_thread)
                self.socket_thread.start()
                self.is_connected = True
            self.send_data("join", {"username": self.name_input.text()})

    

        except Exception as e:
            self.connection_error.setText(str(e))

    def send_message(self):
        message = self.message_typing_box.text()
        self.message_typing_box.setText("")
        self.send_data("send_message", {
            "message": message
        })

    def send_data(self, name: str, data: dict):
        data["type"] = name
        data_text = json.dumps(data).encode("utf-8") + END
        try:
            sock.send(data_text)
        except BrokenPipeError:
            raise SystemExit()
    
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
        self.user_list = QTextEdit()
        self.user_list.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)

        # Add sublayouts
        self.main_layout.addLayout(self.message_view_layout)
        self.main_layout.addWidget(self.user_list)

        # Main Widget!
        self.main_widget = QWidget()
        self.main_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.main_widget)

    def remove_users(self):
        self.user_list.setText("<strong>Connected Users:</strong>")

    def add_user(self, name: str):
        self.user_list.append(name)

    def add_message(self, sender: str, message: str):
        self.message_list_widget.insertHtml("<br><strong>" + sender + "</strong> ")
        self.message_list_widget.setAutoFormatting(QTextEdit.AutoFormattingFlag.AutoAll)
        self.message_list_widget.insertHtml(markdown.markdown(html.escape(message)))
        self.message_list_widget.verticalScrollBar().setValue(self.message_list_widget.maximumHeight())

    def room_update(self, data: dict):
        self.remove_users()
        for user in data["user_list"]:
            self.add_user(user["name"])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    app.exec()
    sock.shutdown(socket.SHUT_RDWR)
    if window.socket_thread: window.socket_thread.join()
    sock.close()