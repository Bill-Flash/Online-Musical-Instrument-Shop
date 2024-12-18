from time import time
class Cache:
    def __init__(self):
        self.mem={}
        self.time={}
    def set(self,key,data,last):
        self.mem[key] = data
        self.time[key] = time() + last
        return True
    def get(self,key):
        for k in list(self.mem.keys()):
            if self.time[k] < time():
                self.delete(k)
        if key in self.mem.keys():
            return self.mem[key]
        else:
            return None
    def delete(self,key):
        del self.mem[key]
        del self.time[key]
        return True
