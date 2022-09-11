from filetools import class_for_name
from Tools.P_Values import P_Values
from Tools.Financing import Financing
from Tools.Annual_Revenue_Distribution import Rev_Dist
from Modules.Parameters import Parameters
from Tools.DVQ import DVQ
import numpy as np
import xlwings as xw
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def calc():
    # bk = xw.Book('E:/Frank/PycharmProjects/PV/Module.xlsx')
    bk = xw.Book.caller()
    modelSetupList = bk.sheets['ModuleSetup'].range('A2').options(expand = 'table').value

    moduleSetupDict = {};
    for item in modelSetupList:
        temp = {}
        temp['type'] = item[1]
        tempList = []
        for subitem in item[2].split(', '):
            if subitem == 'None':
                tempList.append(None)
            else:
                tempList.append(subitem)
        temp['predecessors'] = tempList
        moduleSetupDict[item[0]] = temp

    bk.sheets['Kennzahlen'].clear()
    bk.sheets['Output'].clear()

    paramDict = bk.sheets['Parameter'].range('B2:C42').options(dict).value
    paramDict['production_price_kWh'] = 0.1
    pValDict = bk.sheets['Parameter'].range('E2:F18').options(dict).value

    x = bk.sheets['Parameter'].range('K2:K25').options(np.array).value
    y = bk.sheets['Parameter'].range('L2:L25').options(np.array).value
    DVQ_curve = DVQ(x, y)

    p_val = P_Values()
    p_val.from_dict(pValDict)

    rd = Rev_Dist()
    financingData = bk.sheets['Parameter'].range('I2:I5').value
    # annuity = Financing(0.0175, 120, 0.03, 180)
    annuity = Financing(financingData[0], financingData[1], financingData[2], financingData[3])

    params = Parameters()
    params.from_dict(paramDict)
    params.append(P_Val = p_val, RevenueDistribution = rd, DVQ = DVQ_curve, Annuität = annuity)

    modules = []
    results = {}
    for item in moduleSetupDict:
        name = item
        modType = moduleSetupDict[name]['type']
        predecessorNames = moduleSetupDict[name]['predecessors']
        predecessors = []
        for subitem in predecessorNames:
            if subitem is not None:
                tempVal = [x for x in modules if x.name == subitem][0]
                predecessors.append(tempVal)

        tempModule = class_for_name('Modules', modType, name, params, predecessors)
        tempModule.roll_out_cashflows()
        tempModule.combined_cashflows()
        results = tempModule.update_after_rollout(results)
        modules.append(tempModule)

    bk.sheets['Kennzahlen'].range('A1').options(dict).value = results
    df = modules[-1].get_cashflow_dataframe()
    cols = df.columns.tolist()
    ind = cols.index('years')
    cols = list(set([i for i in range(len(cols))]).difference([ind]))
    subdf = df[[item for item in df.columns[cols] if "years" not in item]]

    bk.sheets['Output'].range('A1').options(pd.DataFrame).value = subdf

    subdf.dates = pd.DatetimeIndex(subdf.dates)
    subdf.set_index('dates', inplace = True)

    # subdf.plot(kind = 'bar', stacked = True)

    margin_bottom = np.zeros(len(subdf.index))
    # last = np.zeros(len(subdf.index))
    for item in subdf.columns:
        plt.bar(subdf.index, subdf[item], 15,  bottom = margin_bottom, label = item)
        last = np.array(subdf[item])
        margin_bottom += last

    if paramDict['ChartOutput']:
        ax = plt.axes()
        ax.xaxis.set_major_locator(mdates.YearLocator(base = 3))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax.xaxis.set_minor_locator(mdates.MonthLocator(interval = 3))
        datemin = np.datetime64(subdf.index[0], 'Y') - np.timedelta64(1, 'M')
        datemax = np.datetime64(subdf.index[-1], 'Y') + np.timedelta64(1, 'M')
        ax.set_xlim(datemin, datemax)
        ax.set_xlabel('')
        minVal = (round(min(subdf[['Zinsen', 'Tilgung',
               'Fixe jährliche Kosten', 'Fixe jährliche Kosten pro kWp',
               'Kosten abhängig von Erlösen',
               'Kosten abhängig von Erlösen Vertrieb', 'Steuern', 'Rücklage']].sum(axis = 1)) / 1000) - 1) * 1000
        maxVal = (round(max(subdf[['Produktion', 'Direktverbrauch', 'Einspeisung']].sum(axis = 1)) / 1000) + 1) * 1000
        ax.set_ylim(minVal, maxVal)
        ax.legend(prop = {'size': 5})
        fig = ax.get_figure()
        bk.sheets['Output'].pictures.add(fig, name = 'Cashflows', update = True)

def hello_xlwings():
    wb = xw.Book.caller()
    wb.sheets[0].range("A1").value = "Hello xlwings!"


@xw.func
def hello(name):
    return "hello {0}".format(name)
