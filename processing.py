import pandas as pd
import math

ingredients = pd.read_pickle("data/ingredients.pkl")

print(ingredients.head())

ALCHEMY_SKILL = 30
ALCHEMIST_PERK_RANK = 3
PHYSICIAN_PERK = True
BENEFACTOR_PERK = True
POISONER_PERK = True


def get_alchemist_factor():
    return 20 * ALCHEMIST_PERK_RANK

def get_physician_factor():
    return 1

def get_benefactor_factor():
    return 1

def get_poisoner_factor():
    return 1

def get_power_factor():
    ingredient_factor = 4.0
    skill_factor = 1.5
    alchemy_skill = ALCHEMY_SKILL
    fortify_alchemy = 1 # sum of all active Fortify Alchemy effects
    alchemist_factor = get_alchemist_factor()
    physician_factor = get_physician_factor()
    benefactor_factor = get_benefactor_factor()
    poisoner_factor = get_poisoner_factor()

    return ingredient_factor \
        * (1 + (alchemy_skill - 1) * alchemy_skill / 100 ) \
        * (1 + fortify_alchemy / 100) \
        * (1 + alchemist_factor / 100) \
        * (1 + physician_factor / 100) \
        * (1 + benefactor_factor / 100 + poisoner_factor / 100)

def get_base_cost():
    pass

def get_magnitude():
    pass

def get_duration():
    pass

def get_gold_cost():
    base_cost = get_base_cost()
    magnitude = get_magnitude()
    duration = get_duration()

    if duration == 0:
        duration = 1

    return math.floor(base_cost \
            * max(magnitude ** 1.1, 1) \
            * duration ** 1.1)

