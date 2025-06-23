import json

class ConfigManager:
    data = {}
    def __init__(self):
        self.load()

    def load(self):
        try:
            with open("config.json", "x"): pass
        except: pass
        with open("config.json", "r+") as config:
            self.data = json.loads(config.read())


    def get_server_name(self):
        return self.data["serverName"]
    
