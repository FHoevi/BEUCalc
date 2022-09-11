from scipy import interpolate


class DVQ(object):
    def __init__(self, x, y):
        self.tck = interpolate.splrep(x, y, s = 0)

    def spline(self, x):
        return interpolate.splev(x, self.tck, der = 0)

    def spline_deck(self, x):
        return DVQ.spline(self, x) * x