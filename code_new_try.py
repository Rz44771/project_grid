# -*- coding: utf-8 -*-
"""
Created on Tue Jan 30 15:51:45 2024

@author: roksa
"""

import pulp
from itertools import permutations
#from itertools import product

# Constants
years = list(range(2025, 2046, 5))  # considering the years from 2025 to 2045 with 5 years leap
units = ['power_plant', 'hydrogen_plant',
         'gas_plant']  # here heat pump and gas boiler is used to produce heat in power and h and g plant respectively
fuels = ['electricity', 'green_hydrogen',
         'synthetic_gas']  # these are the input fuels for heat pumps and gas boilers respectively
COP = {
    'electricity': 2.5,  # cop of heat pumps
    'green_hydrogen': 0.90,  # cop of gas boilers
    'synthetic_gas': 0.90
}  # coefficient of performance of the fuels (fuel efficiency)

C_op = {'power_plant': 3, 'hydrogen_plant': 10,
        'gas_plant': 10}  # operational cost of heat pump, gas boiler, unit in euro
C_inv = {'power_plant': 15, 'hydrogen_plant': 18,
         'gas_plant': 18}  # investment cost of heat pump, gas boiler, unit in euro
C_f = {'electricity': 98.44, 'green_hydrogen': 171, 'synthetic_gas': 200}  # cost of fuels, unit in euro
X = {'power_plant': 1000000, 'hydrogen_plant': 100000,
     'gas_plant': 40000}  # already installed capacity (current produced heat in 2025 by each unit u ), unit in MWh
X_max = {'power_plant': 10000000, 'hydrogen_plant': 800000,
         'gas_plant': 200000}  # maximum allowed capacity (maximum amount of heat produced by each unit u) over the whole time period, unit in MWh
x = {'power_plant': 1500000, 'hydrogen_plant': 140000,
     'gas_plant': 45000}  # amount of capacity of unit u increased every 5 years, unit in MWh
# so every 5 years these values of x will be added to current value
# of X of that particular year

# D[2025]  D[2030]    D[2035]  D[2040]  D[2045]
D = [11940000, 10830000, 10000000, 9440000,
     8880000]  # heat demands for 2025,2030,2035,2040,2045 resepectively, unit in MWh
best_objective = float('inf')
best_fuels = None

# ... (Your imports and constant definitions)
# Decision Variables - value will start from 0
G = pulp.LpVariable.dicts("Generation", [(t, u) for t in years for u in units],0)  # G represents the amount of energy (heat) produced by each unit u
CAP = pulp.LpVariable.dicts("Installed_Capacity", [(t, u) for t in years for u in units],0)  # X represents the installed capacity (how much heat is already produced by each unit u)
F = pulp.LpVariable.dicts("Fuel_Consumption", [(t, f) for t in years for f in fuels],0)  # F represents amount of fuel needed (given as input to each unit u)to operate

# Integer Linear Programming
for i, t in enumerate(years):
    for u, f in zip(units, fuels):
        for fuel_combination in permutations(fuels, 2):  # optimization for best fuels to find out which fuel/ more than one fuels is best suited to get the minimum value Z
            prb = pulp.LpProblem(f"Optimization_for_{fuel_combination[0]}_{fuel_combination[1]}",
                                         pulp.LpMinimize)

            # Objective Function - minimize the total system cost
            prb += pulp.lpSum([C_op[u] * G[t, u] for t in years for u in units] +
                                      [C_inv[u] * CAP[t, u] for t in years for u in units] +
                                      [C_f[f] * F[t, f] for t in years for f in fuels]), "TotalCost"

            # Balance Equation - total generation of heat by each unit will be equal to 20% of demand of that pa
            prb += G[t, 'power_plant'] + G[t, 'hydrogen_plant'] + G[t, 'gas_plant'] == (0.2*(i+1)) * D[i]

            # Constraints
            # Capacity Constraint - The generated heat from each unit does not exceed the already installed capacity for that unit
            prb += G[t, u] <= CAP[t, u]

            # Capacity Boundary Constraint - Increment of X[u] by x[u] every 5 years
            prb += CAP[t, u] <= CAP[t, u] + X[u]
            prb += CAP[t, u] + X[u] <= X_max[u]


            # print(G[t, 'power_plant'])
            # Fuel Consumption Constraint - Fuel consumption is linked to the generation by the fuel efficiency
            prb += F[t, 'electricity'] == pulp.LpAffineExpression(
                        [(G[t, 'power_plant'], 1 / COP['electricity'])])
            prb += F[t, 'green_hydrogen'] == pulp.LpAffineExpression(
                        [(G[t, 'hydrogen_plant'], 1 / COP['green_hydrogen'])])
            prb += F[t, 'synthetic_gas'] == pulp.LpAffineExpression(
                        [(G[t, 'gas_plant'], 1 / COP['synthetic_gas'])])

            # Non-negative Constraint - decision variables are non-negative
            prb += G[t, u] >= 0
            prb += CAP[t, u] >= 0
            prb += F[t, f] >= 0
            
            #prb += G[t, 'power_plant'] > 0
            #prb += G[t, 'hydrogen_plant'] > 0

            # Optimization
            prb.solve(pulp.GUROBI())
            
            
        #if prb.status == pulp.LpStatusOptimal:
            for t in years:
                G_power = pulp.value(G[t, 'power_plant'])
                G_hydrogen = pulp.value(G[t, 'hydrogen_plant'])
                G_sgas = pulp.value(G[t, 'gas_plant'])
                
                print(f"At year {t}:")
                print(f"  Heat produced by power plant: {G_power} MWh")
                print(f"  Heat produced by hydrogen plant: {G_hydrogen} MWh")
                print(f"  Heat produced by gas plant: {G_sgas} MWh")
            
            
           

            # Debugging Print Statements
            # print(f"Status: {pulp.LpStatus[prb.status]}")
            # print(f"Objective Value: {pulp.value(prb.objective)}")

            if prb.status == pulp.LpStatusOptimal:
                if pulp.value(prb.objective) < best_objective:
                    best_objective = pulp.value(prb.objective)
                    best_fuels = fuel_combination

# Print the results
print(f"The optimal fuel combination for minimizing cost is: {best_fuels}")
print(f"Optimal Value of Z when using {best_fuels}:", best_objective)
#for t in years:
    #print(f"The optimal values for G[t, 'power_plant'] at year {t}: {G_power}") 
    #print(f"The optimal values for G[t, 'hydrogen_plant'] at year {t}: {G_hydrogen}")
    #print(f"The optimal values for G[t, 'gas_plant'] at year {t}: {G_sgas}")
