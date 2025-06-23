class User:
    def __init__(self, name, sid):
        self.name = name
        self.sid = sid
        self.call_participant_id = -1

    def serialize(self):
        return {
            "name": self.name,
            "sid": self.sid,
            "call_participant_id": self.call_participant_id
        }

class UserManager:
    users: list[User] = []
    voice_excluded_sids = []
    def __init__(self):
        pass

    def create_user(self, name, sid):
        self.users.append(User(name, sid))
        self.voice_excluded_sids.append(sid)

    def get_user(self, name=None, sid=None):
        for user in self.users:
            if user.name == name or user.sid == sid:
                return user
        return None
    
    def get_user_guaranteed(self, name=None, sid=None):
        user = self.get_user(name, sid)
        if not user:
            raise ValueError("User does not exist")
        return user
    
    def construct_user_list(self):
        return [user.serialize() for user in self.users]
    
    def remove_user(self, user):
        del self.users[self.users.index(user)]

    def get_next_call_participant_id(self):
        i = 0
        
        while True:
            found = True
            for user in self.users:
                if user.call_participant_id == i:
                    found = False
                    break
            if found: return i
            i+=1

    def add_to_voice(self, sid):
        self.voice_excluded_sids.remove(sid)
    
    def remove_from_voice(self, sid):
        self.voice_excluded_sids.append(sid)