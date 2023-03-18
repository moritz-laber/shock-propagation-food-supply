### -------------- FOOD SUPPLY MODEL --------  ####
#                                                 #
#                                                 #
#     Moritz Laber - 2023                         #
#### ----------------------------------------- ####

### ------------- PARAMETERS ---------------- ###

input_folder = './input/'                  # folder with parameters
simulations =  './complete/'               # folder to write results to
relative_loss = './relative_loss/complete/' # folder to store the relative loss to

c_shock = 'Ukraine'

### --------------- IMPORT ----------------- ###

import pandas as pd
from pandas import IndexSlice as idx

import scipy.io as io
import scipy.sparse as sprs

import numpy as np

import matplotlib.pyplot as plt


### ------------- LOADING DATA -------------- ###

# Load list of country
countries = pd.read_csv(input_folder+'country-index.csv',header=None,names=['c'],sep='\t')
countries = countries['c'].values

# Load list of items
items = pd.read_csv(input_folder+'item-index.csv', header=None, names=['i'],sep='\t')
items = items['i'].values

# Load list of processes
processes = pd.read_csv(input_folder+'process-index.csv',header=None, names=['p'],sep='\t')
processes = processes['p'].values

# Load information on countries
c_frame = pd.read_csv(input_folder+'country-information.csv',index_col=[2])
c_frame.drop(['Unnamed: 0'], inplace=True, axis=1)

# Load the result of the shocked simulation
X = pd.read_csv(simulations+'base.csv', index_col=[0,1], header=[0])

### ---------- PREPARATORY COMPUTATIONS --------------------- ###

# Get a list of all geographical regions from country information
regions = c_frame['region'].unique()[:-1]


### RELATIVE LOSS COMPUTATION ###

XS = pd.read_csv(simulations+c_frame.loc[c_shock,'code']+'.csv', index_col=[0,1], header=[0,1])

XSagg = pd.DataFrame(index=pd.MultiIndex.from_product((regions,items)),columns=['complete'])
Xagg = pd.DataFrame(index=pd.MultiIndex.from_product((regions,items)),columns=['base'])

for r in regions:

    # get countries in a specific region
    r_countries = c_frame[c_frame['region'].eq(r)].index.values
    r_countries = r_countries[r_countries!=c_shock]
    
    # aggregate the amount in the baseline scenario
    Xagg.loc[r,:] = X.loc[idx[r_countries,:],:].sum(axis=0,level='item').values
    
    # aggreggate the amount in shocked scenario
    XSagg.loc[r,:] = XS.loc[idx[r_countries,:],:].sum(axis=0,level='item').values

# Calculate the relative loss
RL = 1 - XSagg.div(Xagg.loc[:,'base'].replace({0:np.nan}),axis=0)
RL.fillna(0,inplace=True)
RL[RL<0] = 0

# Setup a dataframe for the relative loss
RL.columns = pd.MultiIndex.from_product([[c_shock],['complete']])
RL.columns.names = ['c_shock','i_shock']
RL.index.names = ['c_receive','i_receive'] 

# save
RL.to_csv(relative_loss+'RL-'+c_frame.loc[c_shock,'code']+'.csv')
