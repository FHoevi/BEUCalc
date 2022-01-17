import pandas as pd
from Modules.business_module import business_module
from Modules.cashflows import cashflows
import numpy as np


class Tax_Module(business_module):
    def __init__(self, name, params, predecessors = None):
        business_module.__init__(self, name, params, predecessors)
        self.tax_cashflows = []

    def roll_out_cashflows(self):
        business_module.roll_out_cashflows(self)

        for item in self.predecessors: # look out for items of type "PV_Production_Module"
            # tempPrincipalCashflow = next(filter(lambda x: x.name == "Tilgung Production Module", item.cashflows))
            tempPrincipalCashflow = next(filter(lambda x: x.name == "Tilgung", item.cashflows))
            # tempStringPrincipal = "Tilgung " + item.name
            tempStringPrincipal = "Tilgung "
            temp = tempPrincipalCashflow.df[tempPrincipalCashflow.valueColumn] * -1
            df = pd.DataFrame(data={'years': tempPrincipalCashflow.df.years, 'dates': tempPrincipalCashflow.df.dates, 'cashflows': temp})
            tempCf = cashflows(tempStringPrincipal, tempPrincipalCashflow.anchor_date, df)

            if self.cashflows and tempStringPrincipal in (o.name for o in self.cashflows):
                cf = next(filter(lambda x: x.name == tempStringPrincipal, self.cashflows))
                cf = tempCf
            else:
                self.cashflows.append(tempCf)

            # tempTotalCapitalCashflow = next(filter(lambda x: x.name == "Investitionssumme Production Module", item.cashflows))
            tempTotalCapitalCashflow = next(filter(lambda x: x.name == "Investitionssumme", item.cashflows))
            tempTotalCapital = -tempTotalCapitalCashflow.df.cashflows[0]
            monthlyDepreciation = tempTotalCapital / (self.params.container['AfA'] * 12)
            tempStringDepreciation = "Abschreibung"
            temp = np.zeros(len(tempPrincipalCashflow.df.dates))
            temp[0:int(self.params.container['AfA']) * 12] = -monthlyDepreciation
            df = pd.DataFrame(data = {'years': tempPrincipalCashflow.df.years, 'dates': tempPrincipalCashflow.df.dates, 'cashflows': temp})
            tempCf = cashflows(tempStringDepreciation, tempPrincipalCashflow.anchor_date, df)

            if self.cashflows and tempStringDepreciation in (o.name for o in self.cashflows):
                cf = next(filter(lambda x: x.name == tempStringDepreciation, self.cashflows))
                cf = tempCf
            else:
                self.cashflows.append(tempCf)

            for cashflow in item.cashflows:
                tempCashflow = cashflow
                # tempCashflow.name = cashflow.name + " " + item.name
                self.cashflows.append(tempCashflow)

            self.combined_cashflows()

            profits = self.combined_cashflow.df[self.combined_cashflow.valueColumn]
            taxes = profits * -self.params.container['Steuersatz']
            taxes[0]  = 0.0

            df = pd.DataFrame(data = {'years': self.combined_cashflow.df.years, 'dates': self.combined_cashflow.df.dates, 'cashflows': taxes})
            self.combined_cashflow = None
            tempString = "Steuern"
            tempCf = cashflows(tempString, tempPrincipalCashflow.anchor_date, df)

            if self.cashflows and tempString in (o.name for o in self.cashflows):
                cf = next(filter(lambda x: x.name == tempString, self.cashflows))
                cf = tempCf
            else:
                self.cashflows.append(tempCf)

            temp = next(filter(lambda x: x.name == tempStringPrincipal, self.cashflows))
            self.tax_cashflows.append(temp)
            self.cashflows.remove(temp)
            temp = next(filter(lambda x: x.name == tempStringDepreciation, self.cashflows))
            self.tax_cashflows.append(temp)
            self.cashflows.remove(temp)

    def update_after_rollout(self, input):
        input['Eigenkapitalrendite nach Steuern'] = '{:.2%}'.format(round(self.combined_cashflow.irr(), 4))
        tmp_remove_index = self.cashflows.index(
            # next(filter(lambda x: x.name.startswith('Fremdkapital '), self.cashflows)))
            next(filter(lambda x: x.name == 'Fremdkapital', self.cashflows)))
        tmp_remove = self.cashflows.pop(tmp_remove_index)
        self.combined_cashflows()
        input['Gesamtkapitalrendite nach Steuern'] = '{:.2%}'.format(round(self.combined_cashflow.irr(), 4))
        self.cashflows.append(tmp_remove)
        self.combined_cashflows()
        return input
