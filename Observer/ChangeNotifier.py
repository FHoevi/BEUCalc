from Observer.Observable import Observable


class ChangeNotifier(Observable):
    def __init__(self, outer):
        Observable.__init__(self)
        self.outer = outer
        self.activeStatus = False

    def notifyObservers(self):
        if self.outer.hasChanged and self.activeStatus:
            self.setChanged()
            Observable.notifyObservers(self)

    def startNotifying(self):
        self.activeStatus = True

    def stopNotifying(self):
        self.activeStatus = False
