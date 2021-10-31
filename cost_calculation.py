
import pandas as pd
import numpy as np
import math
import re
import time

brew_df = pd.read_pickle('data/brews.pkl')
effects_df = pd.read_pickle('data/effects.pkl')
ingredients_df = pd.read_pickle('data/ingredients.pkl')

brew_df

effects_df

#ALCHEMY_SKILL = 30
#ALCHEMIST_PERK_RANK = 3
#PHYSICIAN_PERK = True
#BENEFACTOR_PERK = True
#POISONER_PERK = True

def get_alchemist_factor():
    return 20 * ALCHEMIST_PERK_RANK

def get_physician_factor(effect):
    if PHYSICIAN_PERK:
        if effect['name'] in ['Restore Health', 
                              'Restore Magicka',
                              'Restore Stamina']:
            return 25
    return 0

def get_benefactor_factor(effect, brew_type):
    if BENEFACTOR_PERK:
        if effect['type'] == 'Potion' and brew_type == 'Potion':
            return 25
    return 0

def get_poisoner_factor(effect, brew_type):
    if POISONER_PERK:
        if effect['type'] == 'Poison' and brew_type == 'Poison':
            return 25
    return 0

def get_power_factor(effect, perks, brew_type):
    ingredient_factor = 4.0
    alchemy_skill = ALCHEMY_SKILL
    fortify_alchemy = 0
    alchemist_factor = get_alchemist_factor()
    
    if perks:
        physician_factor = get_physician_factor(effect)
        benefactor_factor = get_benefactor_factor(effect, brew_type)
        poisoner_factor = get_poisoner_factor(effect, brew_type)
    else:
        physician_factor = 0
        benefactor_factor = 0
        poisoner_factor = 0

    return ingredient_factor \
        * (1 + alchemy_skill / 200 ) \
        * (1 + fortify_alchemy / 100) \
        * (1 + alchemist_factor / 100) \
        * (1 + physician_factor / 100) \
        * (1 + benefactor_factor / 100 + poisoner_factor / 100)

def get_nonstandard_ingredient_multipliers(effect, ingredients):
    possible_ingredients = effect['ingredients'].split('\n') 
    indices = []
    for ingredient in ingredients:
        result = [i for i, item in enumerate(possible_ingredients) if item.startswith(ingredient)]
        if result != []:
            indices.append(result[0])
    nonstandard_ingredient = possible_ingredients[min(indices)]
    
    mag_mult = 1
    dur_mult = 1
    val_mult = 1
    
    if '(' in nonstandard_ingredient:
        multiplier_string = nonstandard_ingredient[nonstandard_ingredient.index('(')+1:nonstandard_ingredient.index(')')]
        multiplier_fragments = multiplier_string.split(',')
        for multiplier_fragment in multiplier_fragments:
            if 'Magnitude' in multiplier_fragment:
                mag_mult = float(multiplier_fragment[:multiplier_fragment.index('×Magnitude')])
            if 'Duration' in multiplier_fragment:
                dur_mult = float(multiplier_fragment[:multiplier_fragment.index('×Duration')])
            if 'Value' in multiplier_fragment:
                val_mult = float(multiplier_fragment[:multiplier_fragment.index('×Value')])
                
    return [mag_mult, dur_mult, val_mult]

def get_effect_value(effect, ingredients, perks=False, brew_type='NA'):
    
    multipliers = get_nonstandard_ingredient_multipliers(effect, ingredients)
    
    magnitude = effect['base_magnitude'] * multipliers[0]
    duration = effect['base_duration'] * multipliers[1]
    value = effect['base_cost'] * multipliers[2]

    power_factor = get_power_factor(effect, perks, brew_type)
    
    if effect['fixed'] == 'fixed_magnitude' or effect['base_magnitude'] in [0, 'NaN']:
        magnitude_factor = 1
    else:
        magnitude_factor = power_factor
    magnitude = round(magnitude * magnitude_factor)
    
    if effect['fixed'] == 'fixed_duration' or effect['base_duration'] in [0, 'NaN']:
        duration_factor = 1
    else:
        duration_factor = power_factor
    duration = round(duration * duration_factor)
    
    magnitude_factor = 1
    if magnitude > 0:
        magnitude_factor = magnitude
    duration_factor = 1
    if duration > 0:
        duration_factor = duration / 10
    value = math.floor(value * (magnitude_factor * duration_factor) ** (1.1))
    
    if perks == True:
        #print(f"Effect: {effect['name']} \t Magnitude: {magnitude} \t Duration: {duration} \t Value: {value}")
        description = effect['description']
        description = description.replace('<mag>', str(magnitude))
        description = description.replace('<dur>', str(duration))
        return [value, description]
    else:
        return value

def get_total_value(index):
    brew = brew_df.iloc[index]
    effects = effects_df.loc[effects_df['name'].isin(brew.effects)]
    ingredients = [brew.first_ingredient, 
                   brew.second_ingredient, 
                   brew.third_ingredient]
    # get gold value of each effect, WITHOUT factoring in perks
    # to get the primary effect
    max_value = 0
    for effect_index in effects.index:
        effect = effects.loc[effect_index]
        value = get_effect_value(effect, ingredients)
        if value > max_value:
            max_value = value
            primary_effect = effect
    
    # determine whether potion or poison
    brew_type = primary_effect['type']
    total_value = 0
    description_list = []
    for effect_index in effects.index:
        effect = effects.loc[effect_index]
        result = get_effect_value(effect, ingredients, perks=True, brew_type=brew_type)
        total_value += result[0]
        description_list.append(result[1])
    brew_name = brew_type + ' of ' + primary_effect['name']
    return [total_value, brew_name, description_list]

def calculate_costs(ALCHEMY_SKILL = 49,
                    ALCHEMIST_PERK_RANK = 1,
                    PHYSICIAN_PERK = False,
                    BENEFACTOR_PERK = False,
                    POISONER_PERK = False):
    brew_names = []
    brew_values = []
    brew_descriptions = []
    tic = time.perf_counter()
    for i in range(len(brew_df)):
        [value, brew_name, descriptions] = get_total_value(i)
        if i % 1000 == 0:
            toc = time.perf_counter()
            print('Index:', i, 'Elapsed Time', np.round(toc-tic, 2), 'seconds')
        brew_names.append(brew_name)
        brew_values.append(value)
        brew_descriptions.append(descriptions)
        
    brew_df['name'] = brew_names
    brew_df['value'] = brew_values
    brew_df['descriptions'] = brew_descriptions
    brew_df.to_pickle('data/brews_with_costs.pkl')

calculate_costs()