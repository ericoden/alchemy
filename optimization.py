import pandas as pd
import gurobipy as gp
from gurobipy import GRB
from mip import Model, xsum, maximize, INTEGER
import scipy.sparse as sp
import numpy as np
from os.path import exists
from cost_calculation import calculate_costs
brews_df = pd.read_pickle('data/brews_with_costs_45_3_0_0_0_0.pkl')
ingredients_df = pd.read_pickle('data/ingredients.pkl')
brews = list(brews_df.name)
ingredients = list(ingredients_df.name)

B = [i for i in range(len(brews_df))]
I = [i for i in range(len(ingredients_df))]
# randomly generate inventory
z = np.random.poisson(lam=1, size=len(I))

def create_constraint_matrix():
    A = [[] for b in B]
    for b in B:
        brew_ingredients = brews_df.loc[b][['first_ingredient','second_ingredient','third_ingredient']]
        for ingredient in brew_ingredients:
            if ingredient != 'NA':
                i = ingredients.index(ingredient)
                A[b].append(i)
    with open('data/constraint_matrix.txt', 'w') as f:
        for row in A:
            for col in row:
                f.write('%s ' % col)
            f.write('\n')


def read_constraint_matrix():
    A = []
    with open('data/constraint_matrix.txt', 'r') as f:
        A = [list(map(int, line.split())) for line in f]
    return A


def create_model(inventory, stats):
    stat_string = f'{stats[0]}_{stats[1]}_{stats[2]}_{stats[3]}_{stats[4]}_{stats[5]}'
    if exists('data/brews_with_costs_'+stat_string+'.pkl'):
        print("Brew costs already calculated!")
    else:
        calculate_costs(stats[0], stats[1], stats[2], stats[3], stats[4], stats[5])
    brews_df = pd.read_pickle('data/brews_with_costs_'+stat_string+'.pkl')

    c = np.array(brews_df['value'])

    A = read_constraint_matrix()
    l = gp.tuplelist()
    brew_ingredient_pairs = []
    for b in B:
        for i in A[b]:
            l.append((b,i))

    brew_ingredient_pairs = []

    K = 0 # number of brew-ingredient pairs
    for b in B:
        for i in A[b]:
            brew_ingredient_pairs.append([b,i,K])
            K += 1
    m = Model('alchemy-mip')
    x = [m.add_var() for k in range(K)]
    y = [m.add_var(var_type=INTEGER) for b in B]
    
    for pair in brew_ingredient_pairs:
        b = pair[0]
        i = pair[1]
        k = pair[2]
        m += y[b] <= x[k]

    for i in I:
        
        m += xsum(x[pair[2]] for pair in brew_ingredient_pairs if pair[1]==i) <= inventory[i]

    m.objective = maximize(xsum(c[b] * y[b] for b in B))

    m.optimize()
    print("mip objective:", m.objective_value)
    optimal_brews = [b for b in B if y[b].x > 0.5]
    
    #m = gp.Model('alchemy')
    #x = m.addVars(l, vtype=GRB.CONTINUOUS, name='x')
    #y = m.addVars(B, vtype=GRB.INTEGER, name='y')
    #m.addConstrs((y[b] <= x[b,i] for (b,i) in l))
    #m.setParam('OUTPUT_FLAG',False)
    #m.addConstrs((x.sum('*', i) <= inventory[i] for i in range(len(I))))
    #m.setObjective(gp.quicksum(c[b]*y[b] for b in B), GRB.MAXIMIZE)
    #m.optimize()
    #print("Gurobi objective:", m.objVal)
    #optimal_brews = [b for b in B if y[b].x > 0.5]


    optimal_df = brews_df.loc[optimal_brews]
    optimal_df['count'] = [int(y[b].x) for b in B if y[b].x > 0.5]
    optimal_df.sort_values(by=['value'], ascending=False)
    optimal_df = optimal_df[['name', 'count', 'value', 'first_ingredient', 'second_ingredient', 'third_ingredient', 'descriptions']]
    optimal_df = optimal_df.sort_values(by='value', ascending=False)
    




    
    return [m.objective_value, optimal_df]

if __name__ == "__main__":
    inventory = [np.random.randint(0,10) for i in range(len(ingredients))]
    create_model(inventory, [10,0,0,0,0,0])
