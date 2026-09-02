class FreeSpacePathLoss:
    def __init__(self):
        pass

class LogShadowing:
    def __init__(self):
        pass


class Underground2AboveGroundLoss:
    def __init__(self):
        self.fspl = FreeSpacePathLoss()
        self.shadowing = LogShadowing()
        
    @property
    def total(self):
        pass
    
    def __str__(self):
        return f"Path loss from Node to Gateway: {self.total}"

class Underground2UndergroundLoss:
    def __init__(self):
        pass

    @property
    def total(self):
        pass

    def __str__(self):
        return f"Path loss from Node to Node: {self.total}"