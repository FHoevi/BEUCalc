import pandas as pd
from Modules.business_module import business_module
from Modules.cashflows import cashflows
import numpy as np


class Reserve_Module(business_module):
    def __init__(self, name, params, predecessors = None):
        business_module.__init__(self, name, params, predecessors)

    def roll_out_cashflows(self):
        business_module.roll_out_cashflows(self)

        remove_cashflows_list = []
        for item in self.predecessors:
            for cashflow in item.cashflows:
                tempCashflow = cashflow
                # tempCashflow.name = cashflow.name + " " + item.name
                self.cashflows.append(tempCashflow)
            if hasattr(item, 'tax_cashflows'):
                for cashflow in item.tax_cashflows:
                    tempCashflow = cashflow
                    # tempCashflow.name = cashflow.name + " " + item.name
                    self.cashflows.append(tempCashflow)
                    remove_cashflows_list.append(tempCashflow)

        totalReserve = self.params.container['Gesetzliche_Rücklage'] + self.params.container['Sonstige_Rücklage']
        self.combined_cashflows()

        reserve = self.combined_cashflow.df[self.combined_cashflow.valueColumn] * -totalReserve
        reserve[0] = 0.0
        df = pd.DataFrame(data={'years': self.combined_cashflow.df.years, 'dates': self.combined_cashflow.df.dates, 'cashflows': reserve})
        tempString = "Rücklage"
        tempCf = cashflows(tempString, self.combined_cashflow.anchor_date, df)
        self.combined_cashflow = None

        for item in remove_cashflows_list:
            self.cashflows.remove(item)

        if self.cashflows and tempString in (o.name for o in self.cashflows):
            cf = next(filter(lambda x: x.name == tempString, self.cashflows))
            cf = tempCf
        else:
            self.cashflows.append(tempCf)

    def update_after_rollout(self, input):
        input['Eigenkapitalrendite nach Steuern + Rücklagen'] = '{:.2%}'.format(round(self.combined_cashflow.irr(), 4))
        tmp_remove_index = self.cashflows.index(
            # next(filter(lambda x: x.name.startswith('Fremdkapital '), self.cashflows)))
            next(filter(lambda x: x.name == 'Fremdkapital', self.cashflows)))
        tmp_remove = self.cashflows.pop(tmp_remove_index)
        self.combined_cashflows()
        input['Gesamtkapitalrendite nach Steuern + Rücklagen'] = '{:.2%}'.format(round(self.combined_cashflow.irr(), 4))
        self.cashflows.append(tmp_remove)
        self.combined_cashflows()
        return input
