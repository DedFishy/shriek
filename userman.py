class User:
    def __init__(self, name, sid):
        self.name = name
        self.sid = sid

    def serialize(self):
        return {
            "name": self.name,
            "sid": self.sid
        }

class UserManager:
    users: list[User] = []
    voice_excluded_sids: list[tuple] = []
    def __init__(self):
        pass

    def create_user(self, name: str, sid: tuple):
        self.users.append(User(name, sid))
        self.voice_excluded_sids.append(sid)

    def get_user(self, name: str|None=None, sid: tuple|None=None) -> User|None:
        for user in self.users:
            if user.name == name or user.sid == sid:
                return user
        return None
    
    def get_user_guaranteed(self, name: str|None=None, sid: tuple|None=None) -> User:
        user = self.get_user(name, sid)
        if not user:
            raise ValueError("User does not exist")
        return user
    
    def construct_user_list(self) -> list[dict]:
        return [user.serialize() for user in self.users]
    
    def remove_user(self, user: User|None):
        if not user:
            print("Invalid user")
            return
        del self.users[self.users.index(user)]


    def add_to_voice(self, sid: tuple):
        self.voice_excluded_sids.remove(sid)
    
    def remove_from_voice(self, sid: tuple):
        self.voice_excluded_sids.append(sid)