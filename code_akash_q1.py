import pulp
from itertools import permutations

# ============================= Constants ==========================================================
# Considering the years from 2025 to 2045 with 5 years leap
years = list(range(2025, 2046, 5))

# Here heat pump and gas boiler is used to produce heat in power and h and g plant respectively
units = [
    'power_plant',
    'hydrogen_plant',
    'gas_plant'
]

# These are the input fuels for heat pumps and gas boilers respectively
fuels = [
    'electricity',
    'green_hydrogen',
    'synthetic_gas'
]

# Coefficient of performance of the fuels (fuel efficiency)
COP = {
    'electricity': 2.5,  # cop of heat pumps
    'green_hydrogen': 0.90,  # cop of gas boilers
    'synthetic_gas': 0.90
}

# Operational cost of heat pump, gas boiler, unit in euro
C_op = {
    'power_plant': 3,
    'hydrogen_plant': 10,
    'gas_plant': 10
}

# Investment cost of heat pump, gas boiler, unit in euro
C_inv = {
    'power_plant': 15,
    'hydrogen_plant': 18,
    'gas_plant': 18
}

# Cost of fuels, unit in euro
C_f = {
    'electricity': 98.44,
    'green_hydrogen': 171,
    'synthetic_gas': 200
}

# Already installed capacity (current produced heat in 2025 by each unit u ), unit in MWh
X = {
    'power_plant': 1000000,
    'hydrogen_plant': 100000,
    'gas_plant': 40000
}

# maximum allowed capacity (maximum amount of heat produced by each unit u) over the whole time period, unit in MWh
X_max = {
    'power_plant': 10000000,
    'hydrogen_plant': 800000,
    'gas_plant': 200000
}

# amount of capacity of unit u increased every 5 years, unit in MWh
# so every 5 years these values of x will be added to current value
# of X of that particular year
x = {
    'power_plant': 1500000,
    'hydrogen_plant': 140000,
    'gas_plant': 45000
}

# D[2025]  D[2030]    D[2035]  D[2040]  D[2045]
# heat demands for 2025,2030,2035,2040,2045 resepectively, unit in MWh
D = [
    11940000,
    10830000,
    10000000,
    9440000,
    8880000
]
best_objective = float('inf')
best_fuels = None

# Lp Problem for Cost Optimization
prb = pulp.LpProblem(f"Optimization_for_", pulp.LpMinimize)

# ============================== Decision Variables - value will start from 0 ===============================
# G represents the amount of energy (heat) produced by each unit u
G = pulp.LpVariable.dicts("Generation",
                          [(t, u) for t in years for u in units],
                          lowBound=0,
                          cat='Continuous')

# CAP represents the installed capacity (how much heat is already produced by each unit u)
CAP = pulp.LpVariable.dicts("Installed_Capacity", [(t, u) for t in years for u in units],
                            lowBound=0,
                            cat='Continuous')

# F represents amount of fuel needed (given as input to each unit u)to operate
F = pulp.LpVariable.dicts("Fuel_Consumption", [(t, f) for t in years for f in fuels],
                          lowBound=0,
                          cat='Continuous')

# Objective Function - minimize the total system cost
prb += pulp.lpSum([C_op[u] * G[t, u] for t in years for u in units]
                  + [C_inv[u] * CAP[t, u] for t in years for u in units]
                  + [C_f[f] * F[t, f] for t in years for f in fuels]), "TotalCost"


# Constraints
for year in years:
    # Constraint 1 - Balance Equation: Total generation of heat by each unit is equal to 20% of demand
    prb += pulp.lpSum(G[i, j] for i in years for j in units) == 0.2 * D[years.index(year)]

    for unit in units:
        # Constraint 2: Generated heat does not exceed already installed capacity
        prb += G[year, unit] <= CAP[year, unit]

        # Constraint 3 - Capacity Boundary Constraint: Increment of X[u] by x[u] every 5 years
        prb += CAP[year, unit] <= CAP[year, unit] + X[unit]
        prb += CAP[year, unit] + X[unit] <= X_max[unit]

        # Fuel Consumption Constraint - Fuel consumption is linked to the generation by the fuel efficiency
        prb += F[year, 'electricity'] == pulp.LpAffineExpression([(G[year, 'power_plant'], 1 / COP['electricity'])])
        prb += F[year, 'green_hydrogen'] == pulp.LpAffineExpression([(G[year, 'hydrogen_plant'], 1 / COP['green_hydrogen'])])
        prb += F[year, 'synthetic_gas'] == pulp.LpAffineExpression([(G[year, 'gas_plant'], 1 / COP['synthetic_gas'])])

        # Non-negative Constraint - decision variables are non-negative
        prb += G[year, unit] >= 0
        prb += CAP[year, unit] >= 0

        for fuel in fuels:
            prb += F[year, fuel] >= 0

            prb.solve(pulp.GUROBI())

            if prb.status == pulp.LpStatusOptimal:
                if pulp.value(prb.objective) < best_objective:
                    best_objective = pulp.value(prb.objective)
                    best_fuel = fuel


# Optimization
# prb.solve(pulp.GUROBI())

# Displaying the results

print(f"The optimal fuel combination for minimizing cost is: {best_fuels}")
print(f"Optimal Value of Z when using {best_fuels}:", best_objective)

print("Optimal solution:")
for v in prb.variables():
    print(f"{v.name}: {v.varValue}")

print("=================Minimum Costs===========================================================")
# Extracting the optimal values of decision variables
optimal_fuel_values = {(unit, year): G[year, unit].varValue for year in years for unit in units }

# Calculating the total cost to operate each heat plant
total_cost_per_unit = {unit: sum(C_op[unit] * x[unit] + C_inv[unit] * (X[unit] + x[unit] * (year - 2025)) + C_f[fuel] * COP[fuel] for fuel in fuels for year in years) for unit in units}

for unit, cost in total_cost_per_unit.items():
    print(f"Minimum cost to operate {unit}: {cost} euro")