# -*- coding: utf-8 -*-
"""
Created on Thu Oct 26 11:19:59 2023

@author: roksa
"""

import pulp

# Constants
years = list(range(2025, 2046, 5))
units = ['power_plant', 'hydrogen_plant', 'gas_plant']
fuels = ['electricity', 'green_hydrogen', 'synthetic_gas']
COP = {
    'electricity': 2.5,
    'green_hydrogen': 0.90,
    'synthetic_gas': 0.85
}
C_op = {'power_plant': 300, 'hydrogen_plant': 1000, 'gas_plant': 900}
C_inv = {'power_plant': 1500, 'hydrogen_plant': 1800, 'gas_plant': 1700}
C_f = {'electricity': 9844, 'green_hydrogen': 17100, 'synthetic_gas': 20000}
X_max = {'power_plant': 168, 'hydrogen_plant': 150, 'gas_plant': 125}
x = {'power_plant': 10, 'hydrogen_plant': 12, 'gas_plant': 9}
CF = 20

best_objective = float('inf')
best_fuel_combination = []

for y in years:
    electricity_contribution = (y - 2025) // 5 * 0.20
    other_fuel_contribution = 1 - electricity_contribution

    for other_fuel in [f for f in fuels if f != 'electricity']:
        prb = pulp.LpProblem(f"Optimization_for_{y}_{other_fuel}", pulp.LpMinimize)

        # Variables
        G = pulp.LpVariable.dicts("Generation", [(t, u) for t in years for u in units], 0)  # Since it's every 5 years, no need for t,u combination
        X = pulp.LpVariable.dicts("Installed_Capacity", units, 0)
        F = pulp.LpVariable.dicts("Fuel_Consumption", fuels, 0)

        # Objective Function
        prb += pulp.lpSum(
            [C_op[u] * G[t, u] for t in years for u in units] + 
            [C_inv[u] * X[u] for u in units] +
            [C_f[f] * F[f] * COP[f] for f in fuels]
        ), "TotalCost"

        # Constraints
        for t in years:
            prb += G[t, 'power_plant'] * COP['electricity'] == 100 * electricity_contribution
            prb += G[t, units[fuels.index(other_fuel)]] * COP[other_fuel] == 100 * other_fuel_contribution
        

        for u in units:
            prb += G[t, u] <= X[u] * CF
            prb += X[u] <= X_max[u]
            prb += X[u] <= x[u]
            prb += x[u] <= X_max[u]

        prb += pulp.lpSum([F[f] for f in fuels if f != 'electricity']) == 100 * other_fuel_contribution / COP[other_fuel]
        prb += F['electricity'] == 100 * electricity_contribution / COP['electricity']

        prb.solve(pulp.GUROBI())

        if pulp.value(prb.objective) < best_objective:
            best_objective = pulp.value(prb.objective)
            best_fuel_combination = ['electricity', other_fuel]

print(f"The optimal fuel combination for minimizing cost is: {best_fuel_combination}")
print(f"Optimal Value of Z when using {best_fuel_combination}:", best_objective)
# Extracting the optimal values of decision variables
optimal_fuel_values = {(t, u): G[t, u].varValue for t in years for u in units }
print(optimal_fuel_values)

# Calculating the total heat produced by the two cheapest fuels
total_heat_produced = 0
for unit in units:
    heat_produced = 0
    for fuel in best_fuel_combination:
        for year in years:
            heat_produced += COP[fuel] * optimal_fuel_values[year, unit]
            total_heat_produced += heat_produced
    print(f"Heat Produced by {unit}: {heat_produced}")

# Displaying the results
print("Cheapest Fuels:", best_fuel_combination)
print("Total Heat Produced by the Two Cheapest Fuels:", total_heat_produced)
