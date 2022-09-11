import numpy as np
import pandas as pd
from datetime import datetime
from scipy.optimize import fsolve
import warnings

warnings.filterwarnings('ignore', 'The iteration is not making good progress')


class cashflows(object):
    '''
    Member variables:
    name : string
    anchor_date: datetime
    df: pandas data frame with columns cashflows (float) and years (float) of the same length and potentially
    something else

    Member functions:
    npv(irr) : Net present value of this cash flow series given a return value
    irr() : IRR of this cash flow
    '''

    def __init__(self, name, anchor_date, cf):
        assert isinstance(cf, pd.DataFrame)
        assert isinstance(anchor_date, datetime)

        self.name = name
        self.anchor_date = anchor_date
        self.df = cf
        if 'years' not in self.df.columns:
            self.df['years'] = (self.df.dates - self.anchor_date) / np.timedelta64(1, 'Y')

        self.df.set_index(['dates', 'years'])

        self.valueColumn = next(iter(list(set(list(self.df.columns.values)).difference(['dates', 'years']))))

    def npv(self, ret):
        #return np.sum(self.df.cashflows.values / (1. + ret) ** self.df.years.values)
        return np.sum(self.df[self.valueColumn].values / (1. + ret) ** self.df.years.values)

    def irr(self):
        return np.asscalar(fsolve(self.npv, x0 = 0.01))
