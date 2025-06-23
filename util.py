import flask
from userman import UserManager

def get_sid():
    return flask.request.sid # type: ignore

def construct_success(message=None):
    if not message: return {"type": "success"}
    return {"type": "success", "message": message}
def construct_error(message):
    return {"type": "error", "message": message}

def construct_room_update(userman: UserManager):
    return {
        "userlist": userman.construct_user_list()
    }