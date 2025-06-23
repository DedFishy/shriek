class User:
    def __init__(self, name, sid):
        self.name = name
        self.sid = sid
        self.is_in_call = False

    def serialize(self):
        return {
            "name": self.name,
            "sid": self.sid,
            "is_in_call": self.is_in_call
        }

class UserManager:
    users: list[User] = []
    def __init__(self):
        pass

    def create_user(self, name, sid):
        self.users.append(User(name, sid))

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