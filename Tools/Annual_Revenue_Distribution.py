from math import sin, cos, pi
from datetime import datetime

class Rev_Dist(object):
    def __init__(self, a = 0.7, b = 11, stepsize = 0.001):
        self.a = a
        self.b = b
        self.stepsize = stepsize

    def dist(self, x):
        return self.stepsize * (self.a * cos(2 * pi * x + pi + self.b / 365) + 1.0)

    def cum_remainder(self, date):
        td = datetime(date.year, 12, 31) - date
        x = 1 - td.days / 365
        return self.a / (2 * pi) * (sin(3 * pi + self.b / 365) - sin(pi * (2 * x + 1) + self.b / 365)) + 1 - x
