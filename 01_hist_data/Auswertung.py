# ===============================================================================
# Auswertung.py
# Analysis and plots belonging to Smart Balancing Simulation (SBS)
# Define location and name of folders with SBS time series (output csv-files):
# 'hist_sim_output_all.csv' and 'hist_sim_output_period.csv'
# ===============================================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
desired_width = 320
pd.set_option('display.width', desired_width)
pd.set_option('display.max_columns', 15)
# ===============================================================================
# define location and name of files to set path
# ===============================================================================

location = "results/"
#location = "results_sin/"
#location = "results_5d/"
#location = "results_1d/"

#================================================================================
#What do you want to analyse?
#================================================================================
save_june_event_csv = True
example_plot = False
frequency_analysis = False
technology_analysis = False
#================================================================================
if location == "results/":
        scenario_files = ['1 no SB','2 TL3','3 TL6'] #,'4 DE', '5 NL'] #,'6 BEPP15','7 BEPP1']
        scenario_path = ['1 no SB','2 TL3','3 TL6'] #,'4 DE', '5 NL'] #,'6 BEPP15','7 BEPP1']

if location == "results_sin/" or location == "results_1d/":
        scenario_files = ['1 no SB','4 DE','5 NL'] #['1 no SB','4 DE', '5 NL']
        scenario_path = ['1 no SB','4 DE','5 NL'] #['1 no SB','4 DE', '5 NL']
#================================================================================
if save_june_event_csv:
        june_data = pd.DataFrame()
# ===============================================================================
#define start and end of example plots
# ===============================================================================

if location == "results_sin/" or location == "results_1d/":
        start = ["2019-01-01 5:00","2019-01-01 9:00","2019-01-01 14:25"]
        end = ["2019-01-01 7:45","2019-01-01 9:45","2019-01-01 15:45"]

if location == "results/":
        start = ["2019-06-12 10:45"]
        end = ["2019-06-12 12:15"]

if location == "XXresults_1d/":
        start = ["2019-01-01 14:25"]
        end = ["2019-01-01 14:45"]
# ===============================================================================
#define start and end of simulation for time stamp index of /hist_sim_output_all.csv'
# ===============================================================================

sim_start = '00:00 01.01.2019'

if location == "results_5d/":
        sim_end_all = '23:59 01.05.2019'
elif location == "results_1d/":
        sim_end_all = '23:59 01.01.2019'
else:
        sim_end_all = '23:59 12.31.2019'


# ===============================================================================
#no further definitions needed
# ===============================================================================
#init lists and dataframe for calculations
# ===============================================================================
scenario_data = list()
#scenario_data_period = list()
scenario_sum = list()
data_sum = list()
minute_sum = list()
scenario_sum_df = pd.DataFrame()

if frequency_analysis:
        frequency_df = pd.DataFrame()

if technology_analysis:
        techno_results = {}
        techno_results['Technologie'] = {'Scenario': [ 'Energie', 'Gewinn', 'spz. Kosten', 'Aufrufe', 'Dauer']}

for j in range(len(scenario_files)):

        #read "period" csv files with ISP resolution (15min)
        scenario_path[j]= location+scenario_files[j]+'/hist_sim_output_period.csv'

        #print('Scenario: ',scenario_path[j])
        scenario_period = pd.read_csv(scenario_path[j], sep=';', encoding='utf-8').round(1)  #'latin-1').round(1)

        #read "all" csv file with all timesteps in 1 min resolution
        scenario_path[j] = location + scenario_files[j] + '/hist_sim_output_all.csv'
        minute_data = pd.read_csv(scenario_path[j], sep=';', encoding='latin-1')

        print('Data load completed: ', scenario_path[j])

        minute_sum.append(minute_data.sum())
        print(j, minute_data.sum())
        minute_data.index = pd.date_range(start=sim_start, end=sim_end_all, freq='1 min')
        scenario_data.append(minute_data)

        if save_june_event_csv and j <3:
                if j == 0:
                        june_data['Historic'] = minute_data['06.12.2019 10:30':'06.12.2019 12:15']['FRCE [MW]']
                else:
                        june_data[scenario_files[j]] = minute_data['06.12.2019 10:30':'06.12.2019 12:15']['FRCE [MW]']

        if technology_analysis:
                names = ['Solar', 'Wind onshore', 'Wind offshore', 'Aluminium', 'Steel', 'Cement', 'Paper', 'Chlorine','Gas']
                EES = ['Solar', 'Wind onshore', 'Wind offshore']

                for name in names:
                        Dict_scenario_period = dict()
                        Dict_scenario_data = dict()
                        Dict_scenario_period['costs'] = scenario_period[name + ' AEP costs [EUR]'].copy()
                        Dict_scenario_period['AEP'] = scenario_period['GER AEP [EUR/MWh]'].copy()
                        # Kosten / AEP = Energy
                        Dict_scenario_period[name] = Dict_scenario_period['costs'] / Dict_scenario_period['AEP']

                        # Count balancing processes
                        Dict_scenario_data[name + '_ON'] = [None] * len(scenario_data[j]['time [s]'])
                        Dict_scenario_data[name + '_runtime'] = [None] * len(scenario_data[j]['time [s]'])
                        Dict_scenario_data[name + 'Power'] = list(scenario_data[j][name + ' Power [MW]'])

                        duration = 0
                        for t in range(1,len(scenario_data[j]['time [s]'])):
                                # start balancing
                                if Dict_scenario_data[name + 'Power'][t] != 0 and Dict_scenario_data[name + 'Power'][t-1] == 0:
                                        duration = 1
                                        Dict_scenario_data[name + '_ON'][t] = 1
                                # continue balancing
                                elif Dict_scenario_data[name + 'Power'][t] != 0:
                                        duration += 1
                                # stop balancing
                                if Dict_scenario_data[name + 'Power'][t] == 0 and Dict_scenario_data[name + 'Power'][t-1] != 0:
                                        Dict_scenario_data[name + '_runtime'][t] = duration

                        scenario_data[j][name + '_ON'] = Dict_scenario_data[name + '_ON']
                        scenario_data[j][name + '_runtime'] = Dict_scenario_data[name + '_runtime']

                        scenario_period[name] = Dict_scenario_period[name]


        #scenario_period.index = pd.date_range(start='00:00 01.01.2019', end='23:30 01.05.2019', freq='15 min')
        #scenario_data_period.append(scenario_period)

# # ===============================================================================
# # Show Example Plot with 1 min resolution
# # ===============================================================================
        if example_plot:
                for i in range(len(start)):
                         scenario_data[j][start[i]:end[i]].drop(
                                 ['time [s]', 'f [Hz]', 'aFRR FRCE (open loop) [MW]', 'mFRR P [MW]','Unnamed: 20'],
                                 axis=1).plot(secondary_y='AEP [EUR/MWh]', title='Scenario ' + scenario_files[j])


# ===============================================================================
# Calculate Balancers Profit
# ===============================================================================
        # list for calculations in loop
        scenario_sum.append(scenario_period.sum())
        data_sum.append(scenario_data[j].sum())
        # dataframe for bar plot after loop
        scenario_sum_df[scenario_files[j]] = scenario_period.sum()

        #save values from reference scenario "1 no SB"
        if j == 0:
                reference_sum = scenario_sum[j]

        if technology_analysis:
                income_all = {}
                income_all['Solar'] = [scenario_sum[j]['Solar AEP costs [EUR]'] ]#- scenario_sum['Solar Marktprämie [EUR]']]
                income_all['Wind onshore'] = [scenario_sum[j]['Wind onshore AEP costs [EUR]']]# - scenario_sum['Wind onshore Marktprämie [EUR]']]
                income_all['Wind offshore'] = [scenario_sum[j]['Wind offshore AEP costs [EUR]']]# - scenario_sum['Wind offshore Marktprämie [EUR]']]
                income_all['Alu'] = [scenario_sum[j]['Aluminium AEP costs [EUR]']]
                income_all['Alu'] = [scenario_sum[j]['Aluminium AEP costs [EUR]']]
                income_all['Steel'] = [scenario_sum[j]['Steel AEP costs [EUR]']]
                income_all['Cement'] = [scenario_sum[j]['Cement AEP costs [EUR]']]
                income_all['Paper'] = [scenario_sum[j]['Paper AEP costs [EUR]']]
                income_all['Chlorine'] = [scenario_sum[j]['Chlorine AEP costs [EUR]']]
                income_all['Gas'] = [scenario_sum[j]['Gas AEP costs [EUR]']]

                header_energy = []
                header_price = []
                for name in names:
                        energy = minute_sum[j][name + ' Power [MW]']
                        costs = scenario_sum[j][name+ ' AEP costs [EUR]']
                        # Marktprämie calculation
                        if name in EES:
                                dMP = scenario_sum[0][name + ' Marktprämie [EUR]'] - scenario_sum[j][name + ' Marktprämie [EUR]']
                                print(name, 'dMP: ', dMP)
                                profit = (-(costs+dMP))
                        else:
                                profit = -costs
                        print(name, ' Profit: ', (profit).round(1), ' kEUR')
                        print(name, ' energy: ', (energy/60).round(1), ' MWh')
                        income_all[name+' Energy'] = energy
                        income_all[name+ ' spc. costs [EUR/MWh]'] = profit / (energy/60)
                        header_price.append(name+ ' spc. costs [EUR/MWh]')
                        header_energy.append(name+' Energy')
                        #['Scenario', 'Energie', 'Gewinn', 'spz. Kosten', 'Aufrufe', 'Dauer']
                        print(name in techno_results)
                        if (name in techno_results) == False:
                                techno_results[name] = {}
                        techno_results[name][scenario_files[j]] = [(profit/1000).round(1), (energy / 60).round(1), profit / (energy / 60), data_sum[j][name+ '_ON'], data_sum[j][name+ '_runtime']]

                #header = ['Solar', 'Wind onshore', 'Wind offshore', 'Alu, Steel', 'Cement', 'Paper', 'Chlorine', 'Gas']
                data = pd.DataFrame.from_dict(income_all) #, orient='index')

                show_data_energy = data[header_energy].T
                show_data_price = data[header_price].T
                print('------------------------------------------------------------------')
                print('Scenario ',scenario_files[j],': PROFITS BY TECHNOLOGY')
                print('------------------------------------------------------------------')
                print('The balancers specific energy purchase costs in EUR/MWh')
                print((show_data_price).round(1))
                print('------------------------------------------------------------------')
                print('The balancers energy purchase in MWh')
                print((show_data_energy).round(1))
                print('------------------------------------------------------------------')


# ===============================================================================
# Calculate Overall System Impact
# ===============================================================================
# compare positive and negative balancing power of ref and sce
        aFRR_pos = scenario_sum[j]['GER pos. energy aFRR [MWh]'] / reference_sum['GER pos. energy aFRR [MWh]']
        aFRR_neg = scenario_sum[j]['GER neg. energy aFRR [MWh]'] / reference_sum['GER neg. energy aFRR [MWh]']
        mFRR_pos = scenario_sum[j]['GER pos. energy mFRR [MWh]'] / reference_sum['GER pos. energy mFRR [MWh]']
        mFRR_neg = scenario_sum[j]['GER neg. energy mFRR [MWh]'] / reference_sum['GER neg. energy mFRR [MWh]']
        print('Scenario ',scenario_files[j],': POWER')
        print('------------------------------------------------------------------')
        print('Positive aFRR could be reduced to: ', aFRR_pos.round(2)*100,'% of the reference simulation')
        print('Negative aFRR could be reduced to: ', aFRR_neg.round(2)*100,'% of the reference simulation')
        print('------------------------------------------------------------------')
        print('Positive mFRR could be reduced to: ', mFRR_pos.round(2)*100,'% of the reference simulation')
        print('Negative mFRR could be reduced to: ', mFRR_neg.round(2)*100,'% of the reference simulation')
        print('------------------------------------------------------------------')

# ===============================================================================
# Calculate Overall System Costs
# ===============================================================================
# compare balancing costs of ref and sce
        costs_pos = (scenario_sum[j]['GER pos. aFRR costs [EUR]'] + scenario_sum[j]['GER pos. mFRR costs [EUR]']) / (reference_sum['GER pos. aFRR costs [EUR]'] + reference_sum['GER pos. mFRR costs [EUR]'])
        costs_neg = (scenario_sum[j]['GER neg. aFRR costs [EUR]'] + scenario_sum[j]['GER neg. mFRR costs [EUR]']) / (reference_sum['GER neg. aFRR costs [EUR]'] + reference_sum['GER neg. mFRR costs [EUR]'])
        costs_tot = (scenario_sum[j]['GER pos. aFRR costs [EUR]'] + scenario_sum[j]['GER pos. mFRR costs [EUR]'] + scenario_sum[j]['GER neg. aFRR costs [EUR]'] + scenario_sum[j]['GER neg. mFRR costs [EUR]']) / (reference_sum['GER pos. aFRR costs [EUR]'] + reference_sum['GER pos. mFRR costs [EUR]'] + reference_sum['GER neg. aFRR costs [EUR]'] + reference_sum['GER neg. mFRR costs [EUR]'])
        print('Scenario ',scenario_files[j],': COSTS')
        print('------------------------------------------------------------------')
        print('Pos balancing costs could be reduced to: ', costs_pos.round(2)*100,'% of the reference simulation')
        print('Neg balancing costs could be reduced to: ', costs_neg.round(2)*100,'% of the reference simulation')
        print('Total balancing costs could be reduced to: ', costs_tot.round(2)*100,'% of the reference simulation')
        print('------------------------------------------------------------------')

# ===============================================================================
# Calculate Balancers Impact on System Frequency (Rest of Europe = 300 GW and balanced)
# ===============================================================================
# compare contribution to frequency deviation
        # dataframe for bar plot after loop
        if frequency_analysis:
                frequency_df[scenario_files[j]] = scenario_data[j].std()
                # save values from reference scenario "1 no SB"
                if j == 0:
                        frequency_ref = scenario_data[j]['f [Hz]'].std()

                frequency_all = {}
                frequency_all[scenario_files[j], ' f Mean in Hz'] = scenario_data[j]['f [Hz]'].mean()
                frequency_all[scenario_files[j],' f std in Hz']= scenario_data[j]['f [Hz]'].std()
                frequency_all[scenario_files[j], ' f min in Hz'] = scenario_data[j]['f [Hz]'].min()
                frequency_all[scenario_files[j], ' f max in Hz'] = scenario_data[j]['f [Hz]'].max()

                print('Scenario ', scenario_files[j], ': FREQUENCY')
                print('------------------------------------------------------------------')
                print('f Mean: ', frequency_all[scenario_files[j], ' f Mean in Hz'], ' Hz')
                print('f Std: ', frequency_all[scenario_files[j], ' f std in Hz'].round(6), ' Hz')
                print('f min: ', frequency_all[scenario_files[j], ' f min in Hz'].round(3), ' Hz')
                print('f max: ', frequency_all[scenario_files[j], ' f max in Hz'].round(3), ' Hz')
                print('------------------------------------------------------------------')
                print('------------------------------------------------------------------')
# ===============================================================================
#todo: Inputs zur Analyse, welche Technologie wann richtig stand?
#todo: sign of imba vs. sign of SB per technology
#print('The impact of the single technologies on system stability is as follows: ')
#print('Income.sum()')



# ===============================================================================
# Bar-Plot with Comparison of all Scenarios (balancing energy and costs)
# ===============================================================================
Energie_Summen = scenario_sum_df.filter(['GER pos. energy aFRR [MWh]', 'GER neg. energy aFRR [MWh]', 'GER pos. energy mFRR [MWh]', 'GER neg. energy mFRR [MWh]'], axis=0)/1000
Energie_Summen.plot.bar(title='Comparison of Balancing Energy')
plt.ylabel('balancing energy in GWh')
Energie_Summen.to_csv("energie_summen_hist.csv")

Kosten_Summen = scenario_sum_df.filter(['GER pos. aFRR costs [EUR]','GER neg. aFRR costs [EUR]', 'GER pos. mFRR costs [EUR]','GER neg. mFRR costs [EUR]'], axis=0)/1000000
Kosten_Summen.plot.bar(title='Comparison of Costs')
plt.ylabel('costs in mio. €')
Kosten_Summen.to_csv("kosten_summen_hist.csv")

if save_june_event_csv:
        fig, ax = plt.subplots(1, 1)
        ax.plot(june_data['Historic'], label='Historic')
        ax.plot(june_data['2 TL3'], '--', label='TL3')
        ax.plot(june_data['3 TL6'], ':', label='TL6')
        plt.hlines(3098.0,june_data.first_valid_index(),june_data.last_valid_index(), linestyles='-.',  lw=0.5,label='100% FRR')
        plt.hlines(4647.0, june_data.first_valid_index(), june_data.last_valid_index(), linestyles='-.', lw=0.5,label='150% FRR')
        plt.ylabel('ACE in MW')
        plt.legend()

plt.show()

if technology_analysis:
        results = {}
        cols = ['Gewinn', 'Energie','spz. Kosten', 'Aufrufe', 'Dauer']
        for name in names:
                results[name] = pd.DataFrame()
                results[name] = (pd.DataFrame.from_dict(techno_results[name])).T
                results[name].columns = cols

                print(name)
                print("-------------------------------------------------------------------------")
                print(results[name])
                print("-------------------------------------------------------------------------")

        results_col = {}
        for col in cols:
                results_col[col] = {}
                for name in names:
                        results_col[col][name] = results[name][col]

                print(col)
                print("-------------------------------------------------------------------------")
                print(pd.DataFrame.from_dict(results_col[col]))
                print("-------------------------------------------------------------------------")