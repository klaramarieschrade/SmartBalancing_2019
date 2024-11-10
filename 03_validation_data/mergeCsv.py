import pandas as pd

hist_Generation1 = pd.read_csv("01_hist_data/hist_Generation_1.csv 01_hist_data/hist_Generation_2.csv",sep=";",decimal=".")
hist_Generation2 = pd.read_csv("01_hist_data\hist_Generation_2.csv",sep=";",decimal=".")
hist_Generation = pd.concat([hist_Generation1, hist_Generation2], axis=1, sort=False)
hist_Generation.to_csv("01_hist_data\hist_Generation.csv", sep=";", decimal=".", index=False)