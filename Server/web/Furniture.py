class Furniture(object):
    def __init__(self):
        self.state = ""


class Light(Furniture):
    def __int__(self):
        self.name = "light"
        self.state = False

    def getState(self):
        return self.state

    def changeState(self):
        self.state = not self.state
