# shock-propagation-food-supply

 This repository contains the code for the paper Laber, Klimek, Bruckner, Yang, Thurner (2022) [*Shock propagation in international multilayer food-production network determines global food availability: the case of the Ukraine war*](https://arxiv.org/abs/2210.01846) .

The script `shock-complete.py` (`shock-individual.py`) simulates a worst case scenario of 100% production loss for all products simultaneously (individually) based on trade, production and usage data from the year 2013 (based on [Bruckner et al. 2019](https://doi.org/10.1021/acs.est.9b03554)).

The files `compute_RL-complete.py` and `compute_RL-individual.py` compute the relative loss with respect to a non-shocked baseline scenario from the output of the respective simulations.