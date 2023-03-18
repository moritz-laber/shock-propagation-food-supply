############## FOOD SUPPLY MODEL #############
#
#
#  Moritz Laber - 2023

### PARAMETERS ###

input_folder = './input/'           # folder with parameters
output_folder = './complete/'       # folder to write results to

tau = 10                            # number of iterations

### IMPORT ###

import pandas as pd
from pandas import IndexSlice as idx

import scipy.io as io
import scipy.sparse as sprs

import numpy as np


### LOADING DATA ###

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

# Load initial conditions
vector_x0 = io.mmread(input_folder+'sparse_x0.mtx')
vector_startstock = io.mmread(input_folder+'sparse_startstock.mtx')

# Load model parameters
vector_eta_prod = io.mmread(input_folder+'sparse_eta_prod.mtx')
vector_eta_exp = io.mmread(input_folder+'sparse_eta_exp.mtx')
matrix_nu = io.mmread(input_folder+'sparse_nu.mtx')
matrix_alpha = io.mmread(input_folder+'sparse_alpha.mtx')
matrix_beta = io.mmread(input_folder+'sparse_beta.mtx')
matrix_trade = io.mmread(input_folder+'sparse_trade.mtx')


### PREPARATORY COMPUTATIONS ###

# Counting
Ni = len(items)         # number of items
Np = len(processes)     # number of processes
Nc = len(countries)     # number of countries

# Get a list of all geographical regions from country information
regions = c_frame['region'].unique()[:-1]

# Build (country,item)-index
ci_index = pd.MultiIndex.from_product([countries,items])

# Create a vector of all ones for summation
one_vec = sprs.csr_matrix(np.ones(Nc*Np))
one_vec = one_vec.transpose()

# Turn data into sparse csr-format
x0 = sprs.csr_matrix(vector_x0)                         # initial condition
xstartstock = sprs.csr_matrix(vector_startstock)        # starting stock
eta_prod = sprs.csr_matrix(vector_eta_prod)             # allocation to production
eta_exp = sprs.csr_matrix(vector_eta_exp)               # allocation to trade
alpha = sprs.csr_matrix(matrix_alpha)                   # conversion from input to output
beta = sprs.csr_matrix(matrix_beta)                     # output for non-converting processes
T = sprs.csr_matrix(matrix_trade)                       # fraction sent to each trading partner
nu = sprs.csr_matrix(matrix_nu)                         # fraction allocated to a specific production process

# eliminate zeros from sparse matrices
x0.eliminate_zeros()
xstartstock.eliminate_zeros()
eta_prod.eliminate_zeros()
eta_exp.eliminate_zeros()
alpha.eliminate_zeros()
beta.eliminate_zeros()
T.eliminate_zeros()
nu.eliminate_zeros()

# Determine countries that are producers of specific items
producer = (alpha@one_vec) + (beta@one_vec)
producer = producer.toarray()
producer = producer>0
producer = pd.DataFrame(producer, index=ci_index, columns=['is_producer'])


### SIMULATION: BASELINE ###

# Prepare storage
x = sprs.csr_matrix((Nc*Ni,1))

# Set initial conditions
x = x0                          

# Iterate dynamics
for t in range(0,tau):          

    x = (alpha @ (nu @ (eta_prod.multiply(x))) + (beta @ one_vec))  + T @ (eta_exp.multiply(x))

    if t==0:
        x = x+xstartstock

# Store
xbase = x.toarray()[:,0]
X = pd.DataFrame(xbase,index=ci_index,columns=['base'])
X.index.names = ['area','item']
X.columns.names = ['scenario']

# save
X.to_csv(output_folder+'base.csv')

# output
print('Baseline scenario done.')


### SIMULATION: SHOCK ###

# iteration over all countries that can be shocked
for cit, c_shock in enumerate(countries):

    XS = pd.DataFrame(index=ci_index,columns=pd.MultiIndex.from_product([[c_shock],['complete']]))
    XS.index.names = ['area','item']
    XS.columns.names = ['shock_area','shock_item']

    if np.any([producer.loc[(c_shock,i),'is_producer'] for i in items]):

        # Find the shocked country and item in the index
        shock_id_start = list(ci_index.values).index((c_shock,'Abaca'))
        shock_id_end = list(ci_index.values).index((c_shock,'Yams'))

        # Initialize
        x = sprs.csr_matrix((Nc*Ni,1))
        x = x0

        for t in range(0,tau):

            # Production
            o = (alpha @ (nu @ (eta_prod.multiply(x))) + (beta @ one_vec))
            
            # Start Stock
            if t == 0:
                o = o+xstartstock
            
            # Shock
            o[shock_id_start:shock_id_end] = 0
            
            # Trade
            h =  T @ (eta_exp.multiply(x))
            
            # Summation 
            x = o + h

        # Save last time step
        XS.loc[idx[:,:],(c_shock,'complete')] = x.toarray()[:,0]

    else:

        XS.loc[idx[:,:],(c_shock,'complete')] = xbase

    # Save
    XS.to_csv(output_folder+c_frame.loc[c_shock,'code']+'.csv')

    # Progress
    print(f'Shocked Scenario: {100*cit/len(countries):.2f}%',end='\r')

print(f'Shocked scenario done')