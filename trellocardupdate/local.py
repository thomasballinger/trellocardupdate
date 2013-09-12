from clint import resources
import json

resources.init('thomasballinger', 'trello-card-updater')

#being used as though they have in-memory caches
class LocalStorage(object):
    def __init__(self, name):
        object.__setattr__(self, 'res', getattr(resources, name))
    def __getattr__(self, att):
        s = self.res.read(att)
        if s is None:
            return None
        data = json.loads(s)
        return data
    def __setattr__(self, att, data):
        s = json.dumps(data)
        self.res.write(att, s)
    def __getitem__(self, key):
        return getattr(self, key)
    def __setitem__(self, key, value):
        setattr(self, key, value)

class LocalObfuscatedStorage(LocalStorage):
    """Of questionable use, but should avoid card names being indexed"""
    def __getattr__(self, att):
        s = self.res.read(att)
        if s is None:
            return None
        data = json.loads(s.encode('rot13'))
        return data
    def __setattr__(self, att, data):
        s = json.dumps(data).encode('rot13')
        self.res.write(att, s)

user = LocalStorage('user')
cache = LocalObfuscatedStorage('cache')
