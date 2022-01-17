# Util/Observer.py
# Class support for "observer" pattern.
from Observer.Synchronization import *
from Observer.Observable import Observable

class Observer:
    def update(observable, arg):
        '''Called when the observed object is
        modified. You call an Observable object's
        notifyObservers method to notify all the
        object's observers of the change.'''
        pass

synchronize(Observable, "addObserver deleteObserver deleteObservers " +
            "setChanged clearChanged hasChanged countObservers")

