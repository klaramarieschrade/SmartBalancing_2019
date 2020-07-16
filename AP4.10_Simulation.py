# ....................................................................................
# ...GRID SIMULATION SOFTWARE.........................................................
# ....................................................................................
# ...Project:        NEW4.0
# ...Authors:        Julian Franz, Anna Meissner, Felix Roeben, Simon Rindelaub
# ...Institution:    Fraunhofer Institute for Silicon Technologies (ISIT)
# ...Department:     Power Electronics for Renewable Energy Systems
# ....................................................................................
# ...Purpose:        Simulation of various ancillary services in power systems
# ....................................................................................
# ...Version:        1.1
# ...Date:           July 16th 2020
# ....................................................................................

# ------------------------------------------------------------------------------------
# ---IMPORT---------------------------------------------------------------------------
# ------------------------------------------------------------------------------------

import matplotlib.pyplot as plt
import time
import os

# ...Import of project files
import gridelem
import balagrou
import generato
import loadload
import smarbala
import fuzzlogi
import fileexch
import grapfunc
import math



# ------------------------------------------------------------------------------------
# ---DEFINITION OF SIMULATION PARAMETERS----------------------------------------------
# ------------------------------------------------------------------------------------

# !!! File will be overwritten !!!
savefilename_period = 'sim_output_period.csv'       # name of save file, location defined by "scenario"
savefilename_all = 'sim_output_all.csv'             # name of save file, location defined by "scenario"
#scenario = 'Test_data//Test_'
#scenario = 'Feldtest_data//Feldtest_'
scenario = 'WC_data//WC_'
start = 0                                           # simulation time

# ...Set simulation time step in s
t_step = 1
# ...Set simulation discrete time variable
k_now = 0

# ...Activation of simulation functions
smartbalancing = False       # True: values being read from the .csv
save_data = True            # True: write the Simulation data to .csv
show_fig = True             # True: show all figures at the end of the simulation
save_fig = False            # True: figures are saved as .png files at the end of the simulation

# ...Set simulation time settings in seconds
day_count = 0                       # number of the first day...needed for correct MOL access
t_now = 0                           # start of simulation in s
t_day = t_now                       # time of current day in s
t_isp = 900                         # duration of an Imbalance Settlement Period in s
t_mol = 14400                       # time in s, after which the MOL gets updated
t_stop = 604789                     # end of simulation in s
sim_duration = t_stop - t_now + 1

# ...Set simulation time settings in timestamps utc
sim_duration_uct = ['18.11.2019', '25.11.2019', '26.11.2019']

array_bilanzkreise = []

t_vector = []
k_vector = []
os.system("cls")
print('\nInitializing data from CSV files')
start = time.time()



# ------------------------------------------------------------------------------------
# ---INITIALIZATION OF GRID MODEL-----------------------------------------------------
# ------------------------------------------------------------------------------------

# ...read DA prices for specified time range (sim_duration_uct) from csv
list_da_prices = fileexch.get_da_price_data(sim_duration_uct)
i = 0
t_da = 0.0
array_da_prices = []
# ...write prices into array with one value per time step of the simulation
while t_da <= t_stop:
    array_da_prices.append(list_da_prices.iloc[math.floor(i/3600)][0])
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
                           aFRR_T=170.0,
                           aFRR_beta=0.1,
                           aFRR_delay=30.0,
                           mFRR_trigger=0.6,
                           mFRR_target=0.4,
                           mFRR_time=300.0,
                           sb_delay=0.0)
SZ.array_subordinates.append(CA1)

CA1.array_da_prices = array_da_prices

# ...Initialization of Balancing Groups
BG0 = balagrou.BalancingGroup(name='Rest von Deutschland',
                              read=False,
                              smart=smartbalancing)
CA1.array_balancinggroups.append(BG0)

# read balance Groups from csv and add to Control area
array_bilanzkreise = fileexch.get_balancing_groups(scenario, smartbalancing, sim_duration)

for i in range(len(array_bilanzkreise)):
    CA1.array_balancinggroups.append(array_bilanzkreise[i])

# compare BG-name and Asset-BG and append to the right BG, if SB is turned on!
if smartbalancing:

    # Creating smart balancing assets from .csv files and assigning them to the respective balancing groups
    array_assets = fileexch.get_assets(scenario)
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

CA1.array_aFRR_molpos, CA1.array_aFRR_molneg = fileexch.read_afrr_mol(scenario, 0, 0, 0)
CA1.array_mFRR_molpos, CA1.array_mFRR_molneg = fileexch.read_mfrr_mol(scenario, 0, 0, 0)

print('\nInitialization Done! It took %.5f seconds' % (time.time() - start))

# The time series for load_P of the FlexLoad "Aurubis_E_Kessel" does not get read from the .csv file...
# ...and its load gets set to a default value of zero
# if True:
#     CA1.array_balancinggroups[3].read = False
#     CA1.array_balancinggroups[3].array_load_P_schedule = []
#     CA1.array_balancinggroups[3].load_P_schedule = 0.0
#     for i in CA1.array_balancinggroups[3].array_loads:
#         if i.name == 'Aurubis_E_Kessel':
#             i.read = False
#             i.array_load_P = []
#             i.array_load_P_schedule = []
#             i.load_P = 0.0
#             i.load_P_schedule = 0.0
# else:
#     pass



# ------------------------------------------------------------------------------------
# ---SIMULATION-----------------------------------------------------------------------
# ------------------------------------------------------------------------------------

print('\n#-----------Simulation Start-----------#')
print('#-----------Day %d-----------#' % day_count)

start = time.time()

# ...Initialization of FCR and aFRR parameters
SZ.fcr_init()
SZ.afrr_init(t_step=t_step)

t_vector.append(t_now)
k_vector.append(k_now)

SZ.readarray(k_now)
SZ.gen_calc()
SZ.load_calc()
SZ.schedule_init()
SZ.gen_schedule_calc()
SZ.load_schedule_calc()
SZ.imba_calc()
SZ.f_calc()
SZ.fcr_calc()
SZ.afrr_calc(k_now=k_now, t_now=t_now, t_step=t_step, t_isp=t_isp)
SZ.mfrr_calc(t_now=t_now, t_step=t_step, t_isp=t_isp)
SZ.energy_costs_calc(k_now=k_now, t_now=t_now, t_step=t_step, t_isp=t_isp)
SZ.write_results()

day_count += 1
print('#-----------Day %d-----------#' % day_count)

# ...Simulation of every time step
while t_now < t_stop:

    if t_day >= 86400:
        day_count += 1
        print('#-----------Day %d-----------#' % day_count)
        t_day = 0.0

    if (t_now % t_mol) == 0:
        print('Reached MOL update on day', day_count,'at', int((t_day / 3600)) ,'o´clock')
        (CA1.array_aFRR_molpos, CA1.array_aFRR_molneg) = fileexch.read_afrr_mol(scenario, t_day, t_mol, day_count)
        (CA1.array_mFRR_molpos, CA1.array_mFRR_molneg) = fileexch.read_mfrr_mol(scenario, t_day, t_mol, day_count)
        SZ.mol_update()

    t_now += t_step
    t_day += t_step
    t_vector.append(t_now)
    k_now += 1
    k_vector.append(k_now)

    SZ.readarray(k_now)
    SZ.gen_calc()
    SZ.load_calc()
    SZ.gen_schedule_calc()
    SZ.load_schedule_calc()
    SZ.imba_calc()
    SZ.f_calc()
    SZ.fcr_calc()
    SZ.afrr_calc(k_now=k_now, t_now=t_now, t_step=t_step, t_isp=t_isp)
    SZ.mfrr_calc(t_now=t_now, t_step=t_step, t_isp=t_isp)
    SZ.energy_costs_calc(k_now=k_now, t_now=t_now, t_step=t_step, t_isp=t_isp)
    SZ.write_results()

print('#-----------Simulation Done-----------#\n')
print('Simulation time: %.5f seconds\n' % (time.time() - start))



# ------------------------------------------------------------------------------------
# ---SAVE SIMULATION RESULTS----------------------------------------------------------
# ------------------------------------------------------------------------------------

if save_data:
    save_dict = {'time [s]': t_vector,
                 'GER pos. energy aFRR [MWh]': CA1.array_aFRR_E_pos_period,
                 'GER neg. energy aFRR [MWh]': CA1.array_aFRR_E_neg_period,
                 'GER pos. aFRR costs [EUR]': CA1.array_aFRR_costs_pos_period,
                 'GER neg. aFRR costs [EUR]': CA1.array_aFRR_costs_neg_period,
                 'GER pos. energy mFRR [MWh]': CA1.array_mFRR_E_pos_period,
                 'GER neg. energy mFRR [MWh]': CA1.array_mFRR_E_neg_period,
                 'GER pos. mFRR costs [EUR]': CA1.array_mFRR_costs_pos_period,
                 'GER neg. mFRR costs [EUR]': CA1.array_mFRR_costs_neg_period,
                 'GER AEP [EUR/MWh]': CA1.array_AEP
                }
    fileexch.save_period_data(scenario=scenario,
                              save_file_name=savefilename_period,
                              save_dict=save_dict,
                              t_step=t_step,
                              t_isp=t_isp,
                              t_stop=t_stop)
    print('Simulation results for every ISP were saved in file', savefilename_period)

    save_dict = {'time [s]': t_vector,
                 'open loop FRCE [MW]': CA1.array_FRCE_ol,
                 'aFRR P [MW]': CA1.array_aFRR_P,
                 'mFRR P [MW]': CA1.array_mFRR_P,
                 'AEP [EUR/MWh]': CA1.array_AEP
                }
    fileexch.save_t_step_data(scenario=scenario,
                              save_file_name=savefilename_all,
                              save_dict=save_dict,
                              t_step=t_step,
                              t_isp=t_isp,
                              t_stop=t_stop)
    print('Simulation results for all t_step were saved in file', savefilename_all)
else:
    print('\nAttention! The data was not saved due to settings!')



# ------------------------------------------------------------------------------------
# ---SHOW SIMULATION RESULTS IN FIGURES-----------------------------------------------
# ------------------------------------------------------------------------------------

if show_fig:

    if scenario == 'Feldtest_data//Feldtest_':

        plt.figure(1)
        plt.plot(t_vector, CA1.array_imba_P_sc,
                 t_vector, CA1.array_balancinggroups[7].array_gen_P)
        plt.title(CA1.name)
        plt.grid()
        plt.xlabel('time / s')
        plt.ylabel('Power / MW')
        plt.legend(['Total Imbalance', CA1.array_balancinggroups[7].name])
        if save_fig:
            plt.savefig('Bilder//Feldtest1.png', bbox_inches='tight')
        else:
            pass

        plt.figure(2)
        plt.plot(t_vector, CA1.array_FRCE_sb,
                 t_vector, CA1.array_balancinggroups[1].array_sb_P,
                 t_vector, CA1.array_balancinggroups[2].array_sb_P,
                 t_vector, CA1.array_balancinggroups[3].array_sb_P,
                 t_vector, CA1.array_balancinggroups[4].array_sb_P,
                 t_vector, CA1.array_balancinggroups[5].array_sb_P)
        plt.title(CA1.name)
        plt.grid()
        plt.legend(['FRCE_sb',
                    CA1.array_balancinggroups[1].name,
                    CA1.array_balancinggroups[2].name,
                    CA1.array_balancinggroups[3].name,
                    CA1.array_balancinggroups[4].name,
                    CA1.array_balancinggroups[5].name])
        if save_fig:
            plt.savefig('Bilder//Feldtest3.png', bbox_inches='tight')
        else:
            pass

        plt.figure(3)
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
        if save_fig:
            plt.savefig('Bilder//Feldtest3.png', bbox_inches='tight')
        else:
            pass

    elif scenario == 'WC_data//WC_':

        plt.figure(1)
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
        if save_fig:
            plt.savefig('Bilder//Feldtest3.png', bbox_inches='tight')
        else:
            pass

        plt.show()

    else:
        print('\nNo suitable scenario found!')
        pass

else:
    print('\nFigures are turned off.')