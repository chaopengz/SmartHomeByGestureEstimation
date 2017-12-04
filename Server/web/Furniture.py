class Furniture(object):
    def __init__(self):
        self.state = ""


class Light(Furniture):
    def __init__(self):
        self.name = "light"
        self.state = False

    def getState(self):
        return self.state

    def changeState(self):
        self.state = not self.state


class Soft(Furniture):
    def __init__(self):
        self.name = "soft"
        self.state = False

    def getState(self):
        return self.state

    def changeState(self):
        self.state = not self.state


class TV(Furniture):
    def __init__(self):
        self.name = "tv"
        self.state = False

    def getState(self):
        return self.state

    def changeState(self):
        self.state = not self.state
