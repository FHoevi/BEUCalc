import pandas as pd
from Modules.cashflows import cashflows
from Observer.Observer import Observer
from Observer.ChangeNotifier import ChangeNotifier
from Modules.Parameters import Parameters
from datetime import datetime
from calendar import isleap
import numpy as np
import abc

class business_module(abc.ABC, object):
    __metaclass__ = abc.ABCMeta

    '''
    Member variables:
    name : string
    cashflows: list of cashflows
    combined_cashflow: cashflows as a union of all items from cash_flows

    Member functions:
    combined_cashflows() : add up cashflows, skip offsetting cash flows
    '''

    class ChangeObserver(Observer):
        def __init__(self, outer):
            self.outer = outer

        def update(self, observable, arg):
            self.outer.roll_out_cashflows()
            self.outer.combined_cashflows()

    def __init__(self, name, params, predecessors = None):
        assert isinstance(params, Parameters)
        self.params = params
        # observable interface
        self.hasChanged = False
        self.changeNotifier = ChangeNotifier(self)
        self.changeNotifier.startNotifying()

        # observer interface
        self.changeObserver = business_module.ChangeObserver(self)
        params.changeNotifier.addObserver(self.changeObserver)

        if predecessors:
            self.predecessors = predecessors
            for item in self.predecessors:
                item.changeNotifier.addObserver(self.changeObserver)

        self.name = name
        self.cashflows = []
        self.combined_cashflow = None

    def roll_out_cashflows(self):
        self.cashflows = []

    def combined_cashflows(self):
        dfs = []
        temp = pd.DataFrame(data = {'years' : [], 'dates' : [], 'cashflows' : []})
        for item in self.cashflows:
            dfs.append(item.df)
            temp = pd.merge(temp, item.df, on = ['years', 'dates'], how = 'outer').set_index(['years', 'dates'])\
                .sum(axis = 1).reset_index()
            temp.columns = ['years', 'dates', 'cashflows']

        temp = temp[temp.cashflows != 0]
        self.combined_cashflow = cashflows("Combined Cashflows", self.cashflows[0].anchor_date,
                                           temp.sort_values('dates').reset_index(drop = True))

    @abc.abstractmethod
    def update_after_rollout(self, input):
        pass

    def yearfraction(self, date):
        td = datetime(date.year, 12, 31) - date
        daysInYear = isleap(date.year) and 366 or 365
        return td.days / daysInYear

    def get_cashflow_dataframe(self):
        result = pd.DataFrame(data={'dates': [], 'years': [], 'dummy': []})
        result.set_index(['dates', 'years'])

        for cashflow in self.cashflows:
            columnName = cashflow.df[cashflow.valueColumn].name
            cashflow.df.rename(columns = {cashflow.valueColumn: cashflow.name}, inplace = True)
            result = pd.merge(result, cashflow.df, how = 'outer', on = ['dates', 'years'], sort = True).fillna(0)
            cashflow.df.rename(columns = {cashflow.name: cashflow.valueColumn}, inplace = True)

        result = result.drop(['dummy'], axis = 1)
        cols = result.columns.tolist()
        ind = cols.index('dates')
        cols = [ind] + list(set([i for i in range(len(cols))]).difference([ind]))
        return result[result.columns[cols]]

    def getInflationFactors(self, dates):
        return np.array([1 + self.params.container['Inflation']] * len(dates)) ** np.array((dates - self.cashflows[0].anchor_date) / np.timedelta64(1, 'Y'))
