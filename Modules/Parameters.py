from Observer.ChangeNotifier import ChangeNotifier


class Parameters(object):
    def __init__(self, **kwargs):
        self.container = {}

        # observable interface
        self.hasChanged = False
        self.changeNotifier = ChangeNotifier(self)
        self.changeNotifier.startNotifying()

        if kwargs is not None:
            for key, value in kwargs.items():
                self.container[key] = value

    def append(self, **kwargs):
        if kwargs is not None:
            for key, value in kwargs.items():
                self.container[key] = value

        self.changeNotifier.notifyObservers()

    def delete(self, **kwargs):
        if kwargs is not None:
            for key in kwargs.items():
                if key in self.container.items():
                    del self.container[key]

    def from_dict(self, d):
        self.container = d

