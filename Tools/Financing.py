class Financing(object):
    def __init__(self, r1, t1, r2, t2):
        self.r1 = r1
        self.r2 = r2
        self.t1 = t1
        self.t2 = t2

        q1m = (1 + self.r1 / 12)
        q2m = (1 + self.r2 / 12)
        self.monthlyAnnuityFactor = (1 - q1m ** (-self.t1)) / (self.r1 / 12)\
                             + q1m** (-self.t1)\
                             * (1 - q2m ** (self.t1 - self.t2)) / (self.r2 / 12)

        q1q = (1 + self.r1 / 4)
        q2q = (1 + self.r2 / 4)
        self.quarterlyAnnuityFactor = (1 - q1q ** (-self.t1)) / (self.r1 / 4)\
                             + q1q** (-self.t1)\
                             * (1 - q2q ** (self.t1 - self.t2)) / (self.r2 / 4)

        q1 = (1 + self.r1)
        q2 = (1 + self.r2)
        self.annualAnnuityFactor = (1 - q1 ** (-self.t1)) / self.r1\
                             + q1** (-self.t1)\
                             * (1 - q2 ** (self.t1 - self.t2)) / self.r2

    def annuityFactor(self, freq):
        if freq == 'M':
            result = self.monthlyAnnuityFactor
        elif freq == 'A':
            result = self.annualAnnuityFactor
        elif freq == 'Q':
            result = self.quarterlyAnnuityFactor
        return result
