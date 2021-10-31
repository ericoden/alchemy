import pandas as pd
import gurobipy as gp
from gurobipy import GRB
import scipy.sparse as sp
import numpy as np

brews_df = pd.read_pickle('data/brews_with_costs.pkl')
ingredients_df = pd.read_pickle('data/ingredients.pkl')
brews = list(brews_df.name)
ingredients = list(ingredients_df.name)

B = [i for i in range(len(brews_df))]
I = [i for i in range(len(ingredients_df))]
c = np.array(brews_df['value'])
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


def create_model(inventory):
    A = read_constraint_matrix()
    l = gp.tuplelist()
    for b in B:
        for i in A[b]:
            l.append((b,i))
            
    m = gp.Model('alchemy')
    x = m.addVars(l, vtype=GRB.CONTINUOUS, name='x')
    y = m.addVars(B, vtype=GRB.INTEGER, name='y')
    m.addConstrs((y[b] <= x[b,i] for (b,i) in l))
    m.setParam('OUTPUT_FLAG',False)
    m.setObjective(gp.quicksum(c[b]*y[b] for b in B), GRB.MAXIMIZE)

    m.addConstrs((x.sum('*', i) <= inventory[i] for i in range(len(I))))

    m.setObjective(gp.quicksum(c[b]*y[b] for b in B), GRB.MAXIMIZE)

    m.optimize()

    optimal_brews = [b for b in B if y[b].x > 0.5]
    optimal_df = brews_df.loc[optimal_brews]
    optimal_df['count'] = [int(y[b].x) for b in B if y[b].x > 0.5]
    optimal_df.sort_values(by=['value'], ascending=False)
    optimal_df = optimal_df[['name', 'count', 'value', 'first_ingredient', 'second_ingredient', 'third_ingredient', 'descriptions']]
    optimal_df = optimal_df.sort_values(by='value', ascending=False)
    return [m.objVal, optimal_df]
