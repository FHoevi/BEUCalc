import pandas as pd
from Modules.business_module import business_module
from Modules.cashflows import cashflows
import datetime as dt
# import numpy as np
# from scipy.optimize import fsolve

class PV_Production_Module(business_module):
    def __init__(self, name, params, predecessors):
        business_module.__init__(self, name, params)
        # assert 'dummy_key' in params.container

    def get_last_day_of_month(self, date):
        if date.month == 12:
            return date.replace(day = 31)
        return date.replace(month = date.month + 1) - dt.timedelta(days = 1)

    def roll_out_cashflows(self):
        self.cashflows = []
        self.calcEquityAndDebt()
        if self.debt > 0.0:
            self.calcInitialDebtCashflow()
            self.calcFinancing()
        self.calcInitialInvestmentCashflow()
        self.calcTerminalCashflow()
        self.calcElectricityProductionCashflow()
        self.calcFixAmountPerAnnumCashflow()
        self.calcFixAmountPerAnnumPerkWpCashflow()
        self.calcCostsRelativeToRevenues()

    def calcEquityAndDebt(self):
        self.capital = self.params.container['Investitionssumme'] + self.params.container['ZusatzkostenVerteilnetzbetreiber'] + \
             self.params.container['BaulicheInvestitionen'] + self.params.container['ITInfrastruktur'] + \
             self.params.container['Messkonzept'] + self.params.container['PersonalKosten'] + self.params.container['SonstigeKosten'] + \
             self.params.container['PauschaleUnvorhergesehenes']

        if self.params.container['EigenkapitalAnteil'] < 1.0:
            self.equity = self.params.container['EigenkapitalAnteil'] * self.capital
            self.debt = (1 - self.params.container['EigenkapitalAnteil']) * self.capital
        else:
            self.equity = self.capital
            self.debt = 0.0

    def calcFinancing(self):
        factor = 0
        if self.params.container["Zinsfrequenz"] == 'M':
            # periods = 13 - self.params.container['Tilgungsbeginn'].month + self.params.container['AfA'] * 12
            periods = self.params.container['AfA'] * 12
            factor = 12
        elif self.params.container["Zinsfrequenz"] == 'A':
            periods = 1 + self.params.container['AfA']
            factor = 1
        elif self.params.container["Zinsfrequenz"] == 'Q':
            # periods = ceil((13 - self.params.container['Tilgungsbeginn'].month) / 12) + self.params.container['AfA'] * 4
            periods = self.params.container['AfA'] * 4
            factor = 4

        tilgungsStart = self.get_last_day_of_month(self.params.container['Tilgungsbeginn'])
        interestStart = self.get_last_day_of_month(self.params.container['Inbetriebnahmedatum'])

        dates = pd.date_range(start=tilgungsStart, end=None, periods=periods, freq=self.params.container["Zinsfrequenz"])
        interestDates = pd.date_range(start=interestStart, end=dates[-1], periods=None, freq=self.params.container["Zinsfrequenz"])
        outstandingDebt = [self.debt] * len(interestDates)

        interest = [None] * len(interestDates)
        principal = [None] * len(interestDates)

        tempDateRange = pd.date_range(start=tilgungsStart, end=None,
                                      periods=self.params.container["Annuität"].t1,
                                      freq=self.params.container["Zinsfrequenz"])
        changeDate = tempDateRange[-1].to_pydatetime()

        if self.params.container["Finanzierung"] == 'Annuität':
            annuityFactor = self.params.container["Annuität"].annuityFactor(freq=self.params.container["Zinsfrequenz"])
            payment = self.debt / annuityFactor

            df = pd.DataFrame(data = {'dates': interestDates, 'outstandingDebt': outstandingDebt, 'interest': interest, 'principal': principal})
            indexStartPrincipalPayments = df.index[df.dates == tilgungsStart]

            df.loc[df.dates < tilgungsStart, 'principal'] = 0.0
            df.loc[df.dates <= tilgungsStart, 'interest'] = df.loc[df.dates <= tilgungsStart, 'outstandingDebt'] * self.params.container["Annuität"].r1 / factor
            df.loc[indexStartPrincipalPayments, 'principal'] = payment - df.loc[indexStartPrincipalPayments, 'interest']

            for i in range(indexStartPrincipalPayments[0] + 1, len(df)):
                df.loc[i, 'outstandingDebt'] = df.loc[i - 1, 'outstandingDebt'] - df.loc[i - 1, 'principal']
                if df.loc[i, 'dates'] <= changeDate:
                    df.loc[i, 'interest'] = df.loc[i, 'outstandingDebt'] * self.params.container["Annuität"].r1 / factor
                else:
                    df.loc[i, 'interest'] = df.loc[i, 'outstandingDebt'] * self.params.container["Annuität"].r2 / factor

                if df.loc[i, 'outstandingDebt'] > 0:
                    df.loc[i, 'principal'] = min(payment - df.loc[i, 'interest'], df.loc[i, 'outstandingDebt'])
                else:
                    df.loc[i, 'principal'] = 0.0

        elif self.params.container["Finanzierung"] == 'Tilgung':
            df = pd.DataFrame(data = {'dates': dates, 'outstandingDebt': outstandingDebt, 'interest': interest, 'principal': principal})
            df.loc[:, 'principal'] = df.loc[:, 'outstandingDebt'] / periods
            for i in range(1, len(df)):
                df.loc[i, 'outstandingDebt'] = max(0.0, df.loc[i - 1, 'outstandingDebt'] - df.loc[i - 1, 'principal'])
                if df.loc[i, 'outstandingDebt'] > 0:
                    if df.loc[i, 'dates'] <= changeDate:
                        df.loc[i, 'interest'] = df.loc[i, 'outstandingDebt'] * self.params.container['Annuität'].r1 / factor
                    else:
                        df.loc[i, 'interest'] = df.loc[i, 'outstandingDebt'] * self.params.container['Annuität'].r2 / factor
                    df.loc[i, 'principal'] = min(df.loc[i, 'outstandingDebt'], df.loc[i, 'principal'])

        interestDf = df[['dates', 'interest']].copy()
        interestDf.loc[:, 'interest'] *= -1
        self.cashflows.append(cashflows("Zinsen", self.params.container['Inbetriebnahmedatum'], interestDf))
        principalDf = df[['dates', 'principal']].copy()
        principalDf.loc[:, 'principal'] *= -1
        self.cashflows.append(cashflows("Tilgung", self.params.container['Inbetriebnahmedatum'], principalDf))

    def calcInitialDebtCashflow(self):
        df = pd.DataFrame(data = {'cashflows': [self.debt], 'dates': pd.date_range(start = self.params.container['Inbetriebnahmedatum'],
                                                                            end = self.params.container['Inbetriebnahmedatum'])})
        self.cashflows.append(cashflows("Fremdkapital", self.params.container['Inbetriebnahmedatum'], df))

    def calcInitialInvestmentCashflow(self):
        df = pd.DataFrame(data = {'cashflows': [-self.capital], 'dates': pd.date_range(start = self.params.container['Inbetriebnahmedatum'],
                                                                            end = self.params.container['Inbetriebnahmedatum'])})
        self.cashflows.append(cashflows("Investitionssumme", self.params.container['Inbetriebnahmedatum'], df))

    def calcTerminalCashflow(self):
        if self.params.container['Abloesewert'] > 0.0:
            tempDate = pd.datetime(self.params.container['Inbetriebnahmedatum'].year + self.params.container['AfA'], 12, 31)
            df = pd.DataFrame(data = {'cashflows': [self.params.container['Abloesewert']],
                                      'dates': pd.date_range(start = tempDate, end = tempDate)})
            self.cashflows.append(cashflows("Ablösewert", self.params.container['Inbetriebnahmedatum'], df))

    def calcElectricityProductionCashflow(self):
        periods = 13 - self.params.container['Inbetriebnahmedatum'].month + self.params.container['AfA'] * 12
        dates = pd.date_range(start = self.params.container['Inbetriebnahmedatum'], end = None, periods = periods, freq = 'M')
        electricity = [None] * len(dates)

        rd = self.params.container["RevenueDistribution"]
        factors = [None] * (len(dates) + 1)
        monthly_degradation_factor = (1 - self.params.container['Degradation']) ** (1 / 12)
        annual_electricity = self.params.container['kWp'] * self.params.container['kWh_kWp']

        p_loss = 1.0 + self.params.container['P_Val'].p_value_delta(self.params.container['P_Wert'])

        factors[0] = rd.cum_remainder(self.params.container['Inbetriebnahmedatum'])
        temp = monthly_degradation_factor
        for i in range(len(dates)):
            factors[i + 1] = rd.cum_remainder(dates[i])
            if i != 0 and dates[i].month == 1:
                electricity[i] = annual_electricity * (1 - factors[i + 1]) * temp * p_loss
            elif dates[i].month != 12:
                electricity[i] = annual_electricity * (factors[i] - factors[i + 1]) * temp * p_loss
            else:
                electricity[i] = annual_electricity * factors[i] * temp * p_loss
            temp *= monthly_degradation_factor

        self.electricity = pd.DataFrame(data = {'electricity': electricity, 'dates': dates})
        revenues = pd.DataFrame(data = {'revenues': electricity, 'dates': dates})
        revenues.revenues = revenues.revenues * self.params.container['production_price_kWh']
        self.cashflows.append(cashflows("Produktion", self.params.container['Inbetriebnahmedatum'], revenues))

    def calcFixAmountPerAnnumCashflow(self):
        periods = self.params.container['AfA'] + 1
        dates = pd.date_range(start = self.params.container['Inbetriebnahmedatum'], periods = periods, freq = 'A-DEC')

        tempCosts = 0.0
        keys = self.params.container.keys()
        for item in keys:
            if item in ['Messstellenbetrieb', 'Stromeigenbedarf', 'OnlinePortalNutzungsentgelt', 'InternetNutzungsvertrag', 'Verwaltungskosten', 'Beteiligungskosten']:
                tempCosts -= self.params.container[item]

        inflfactors = self.getInflationFactors(dates)

        fixedCosts = pd.DataFrame(data = {'costs': [tempCosts] * len(dates) * inflfactors, 'dates': dates})
        fixedCosts.loc[0, 'costs'] *= self.yearfraction(self.params.container['Inbetriebnahmedatum'])

        self.cashflows.append(cashflows("Fixe jährliche Kosten", self.params.container['Inbetriebnahmedatum'], fixedCosts))

    def calcFixAmountPerAnnumPerkWpCashflow(self):
        periods = self.params.container['AfA'] + 1
        dates = pd.date_range(start=self.params.container['Inbetriebnahmedatum'], periods = periods, freq = 'A-DEC')

        tempCosts = 0.0
        keys = self.params.container.keys()
        for item in keys:
            if item in ['Anlagenversicherung', 'Wartungsvertrag']:
                tempCosts -= self.params.container[item]

        tempCosts *= self.params.container['kWp']

        inflfactors = self.getInflationFactors(dates)

        fixedCostsPerkWp = pd.DataFrame(data = {'costs': [tempCosts] * len(dates) * inflfactors, 'dates': dates})
        fixedCostsPerkWp.loc[0, 'costs'] *= self.yearfraction(self.params.container['Inbetriebnahmedatum'])

        self.cashflows.append(cashflows("Fixe jährliche Kosten pro kWp", self.params.container['Inbetriebnahmedatum'], fixedCostsPerkWp))

    def calcCostsRelativeToRevenues(self):
        prodCashflow = next(item for item in self.cashflows if item.name == "Produktion")
        dates = prodCashflow.df.dates

        tempCosts = 0.0
        keys = self.params.container.keys()
        for item in keys:
            if item in ['Reparaturrückstellungen', 'Pachtkosten']:
                tempCosts -= self.params.container[item]

        tempCosts *= prodCashflow.df.revenues

        inflfactors = self.getInflationFactors(dates)

        costsRelativeToRevenues = pd.DataFrame(data = {'costs': tempCosts * inflfactors, 'dates': dates})

        self.cashflows.append(cashflows("Kosten abhängig von Erlösen", self.params.container['Inbetriebnahmedatum'], costsRelativeToRevenues))

    def findPrice(self, price, discountRate = 0.0):
        self.params.container['production_price_kWh'] = price
        self.params.hasChanged = True
        self.params.changeNotifier.notifyObservers()
        return self.combined_cashflow.npv(discountRate)

    def calcLCOE(self, discountRate = None):
        if discountRate == None:
            discountRate = self.params.container['LCOEDiskontierungszins']

        result = 0.0
        for item in self.cashflows:
            if item.name != "Produktion" and item.name != "Kosten abhängig von Erlösen":
                result -= item.npv(discountRate)

        tempElectricityCashflow = cashflows("Electricity Cashflow", self.params.container['Inbetriebnahmedatum'], self.electricity)
        costsRelativeToRevenuesCashflow = next(item for item in self.cashflows if item.name == "Kosten abhängig von Erlösen")

        return result / (tempElectricityCashflow.npv(discountRate) + costsRelativeToRevenuesCashflow.npv(discountRate) / self.params.container['production_price_kWh'])

    def update_after_rollout(self, input):
        input['Eigenkapitalrendite Produktion vor Steuern'] = '{:.2%}'.format(round(self.combined_cashflow.irr(), 4))
        self.params.container["production_price_kWh"] = self.calcLCOE(0.0)
        input['LCOE'] = '{:.3}'.format(self.params.container["production_price_kWh"])
        self.params.hasChanged = True
        self.params.changeNotifier.notifyObservers()
        input['LCOE bei LCOE Diskontierungszins'] = '{:.3}'.format(self.calcLCOE())
        input['Eigenkapitalrendite Produktion vor Steuern bei Preis = LCOE'] = '{:.2%}'.format(round(self.combined_cashflow.irr(), 4))
        return input

    # def calcLCOE(self, discountRate = None):
    #     if discountRate is None:
    #         discountRate = self.params.container['LCOEDiskontierungszins']
    #
    #     return np.asscalar(fsolve(self.findPrice, x0 = 0.10, args = (discountRate)))
