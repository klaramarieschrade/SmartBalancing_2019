import pandas as pd
import numpy as np
import datetime



historic_ACE = False   # False: overwrite historic ACE with synthetic ACE

marginal_pricing = False  #False: higher ACE applies for pay-as-bid

synth_Generation1 = pd.read_csv("01_hist_data/hist_Generation_1.csv",sep=";",decimal=".")
synth_Generation2 = pd.read_csv("01_hist_data/hist_Generation_2.csv",sep=";",decimal=".")
synth_Generation = pd.concat([synth_Generation1, synth_Generation2], axis=1, sort=False)



if historic_ACE:

    # save synth_Generation.csv file for simulation
    synth_Generation.to_csv("02_synth_data/synth_Generation.csv", sep=";", decimal=".", index=False)

else: #overwrite historic ACE with synthetic ACE (sACE)
    sACE = pd.DataFrame()
    # The number of minutes in a year
    num_min = 525601

    # Seeding to obtain a reproductible dataset
    np.random.seed(0)

    # create ACE with rand40 (value between -40 and 40)
    sACE = pd.DataFrame(np.random.randint(-40, 40, num_min),
                       index=pd.date_range(start=pd.to_datetime('2019-01-01'),
                                           periods=num_min, freq='Min'), columns=["rand40"])

    # create ACE with 1000 MW sin (T = 12.1 h)
    start = datetime.datetime(year=2019,
                              month=1,
                              day=1,
                              minute=0,
                              second=0)
    sACE['min'] = (sACE.index - start).seconds / 60

    if marginal_pricing:
        sACE['1000sin'] = 1000 * np.sin(sACE['min'] / (12.1 * 60 / (2 * 3.14)))
    else:
        sACE['1000sin'] = 1100 * np.sin(sACE['min'] / (12.1 * 60 / (2 * 3.14)))
    #sACE['events'] = #12.06.2019 10 - 16 Uhr

    # add ACE parameters, drop
    sACE['ACE'] = sACE['rand40'] + sACE['1000sin']
    sACE = sACE.drop(columns=['rand40', 'min', '1000sin'])
    synth_Generation.index = pd.date_range(start='00:00 01.01.2019', end='00:00 01.01.2020', freq='1 min')
    #overwrite historic ACE with synthetic ACE
    synth_Generation['FRCE Gen'] = sACE['ACE']

    #save new WC Generation file (without index) for simulation
    synth_Generation['00:00 01.01.2019':'00:00 02.01.2019'].to_csv("02_synth_data/synth_Generation.csv",sep=";",decimal=".",index=False)