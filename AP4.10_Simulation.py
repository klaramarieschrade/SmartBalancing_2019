# ....................................................................................
# ...Smart Balancing SIMULATION SOFTWARE.........................................................
# ....................................................................................
# ...Project:        Norddeutsche EnergieWende 4.0 (NEW 4.0)
# ...Authors:        Julian Franz, Anna Meissner, Felix Roeben, Simon Rindelaub
# ...Institution:    Fraunhofer Institute for Silicon Technologies (ISIT)
# ...Department:     Power Electronics for Renewable Energy Systems
# ....................................................................................
# ...Purpose:        Simulation of energy balancing markets
# ....................................................................................
# ...Version:        1.2
# ...Date:           July 24th 2020
# ....................................................................................

# ------------------------------------------------------------------------------------
# ---IMPORT---------------------------------------------------------------------------
# ------------------------------------------------------------------------------------

import matplotlib.pyplot as plt
import time
import os
import sys
import pandas as pd
from datetime import datetime

# ...Import of project files
import gridelem
import balagrou
import generato
import loadload
import smarbala
import fuzzlogi_marketdesign
import fileexch
import grapfunc
import math



# ------------------------------------------------------------------------------------
# ---DEFINITION OF SIMULATION PARAMETERS----------------------------------------------
# ------------------------------------------------------------------------------------

savefilename_period = 'Sim_output_period_sprung.csv'       # name of save file, location defined by "scenario"
savefilename_all = 'Sim_output_all_sprung.csv'             # name of save file, location defined by "scenario"
scenario = '01_hist_data//hist_' #'01_hist_data//vali_'
#scenario = '02_synth_data//synth_'
#scenario = '03_validation_data//vali_'

# ...Activation of simulation functions
smartbalancing = False      # True: Smart Balancing is globally switched on
fuzzy = False               # True: Smart Balancing is globally activated via Fuzzy Logic
FRR_pricing = 0             # Global variable to switch both aFRR & mFRR from pay-as-bid (0) to marginal pricing (1)
BEPP = 900                  # Balancing Energy Pricing Period (BEPP) in s - only applied for marginal pricing
                            # e.g. 900 (State of the art) or 60 or 4 (=> t_step!)
imbalance_clearing = 0      # For fuzzy SB: Switch from single imbalance pricing (0) to "combined pricing" as in NL (1)
                            # (2) for traffic light with 3 increments and (3) for traffic light approach with 5 increments
save_data = True            # True: write the simulation data to .csv
show_fig = False            # True: show all figures at the end of the simulation
sb_delay = 0.0              # definition of delay of SB signal in s

# ...Simulation time settings
t_step = 1                              # simulation time step in s
t_now = 0                               # start of simulation in s
t_stop =  30 * 60 - t_step          # time, at which the simulation ends in s, one month
k_now = 0                               # discrete time variable
t_day = t_now                           # time of current day in s
t_isp = 15 * 60                         # duration of an Imbalance Settlement Period in s
t_mol = 4 * 60 * 60                     # time in s, after which the MOLs gets updated
day_count = 0                           # number of the day of the year
month_count = 0                         # number of the month of the year
day_in_month = 0                        # day of the month

# ...Vectors for the simulation time variables
t_vector = []
k_vector = []

# ...Checking divisibility of time constants
if (86400.0 % t_step) != 0: # 86400 s = 24 h
    print('ERROR! 86400 must be divisible by t_step!')#sys.exit('ERROR! 86400 must be divisible by t_step!')
elif (t_isp % t_step) != 0:
    sys.exit('ERROR! t_isp must be divisible by t_step!')
elif (t_mol % t_step) != 0:
    sys.exit('ERROR! t_mol must be divisible by t_step!')
else:
    pass

# ...Calculation of duration of simulation
sim_duration = t_stop - t_now
sim_steps = int(((t_stop + t_step) - t_now) / t_step)
print('Simulating', sim_steps, 'time steps with a step size of', t_step, 's')

# ...Set simulation time settings in timestamps utc
sim_duration_utc = ['01.01.2019', '31.12.2019', '01.01.2020']

# Measurement of simulation time
start = 0.0
start = time.time()

os.system("cls")



# ------------------------------------------------------------------------------------
# ---INITIALIZATION OF GRID MODEL-----------------------------------------------------
# ------------------------------------------------------------------------------------

# ...Array buffering the set of Balancing Groups during initialization
array_bilanzkreise = []

# ...Arrays with the "Monatsmarktwert" in EUR/MWh for each month of 2019 for Wind onshore, Wind offshore, and PV
array_windon_mmw =  [38.33, 38.11, 24.23, 32.62, 35.64, 22.31, 36.41, 30.29, 30.64, 31.94, 37.09, 25.99]
array_windoff_mmw = [42.98, 40.88, 26.72, 34.16, 35.59, 26.62, 36.44, 32.00, 33.17, 33.23, 38.35, 29.36]
array_pv_mmw =      [59.06, 42.13, 30.75, 31.72, 35.30, 29.10, 39.17, 33.76, 33.45, 37.88, 43.83, 36.96]

print('\nInitializing data from CSV files')

# ...read DA prices for specified time range (sim_duration_uct) from csv
list_da_prices = fileexch.get_da_price_data(sim_duration_utc)
i = 0
t_da = 0.0
array_da_prices = []
# ...write prices into array with one value per time step of the simulation
while t_da < (t_stop + t_step):
    array_da_prices.append(list_da_prices.iloc[math.floor(i / 3600 * t_step)][0])
    t_da += t_step
    i += 1

# ...Initialization of Synchronous Zone
SZ = gridelem.SynchronousZone(name='UCTE Netz', f_nom=50)

# ...Initialization of Control Areas
CA0 = gridelem.CalculatingGridElement(name='Rest des UCTE Netzes',
                                      gen_P=300000.0,
                                      load_P=300000.0,
                                      FCR_lambda=13500.0,
                                      aFRR_Kr=14000.0,
                                      aFRR_T=170.0,
                                      aFRR_beta=0.1,
                                      aFRR_delay=30.0)
SZ.array_subordinates.append(CA0)

CA1 = gridelem.ControlArea(name='Deutschland',
                           FCR_lambda=1500.0,
                           aFRR_Kr=1550.0,
                           aFRR_T=250.0,
                           aFRR_beta=0.1,
                           aFRR_delay=30.0,
                           aFRR_pricing=FRR_pricing,
                           imbalance_clearing = imbalance_clearing,
                           mFRR_pos_trigger=0.37,
                           mFRR_neg_trigger=0.41,
                           mFRR_pos_target=0.36,
                           mFRR_neg_target=0.375,
                           mFRR_time=300.0,
                           mFRR_pricing=FRR_pricing,
                           sb_delay=sb_delay)
SZ.array_subordinates.append(CA1)

CA1.array_da_prices = array_da_prices

# ...Initialization of Balancing Groups
# read balance Groups from csv and add to Control area
array_bilanzkreise = fileexch.get_balancing_groups(scenario, smartbalancing, sim_steps)

for i in range(len(array_bilanzkreise)):
    CA1.array_balancinggroups.append(array_bilanzkreise[i])

# Creating smart balancing assets from .csv files and assigning them to the respective balancing groups
array_assets = fileexch.get_sb_assets(scenario)
for asset in array_assets:
    for i in range(len(CA1.array_balancinggroups)):
        if CA1.array_balancinggroups[i].name == asset.bg_name:
            CA1.array_balancinggroups[i].array_sb_assets.append(asset)
            break

# Assign smart balancing parameters of flexible generators to already existing 'GeneratorFlex'-objects
# 'GeneratorFlex'-objects need to be created first
fileexch.get_gen_flex(scenario=scenario,
                      control_area=CA1)

# Assign smart balancing parameters of flexible loads to already existing 'LoadFlex'-objects
# 'LoadFlex'-objects need to be created first
fileexch.get_load_flex(scenario=scenario,
                       control_area=CA1)
# MOL: read csv, if historic ACE
if scenario == '01_hist_data//hist_':# or '03_validation_data//vali_':
    CA1.array_aFRR_molpos, CA1.array_aFRR_molneg = fileexch.read_afrr_mol(scenario, 0, 0, 0)
    CA1.array_mFRR_molpos, CA1.array_mFRR_molneg = fileexch.read_mfrr_mol(scenario, 0, 0, 0)

elif FRR_pricing == 0:  #synthetic MOL for pay-as-bid --> created in code, not read from csv

    # dicts for pos and neg MOL
    aFRR_molpos = {'Power': [],
                   'Price': []}
    aFRR_molneg = {'Power': [],
                   'Price': []}
    mFRR_molpos = {'Power': [],
                   'Price': []}
    mFRR_molneg = {'Power': [],
                   'Price': []}

    aFRR_pos = 1700
    price = 30
    reserve = 0
    while reserve < aFRR_pos:
        aFRR_molpos['Power'].append(float(100))
        aFRR_molpos['Price'].append(price)
        price = price + 20
        reserve = reserve + 100

    aFRR_neg = -1800
    price = -10
    reserve = 0
    while reserve > aFRR_neg:
        aFRR_molneg['Power'].append(float(-100))
        aFRR_molneg['Price'].append(price)
        price = price + 20
        reserve = reserve - 100

    mFRR_pos = 800
    price = 110
    reserve = 0
    while reserve < mFRR_pos:
        mFRR_molpos['Power'].append(float(100))
        mFRR_molpos['Price'].append(price)
        price = price + 20
        reserve = reserve + 100

    mFRR_neg = -600
    price = 80
    reserve = 0
    while reserve > mFRR_neg:
        mFRR_molneg['Power'].append(float(-100))
        mFRR_molneg['Price'].append(price)
        price = price + 20
        reserve = reserve - 100

    CA1.array_aFRR_molpos = aFRR_molpos
    CA1.array_aFRR_molneg = aFRR_molneg
    CA1.array_mFRR_molpos = mFRR_molpos
    CA1.array_mFRR_molneg = mFRR_molneg

elif FRR_pricing == 1:  #synthetic MOL for marginal pricing

    # dicts for pos and neg MOL
    aFRR_molpos = {'Power': [],
                     'Price': []}
    aFRR_molneg = {'Power': [],
                     'Price': []}
    mFRR_molpos = {'Power': [],
                     'Price': []}
    mFRR_molneg = {'Power': [],
                     'Price': []}

    aFRR_pos = 1700
    price = 30
    reserve = 0
    while reserve < aFRR_pos:
        aFRR_molpos['Power'].append(float(100))
        aFRR_molpos['Price'].append(price)
        price = price +10
        reserve = reserve + 100

    aFRR_neg = -1800
    price = -10
    reserve = 0
    while reserve > aFRR_neg:
        aFRR_molneg['Power'].append(float(-100))
        aFRR_molneg['Price'].append(price)
        price = price +10
        reserve = reserve - 100

    mFRR_pos = 800
    price = 110
    reserve = 0
    while reserve < mFRR_pos:
        mFRR_molpos['Power'].append(float(100))
        mFRR_molpos['Price'].append(price)
        price = price +10
        reserve = reserve + 100

    mFRR_neg = -600
    price = 80
    reserve = 0
    while reserve > mFRR_neg:
        mFRR_molneg['Power'].append(float(-100))
        mFRR_molneg['Price'].append(price)
        price = price +10
        reserve = reserve - 100

    CA1.array_aFRR_molpos = aFRR_molpos
    CA1.array_aFRR_molneg = aFRR_molneg
    CA1.array_mFRR_molpos = mFRR_molpos
    CA1.array_mFRR_molneg = mFRR_molneg

else:
    print('MOL settings not valid - ERROR: no MOL for simulation')


print('\nInitialization Done! It took %.1f seconds' % (time.time() - start))



# ------------------------------------------------------------------------------------
# ---SIMULATION-----------------------------------------------------------------------
# ------------------------------------------------------------------------------------

print('\n#-----------Simulation Start-----------#')
print('#-----------Day %d-----------#' % day_count)

start = time.time()


# ...Initialization of FCR and aFRR parameters
SZ.fcr_init(t_step=t_step)
SZ.afrr_init(t_step=t_step)

#save initial values
#SZ.write_results()

t_vector.append(t_now)
k_vector.append(k_now)

SZ.readarray(k_now) # read arrays with time series consumption, consumption scheduled, generation, generation scheduled, gets values for t_now/k_now
SZ.gen_calc()
SZ.load_calc()
SZ.schedule_init()
SZ.gen_schedule_calc()
SZ.load_schedule_calc()
SZ.imba_calc()
SZ.fcr_calc()
SZ.afrr_calc(k_now=k_now, t_now=t_now, t_step=t_step, t_isp=t_isp, fuzzy=fuzzy,imbalance_clearing=imbalance_clearing,BEPP=BEPP)
#SZ.mfrr_calc(t_now=t_now, t_step=t_step, t_isp=t_isp)
SZ.f_calc(t_step=t_step)
SZ.energy_costs_calc(k_now=k_now, t_now=t_now, t_step=t_step, t_isp=t_isp)

SZ.write_results()
SZ.mol_update()

day_count += 1

print('#-----------Day %d-----------#' % day_count)

# ...Simulation of every time step
while t_now < t_stop:

    start_date = datetime.strptime(sim_duration_utc[0], '%d.%m.%Y')
    current_date = start_date + pd.Timedelta(days=day_count)

    month_count = current_date.month
    day_in_month = current_date.day

    if t_day >= 86400:
        day_count += 1
        print('#Date: ',day_in_month,'.',month_count,'.2019 ---------Day:',day_count,'-----------#')
        t_day = 0.0

    #update MOL after t_mol in case of historic values, otherwise the synthetic MOL remains
    if (t_now % t_mol) == 0 and scenario == '01_hist_data//hist_':# or '03_validation_data//vali_':
        print('Reached MOL update on day', day_count,'at', int((t_day / 3600)) ,'o´clock')
        (CA1.array_aFRR_molpos, CA1.array_aFRR_molneg) = fileexch.read_afrr_mol(scenario, t_day, t_mol, day_count)
        (CA1.array_mFRR_molpos, CA1.array_mFRR_molneg) = fileexch.read_mfrr_mol(scenario, t_day, t_mol, day_count)
        SZ.mol_update()

    # Update of "Monatsmarktwert" variables
    CA1.windon_mmw = array_windon_mmw[month_count - 1]
    CA1.windoff_mmw = array_windoff_mmw[month_count - 1]
    CA1.pv_mmw = array_pv_mmw[month_count - 1]

    t_now += t_step
    t_day += t_step
    t_vector.append(t_now)
    if (t_now) % 60 == 0:
        k_now += 1
        k_vector.append(k_now)

    #todo inserte explanaition of simulaiton order

# 1.read arrays with time series consumption, generation  
    SZ.readarray(k_now)
# 2. calculate generation, load, schedules and resulting imbalance
    SZ.gen_calc()
    SZ.load_calc()
    SZ.gen_schedule_calc()
    SZ.load_schedule_calc()
    SZ.imba_calc()
# 3. calculate frequency deviation and FCR
    #SZ.f_calc(t_step=t_step)
    SZ.fcr_calc()    
# 4. calculate FRR and resulting cost / prices. Smart Balancing is calculated in afrr_calc
    SZ.afrr_calc(k_now=k_now, t_now=t_now, t_step=t_step, t_isp=t_isp, fuzzy=fuzzy,imbalance_clearing=imbalance_clearing,BEPP=BEPP)
    #note: AEP for next iteration is calculated in mfrr_calc.
    #SZ.mfrr_calc(t_now=t_now, t_step=t_step, t_isp=t_isp)
    SZ.energy_costs_calc(k_now=k_now, t_now=t_now, t_step=t_step, t_isp=t_isp)
    SZ.f_calc(t_step=t_step)
# 5. write results
    SZ.write_results()

print('#-----------Simulation Done-----------#\n')
print('Simulation time: %.1f seconds\n' % (time.time() - start))



# ------------------------------------------------------------------------------------
# ---SAVE SIMULATION RESULTS----------------------------------------------------------
# ------------------------------------------------------------------------------------

if save_data:
    save_dict = {'time [s]': t_vector,
                 'GER FCR Power [MW]': CA1.array_FCR_P,
                 'GER pos. energy aFRR [MWh]': CA1.array_aFRR_E_pos_period,
                 'GER neg. energy aFRR [MWh]': CA1.array_aFRR_E_neg_period,
                 'GER pos. aFRR costs [EUR]': CA1.array_aFRR_costs_pos_period,
                 'GER neg. aFRR costs [EUR]': CA1.array_aFRR_costs_neg_period,
                 'GER pos. energy mFRR [MWh]': CA1.array_mFRR_E_pos_period,
                 'GER neg. energy mFRR [MWh]': CA1.array_mFRR_E_neg_period,
                 'GER pos. mFRR costs [EUR]': CA1.array_mFRR_costs_pos_period,
                 'GER neg. mFRR costs [EUR]': CA1.array_mFRR_costs_neg_period,
                 'GER AEP [EUR/MWh]': CA1.array_AEP,
                 #'Solar AEP costs [EUR]': CA1.array_balancinggroups[14].array_AEP_costs_period,
                 #'Solar Marktprämie [EUR]': CA1.array_balancinggroups[14].array_gen_income_period,
                 #'Wind offshore AEP costs [EUR]': CA1.array_balancinggroups[15].array_AEP_costs_period,
                 #'Wind offshore Marktprämie [EUR]': CA1.array_balancinggroups[15].array_gen_income_period,
                 #'Wind onshore AEP costs [EUR]': CA1.array_balancinggroups[16].array_AEP_costs_period,
                 #'Wind onshore Marktprämie [EUR]': CA1.array_balancinggroups[16].array_gen_income_period,
                 #'Aluminium AEP costs [EUR]': CA1.array_balancinggroups[17].array_AEP_costs_period,
                 #'Steel AEP costs [EUR]': CA1.array_balancinggroups[18].array_AEP_costs_period,
                 #'Cement AEP costs [EUR]': CA1.array_balancinggroups[19].array_AEP_costs_period,
                 #'Paper AEP costs [EUR]': CA1.array_balancinggroups[20].array_AEP_costs_period,
                 #'Chlorine AEP costs [EUR]': CA1.array_balancinggroups[21].array_AEP_costs_period,
                 #'Gas AEP costs [EUR]': CA1.array_balancinggroups[3].array_AEP_costs_period
            }
    if t_stop > 60*15:
        fileexch.save_period_data(scenario=scenario,
                                    save_file_name=savefilename_period,
                                    save_dict=save_dict,
                                    t_step=t_step,
                                    t_isp=t_isp,
                                    t_stop=t_stop)
        print('Simulation results for every ISP were saved in file', savefilename_period)

    save_dict = {'time [s]': t_vector,
                 'f [Hz]': SZ.array_f,
                 'f_delta [Hz]': SZ.array_f_delta,
                 'delta P [MW]': SZ.array_delta_P,
                 'FRCE [MW]': CA1.array_FRCE,
                 'aFRR FRCE (open loop) [MW]': CA1.array_FRCE_ol,
                 'FCR P [MW]': CA1.array_FCR_P,
                 'aFRR P [MW]': CA1.array_aFRR_P,
                 'mFRR P [MW]': CA1.array_mFRR_P,
                 'SB P [MW]': CA1.array_sb_P,
                 'insufficient pos. aFRR': CA1.array_aFRR_pos_insuf,
                 'insufficient neg. aFRR': CA1.array_aFRR_neg_insuf,
                 'insufficient pos. mFRR': CA1.array_mFRR_pos_insuf,
                 'insufficient neg. mFRR': CA1.array_mFRR_neg_insuf,
                 'AEP [EUR/MWh]': CA1.array_AEP,
            #    'Solar Power [MW]': CA1.array_balancinggroups[14].array_sb_P,
            #    'Wind offshore Power [MW]': CA1.array_balancinggroups[15].array_sb_P,
            #    'Wind onshore Power [MW]': CA1.array_balancinggroups[16].array_sb_P,
            #    'Aluminium Power [MW]': CA1.array_balancinggroups[17].array_sb_P,
            #    'Steel Power [MW]': CA1.array_balancinggroups[18].array_sb_P,
            #    'Cement Power [MW]': CA1.array_balancinggroups[19].array_sb_P,
            #    'Paper Power [MW]': CA1.array_balancinggroups[20].array_sb_P,
            #    'Chlorine Power [MW]': CA1.array_balancinggroups[21].array_sb_P,
            #    'Gas Power [MW]': CA1.array_balancinggroups[3].array_sb_P
                }
    
    fileexch.save_t_step_data(scenario=scenario,
                              save_file_name=savefilename_all,
                              save_dict=save_dict,
                              t_step=t_step,
                              t_isp=t_isp,
                              t_stop=t_stop)

    print('Simulation results for all t_step were saved in file', savefilename_all)

    plt.figure(1)
    plt.plot(t_vector, SZ.array_f)
    plt.title(SZ.name)
    plt.grid()
    #plt.ylim(49.8, 50.2)
    plt.xlabel('time / s')
    plt.ylabel('Frequency / Hz')
    
    
    array_delta_P = [a-b for a, b in zip(CA1.array_gen_P, CA1.array_gen_P_schedule)]
    array_delta_P_load_gen = [a-b for a, b in zip(CA1.array_gen_P, CA1.array_load_P)]

    plt.figure(2)
    plt.plot(t_vector, CA1.array_gen_P,
             t_vector, CA1.array_gen_P_schedule,
             t_vector, CA1.array_load_P,
             #t_vector, CA1.array_load_P_schedule,             
             t_vector, array_delta_P_load_gen,
             t_vector, array_delta_P)
             #t_vector, CA1.array_imba_P_ph,
             #t_vector, CA1.array_imba_P_sc)
    plt.title('Scheduled and generated power')
    plt.grid()
    plt.xlabel('time / s')
    plt.ylabel('Power / MW')
    plt.legend(['P_gen','P_gen_sc','P_load', 'delta_P_ph (gen-load)', 'delta_P_schedule (gen-gen_sc)']) 

    plt.figure(3)
    plt.plot(t_vector, CA1.array_FRCE,
                t_vector, CA1.array_FCR_P,
                t_vector, CA1.array_aFRR_P,
                t_vector, CA1.array_sb_P)
                #t_vector, SZ.array_delta_P)
                # t_vector, CA1.array_FRCE_cl_pos,
                # t_vector, CA1.array_FRCE_cl_neg,
                # t_vector, CA1.array_aFRR_P_pos,
                # t_vector, CA1.array_aFRR_P_neg)
                #t_vector, CA1.array_mFRR_P_pos,
                #t_vector, CA1.array_mFRR_P_neg)
    plt.title(CA1.name)
    grapfunc.add_vert_lines(plt=plt, period=t_isp, t_stop=t_stop, color='gray', linestyle='dotted', linewidth=0.5)
    grapfunc.add_vert_lines(plt=plt, period=t_mol, t_stop=t_stop, color='black', linestyle='dashed', linewidth=0.5)
    plt.title('LFC activation')
    plt.grid()
    plt.xlabel('time / s')
    plt.ylabel('Power / MW')
    #plt.legend(['FRCE', 'aFRR_P_pos', 'aFRR_P_neg', 'mFRR_P_pos', 'mFRR_P_neg'])
    plt.legend(['Imba_FRCE','P_FCR', 'P_aFRR', 'SB_P'])
   
    plt.show()
else:
    print('\nAttention! The data was not saved due to settings!')



# ------------------------------------------------------------------------------------
# ---SHOW SIMULATION RESULTS IN FIGURES-----------------------------------------------
# ------------------------------------------------------------------------------------

if show_fig:

    if scenario == '02_synth_data//synth_':

        plt.figure(1)
        plt.plot(t_vector, CA1.array_imba_P_sc,
                 t_vector, CA1.array_balancinggroups[0].array_gen_P)
        plt.title(CA1.name)
        plt.grid()
        plt.xlabel('time / s')
        plt.ylabel('Power / MW')
        plt.legend(['Total Imbalance', CA1.array_balancinggroups[0].name])

        plt.figure(2)
        plt.plot(t_vector, CA1.array_FRCE,
                 t_vector, CA1.array_FRCE_ol,
                 t_vector, CA1.array_aFRR_P_pos,
                 t_vector, CA1.array_aFRR_P_neg,
                 t_vector, CA1.array_mFRR_P_pos,
                 t_vector, CA1.array_mFRR_P_neg)
        plt.title(CA1.name)
        grapfunc.add_vert_lines(plt=plt, period=t_isp, t_stop=t_stop, color='gray', linestyle='dotted', linewidth=0.5)
        grapfunc.add_vert_lines(plt=plt, period=t_mol, t_stop=t_stop, color='black', linestyle='dashed', linewidth=0.5)
        plt.legend(['FRCE', 'FRCE_ol', 'aFRR_P_pos', 'aFRR_P_neg', 'mFRR_P_pos', 'mFRR_P_neg'])

        plt.figure(3)
        plt.plot(t_vector, CA1.array_balancinggroups[1].array_gen_P,
                 t_vector, CA1.array_balancinggroups[2].array_gen_P,
                 t_vector, CA1.array_balancinggroups[3].array_gen_P,
                 t_vector, CA1.array_balancinggroups[4].array_gen_P,
                 t_vector, CA1.array_balancinggroups[5].array_gen_P,
                 t_vector, CA1.array_balancinggroups[6].array_gen_P,
                 t_vector, CA1.array_balancinggroups[7].array_gen_P,
                 t_vector, CA1.array_balancinggroups[8].array_gen_P,
                 t_vector, CA1.array_balancinggroups[9].array_gen_P,
                 t_vector, CA1.array_balancinggroups[10].array_gen_P,
                 t_vector, CA1.array_balancinggroups[11].array_gen_P,
                 t_vector, CA1.array_balancinggroups[12].array_gen_P,
                 t_vector, CA1.array_balancinggroups[13].array_gen_P,
                 t_vector, CA1.array_balancinggroups[14].array_gen_P,
                 t_vector, CA1.array_balancinggroups[15].array_gen_P,
                 t_vector, CA1.array_balancinggroups[16].array_gen_P)
        plt.title('Generation')
        grapfunc.add_vert_lines(plt=plt, period=t_isp, t_stop=t_stop, color='gray', linestyle='dotted', linewidth=0.5)
        grapfunc.add_vert_lines(plt=plt, period=t_mol, t_stop=t_stop, color='black', linestyle='dashed', linewidth=0.5)
        plt.legend([CA1.array_balancinggroups[1].name,
                    CA1.array_balancinggroups[2].name,
                    CA1.array_balancinggroups[3].name,
                    CA1.array_balancinggroups[4].name,
                    CA1.array_balancinggroups[5].name,
                    CA1.array_balancinggroups[6].name,
                    CA1.array_balancinggroups[7].name,
                    CA1.array_balancinggroups[8].name,
                    CA1.array_balancinggroups[9].name,
                    CA1.array_balancinggroups[10].name,
                    CA1.array_balancinggroups[11].name,
                    CA1.array_balancinggroups[12].name,
                    CA1.array_balancinggroups[13].name,
                    CA1.array_balancinggroups[14].name,
                    CA1.array_balancinggroups[15].name,
                    CA1.array_balancinggroups[16].name])

        plt.figure(4)
        plt.plot(t_vector, CA1.array_balancinggroups[7].array_load_P)
        plt.title('Consumption')
        grapfunc.add_vert_lines(plt=plt, period=t_isp, t_stop=t_stop, color='gray', linestyle='dotted', linewidth=0.5)
        grapfunc.add_vert_lines(plt=plt, period=t_mol, t_stop=t_stop, color='black', linestyle='dashed', linewidth=0.5)
        plt.legend([CA1.array_balancinggroups[7].name])

        plt.figure(5)
        plt.plot(t_vector, CA1.array_da_prices,
                 t_vector, CA1.array_AEP)
        plt.title('Price signals')
        plt.legend(['DA price', 'AEP'])

        plt.figure(6)
        plt.plot(t_vector, CA1.array_balancinggroups[14].array_sb_P,
                 t_vector, CA1.array_balancinggroups[15].array_sb_P,
                 t_vector, CA1.array_balancinggroups[16].array_sb_P,
                 t_vector, CA1.array_balancinggroups[17].array_sb_P,
                 t_vector, CA1.array_balancinggroups[18].array_sb_P,
                 t_vector, CA1.array_balancinggroups[19].array_sb_P,
                 t_vector, CA1.array_balancinggroups[20].array_sb_P,
                 t_vector, CA1.array_balancinggroups[21].array_sb_P)
        plt.title('Smart Balancing')
        plt.legend([CA1.array_balancinggroups[14].name,
                    CA1.array_balancinggroups[15].name,
                    CA1.array_balancinggroups[16].name,
                    CA1.array_balancinggroups[17].name,
                    CA1.array_balancinggroups[18].name,
                    CA1.array_balancinggroups[19].name,
                    CA1.array_balancinggroups[20].name,
                    CA1.array_balancinggroups[21].name])

        plt.figure(7)
        plt.plot(t_vector, CA1.array_balancinggroups[14].array_gen_income_period,
                 t_vector, CA1.array_balancinggroups[15].array_gen_income_period,
                 t_vector, CA1.array_balancinggroups[16].array_gen_income_period)
        plt.title('Generator income')
        plt.legend([CA1.array_balancinggroups[14].name,
                    CA1.array_balancinggroups[15].name,
                    CA1.array_balancinggroups[16].name])
        
        plt.figure(8)
        plt.plot(t_vector, SZ.array_f)
        plt.title(SZ.name)
        plt.grid()
        plt.xlabel('time / s, all 31 days of Simulation')
        plt.ylabel('Frequency / Hz')


        plt.show()

    else:
        print('\nNo suitable scenario found!')
        pass

else:
    print('\nFigures are turned off.')
