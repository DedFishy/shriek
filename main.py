import flask
import secrets
from flask_socketio import SocketIO
from userman import UserManager
from configman import ConfigManager
from util import *

userman = UserManager()
configman = ConfigManager()

app = flask.Flask(__name__, static_folder="assets")

app.debug = True

app.config['SECRET_KEY'] = secrets.token_urlsafe()
if app.debug:
    app.config["TEMPLATES_AUTO_RELOAD"] = True

socketio = SocketIO(app)



@app.route("/")
def hello_world():
    return flask.render_template("index.html")

@socketio.on("tryJoin")
def try_join(data):
    response = {}
    name = data["name"]
    sid = get_sid()
    if userman.get_user(name, sid):
        response = construct_error("That name is taken")
    else:
        userman.create_user(name, sid)
        response = {
            "type": "success", 
            "userlist": userman.construct_user_list(), 
            "servername": configman.get_server_name()
            }
    socketio.emit("tryJoinResponse", response, to=get_sid())

    socketio.emit("roomUpdate", construct_room_update(userman))

@socketio.on("sendMessage")
def send_message(data):
    socketio.emit("userMessage", {"content": data["content"], "sender": userman.get_user_guaranteed(sid=get_sid()).serialize()})

@socketio.on('disconnect')
def disconnect(reason):
    print('Client disconnected, reason:', reason)
    userman.remove_user(userman.get_user(sid=get_sid()))

    socketio.emit("roomUpdate", construct_room_update(userman))


if __name__ == "__main__":
    socketio.run(app, "0.0.0.0")