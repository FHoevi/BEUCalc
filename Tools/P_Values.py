from scipy.stats import norm
from math import sqrt


class P_Values(object):
    def __init__(self, **kwargs):
        self.container = {}
        self.sigma = 0.0

        sumvar = 0.0

        if kwargs is not None:
            for key, value in kwargs.items():
                self.container[key] = value
                sumvar += value ** 2
            self.sigma = sqrt(sumvar)

    def p_value_delta(self, p):
        return 1.0 - norm.ppf(p, 1.0, self.sigma)

    def from_dict(self, d):
        self.container = d
        self.sigma = sqrt(sum([value ** 2 for key, value in self.container.items()]))


