import pandas as pd
from Modules.business_module import business_module
from Modules.cashflows import cashflows
import numpy as np

pd.options.mode.chained_assignment = None  # default='warn'

class PV_Sales_Module(business_module):
    def __init__(self, name, params, predecessors = None):
        business_module.__init__(self, name, params, predecessors)

        for item in self.predecessors:
            if hasattr(item, "electricity"):
                if not hasattr(self, "electricity"):
                    self.electricity = item.electricity
                else:
                    self.electricity = pd.merge(self.electricity, item.electricity, on = ['dates'], how = 'outer').set_index(['dates']).sum(axis = 1).reset_index()
                    self.electricity.columns = ['dates', 'electricity']

        self.calcDirectConsumptionDegree()

    def roll_out_cashflows(self):
        business_module.roll_out_cashflows(self)

        if self.predecessors:
            for item in self.predecessors:
                # tempProdCashflow = next(filter(lambda x: x.name == "Produktion", item.cashflows))
                # # tempString = "Produktion " + item.name
                # tempString = item.name + " Offset"
                # temp = tempProdCashflow.df[tempProdCashflow.valueColumn] * -1
                # df = pd.DataFrame(data = {'years': tempProdCashflow.df.years, 'dates': tempProdCashflow.df.dates, 'cashflows': temp})
                # tempCf = cashflows(tempString, tempProdCashflow.anchor_date, df)
                #
                # if self.cashflows and tempString in (o.name for o in self.cashflows):
                #     cf = next(filter(lambda x: x.name == tempString, self.cashflows))
                #     cf = tempCf
                # else:
                #     self.cashflows.append(tempCf)

                for cashflow in item.cashflows:
                    tempCashflow = cashflow
                    # tempCashflow.name = cashflow.name + " " + item.name
                    self.cashflows.append(tempCashflow)

        # self.calcInvestmentCashflows()
        self.calcDirectConsumptionCashflow()
        self.calcFeedInCashflow()
        self.calcCostsRelativeToRevenues()

    def calcDirectConsumptionDegree(self):
        annual_consumption = self.params.container["StromverbrauchPA"]
        annual_electricity = self.params.container['Teilnahmequote_Mieterstrom'] * self.params.container['kWp'] * self.params.container['kWh_kWp']
        degree = annual_consumption / annual_electricity
        self.DVQ = self.params.container["DVQ"].spline(degree)

    def calcInvestmentCashflows(self):
        for item in self.predecessors:
            for cf in item.cashflows:
                if cf.name in ["Investitionssumme", "Fremdkapital", "Ablösewert"]:
                    self.cashflows.append(cf)

    def calcDirectConsumptionCashflow(self):
        revenues = pd.DataFrame(data = {'revenues': self.electricity.electricity, 'dates': self.electricity.dates})
        revenues.revenues = \
            revenues.revenues * self.DVQ *\
            (self.params.container['LetztverbraucherEntgelt'] - self.params.container['production_price_kWh'])
        revenues.revenues[revenues.dates <= self.params.container['Start_Direktverbrauch']] = 0.0
        self.cashflows.append(cashflows("Direktverbrauch", self.params.container['Inbetriebnahmedatum'], revenues))

    def calcFeedInCashflow(self):
        revenues = pd.DataFrame(data = {'revenues': self.electricity.electricity, 'dates': self.electricity.dates})
        tmp = pd.DataFrame(data = {'revenues': self.electricity.electricity, 'dates': self.electricity.dates}).revenues
        revenues.revenues =\
            revenues.revenues *\
            (self.params.container['EEG_EinspeiseTarif'] - self.params.container['production_price_kWh'])
        revenues.revenues[revenues.dates >= self.params.container['Start_Direktverbrauch']] = \
            revenues.revenues[revenues.dates >= self.params.container['Start_Direktverbrauch']] * \
            (1 - self.DVQ)
        revenues.revenues[revenues.dates < self.params.container['Start_Einspeisung']] = \
            self.electricity.electricity[self.electricity.dates < self.params.container['Start_Einspeisung']] * \
            (-self.params.container['production_price_kWh'])
        self.cashflows.append(cashflows("Einspeisung", self.params.container['Inbetriebnahmedatum'], revenues))

    def calcCostsRelativeToRevenues(self):
        # prodCashflow = next(item for item in self.cashflows if item.name == "Produktion Production Module") #self.predecessors[0].name
        prodCashflow = next(item for item in self.cashflows if item.name == "Produktion")
        dates = prodCashflow.df.dates

        # DVCashFlow = next(item for item in self.cashflows if item.name == "Direktverbrauch")
        # FeedInCashFlow = next(item for item in self.cashflows if item.name == "Einspeisung")
        # dates = DVCashFlow.df.dates

        tempCosts = 0.0
        keys = self.params.container.keys()
        for item in keys:
            if item in ['Reparaturrückstellungen', 'Pachtkosten']:
                tempCosts -= self.params.container[item]

        # tempDf = prodCashflow.df[prodCashflow.valueColumn]
        tempDf = 0.0
        # tempDf = DVCashFlow.df[DVCashFlow.valueColumn] + FeedInCashFlow.df[FeedInCashFlow.valueColumn]
        for cashflow in self.cashflows:
            if cashflow.name in ['Direktverbrauch', 'Einspeisung']:
                tempDf = tempDf + cashflow.df[cashflow.valueColumn]

        tempCosts *= tempDf

        inflfactors = np.array([1 + self.params.container['Inflation']] * len(dates)) ** np.array((dates - self.cashflows[0].anchor_date) / np.timedelta64(1, 'Y'))

        costsRelativeToRevenues = pd.DataFrame(data = {'costs': tempCosts * inflfactors, 'dates': dates})

        self.cashflows.append(cashflows("Kosten abhängig von Erlösen" + " " + self.name, self.params.container['Inbetriebnahmedatum'], costsRelativeToRevenues))
        # self.cashflows.append(cashflows("Kosten abhängig von Erlösen", self.params.container['Inbetriebnahmedatum'], costsRelativeToRevenues))

    def update_after_rollout(self, input):
        input['Eigenkapitalrendite vor Steuern'] = '{:.2%}'.format(round(self.combined_cashflow.irr(), 4))
        tmp_remove_index = self.cashflows.index(
            # next(filter(lambda x: x.name.startswith('Fremdkapital '), self.cashflows)))
            next(filter(lambda x: x.name == 'Fremdkapital', self.cashflows)))
        tmp_remove = self.cashflows.pop(tmp_remove_index)
        self.combined_cashflows()
        input['Gesamtkapitalrendite vor Steuern'] = '{:.2%}'.format(round(self.combined_cashflow.irr(), 4))
        self.cashflows.append(tmp_remove)
        self.combined_cashflows()
        return input




