import time
import flask
import secrets
from flask_socketio import SocketIO
from userman import UserManager
from configman import ConfigManager
from callman import CallMan
from util import *
import asyncio

userman = UserManager()
configman = ConfigManager()
callman = CallMan()

app = flask.Flask(__name__, static_folder="assets")

app.debug = True

app.config['SECRET_KEY'] = secrets.token_urlsafe()
if app.debug:
    app.config["TEMPLATES_AUTO_RELOAD"] = True

socketio = SocketIO(app)

voice_channels = []

@app.route("/")
def hello_world():
    return flask.render_template("index.html")

@socketio.on("voiceFrame")
def voice_frame(data):
    print("Sending voice frame for ID: " + str(userman.get_user_guaranteed(sid=get_sid()).call_participant_id))
    socketio.emit("userVoiceFrame-" + str(userman.get_user_guaranteed(sid=get_sid()).call_participant_id), data)

@socketio.on("joinVoice")
def join_voice():
    user = userman.get_user_guaranteed(sid=get_sid())
    if user.call_participant_id == -1:
        user.call_participant_id = userman.get_next_call_participant_id()
    userman.add_to_voice(get_sid())
    socketio.emit("constructVoiceChannel", {"participant_id": user.call_participant_id}, skip_sid=userman.voice_excluded_sids)
    for channel in voice_channels:
        socketio.emit("constructVoiceChannel", {"participant_id": channel}, to=get_sid())
    voice_channels.append(user.call_participant_id)

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
    socketio.run(app, "0.0.0.0", ssl_context=('cert.pem', 'key.pem'))