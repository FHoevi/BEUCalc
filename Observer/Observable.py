from Observer.Synchronization import *


class Observable(Synchronization):
    def __init__(self):
        self.observers = []
        self.changed = 0
        Synchronization.__init__(self)

    def addObserver(self, observer):
        if observer not in self.observers:
            self.observers.append(observer)

    def deleteObserver(self, observer):
        self.observers.remove(observer)

    def notifyObservers(self, arg = None):
        '''If 'changed' indicates that this object
        has changed, notify all its observers, then
        call clearChanged(). Each observer has its
        update() called with two arguments: this
        observable object and the generic 'arg'.'''

        self.mutex.acquire()
        try:
            if not self.changed: return
            # Make a local copy in case of synchronous
            # additions of observers:
            localArray = self.observers[:]
            self.clearChanged()
        finally:
            self.mutex.release()
        # Updating is not required to be synchronized:
        for observer in localArray:
            observer.update(self, arg)

    def deleteObservers(self): self.observers = []
    def setChanged(self): self.changed = 1
    def clearChanged(self): self.changed = 0
    def hasChanged(self): return self.changed
    def countObservers(self): return len(self.observers)
