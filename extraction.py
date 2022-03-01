"""Reads potion data from the internet and writes to a data frame"""
import requests
import pandas as pd
import time
from bs4 import BeautifulSoup

def get_ingredient_dataframe():
    """Reads the table of ingredient data from the 
    Unofficial Elder Scrolls Pages, and pickles the resulting data 
    frame into ./data"""

    URL = "https://en.uesp.net/wiki/Skyrim:Ingredients"
    page = requests.get(URL)
    soup = BeautifulSoup(page.text, 'html.parser')
    for a in soup.findAll('a', {'class': 'image'}):
        try:
            a.replaceWith("%s" % a['title'])
        except KeyError:
            pass

    data = []
    table = soup.find('table', attrs={'class':'wikitable'})
    rows = table.find_all('tr')
    for row in rows:
        cols = row.find_all('td')
        cols = [ele.text.strip() for ele in cols]
        data.append(cols)

    # each ingredient is associated with a couplet of rows; 
    # so we combine each couplet to a single row
    data2 = [data[2 * i - 1] + data[2 * i] 
                for i in range(1, int(((len(data) - 1) / 2) + 1))]

    df = pd.DataFrame(data2)
    df['name'] = [text.split('\n')[0] for text in df[1]] 
    df['id'] = [text.split('\n')[1] for text in df[1]] 
    df.columns = ['index', 'long_name', 'how_to_get', 'effect_1', 
                    'effect_2', 'effect_3', 'effect_4', 'cost', 
                    'weight', 'merchant_avail', 'garden_yield', 
                    'name', 'id']

    def get_expansion(name):
        if name.endswith('DB'):
            return 'Dragonborn'
        elif name.endswith('DG'):
            return 'Dawnguard'
        elif name.endswith('HF'):
            return 'HearthFire'
        else:
            return 'Base'
    df['expansion'] = [get_expansion(name) for name in df['name']]

    for i in range(1, len(df)):
        name = df['name'][i]
        expansion = df['expansion'][i]
        if expansion != 'Base':
            df['name'][i] = name[: len(name)-2]

    df2 = df[['name', 'id', 'expansion', 'how_to_get', 'effect_1', 
                'effect_2', 'effect_3', 'effect_4', 'cost', 'weight', 
                'merchant_avail', 'garden_yield']]
    df2.to_pickle('data/ingredients.pkl')

# get_ingredient_dataframe()

def get_effect_dataframe():
    """Reads the table of effect data from the 
    Unofficial Elder Scrolls Pages, and pickles the resulting data 
    frame into ./data"""

    URL = "https://en.uesp.net/wiki/Skyrim:Alchemy_Effects"
    page = requests.get(URL)

    soup = BeautifulSoup(page.text, 'html.parser')
    for a in soup.findAll('a', {'class': 'image'}):
        a.replaceWith("%s" % a['title'])

    data = []
    table = soup.find('table', attrs={'class':'wikitable sortable'})
    rows = table.find_all('tr')
    for row in rows:
        cols = row.find_all(['th', 'td'])

        # determine whether potion or poison
        if cols[0].has_attr('class') and cols[0]['class'][0] == 'EffectPos':
            potion_data = ['Potion']
        else:
            potion_data = ['Poison']

        # determine whether magnitude or duration is fixed (always exactly 1 is true)
        if cols[4].has_attr('class') and cols[4]['class'][0] == 'EffectNeg':
            potion_data.append('fixed_magnitude')
        else:
            potion_data.append('fixed_duration')

        cols = [ele.text.strip() for ele in cols]
        data.append(potion_data + cols)
    df = pd.DataFrame(data)
    df = df[1:]
    df.columns = ['type', 'fixed', 'name_id', 'ingredients', 'description', 
                  'base_cost', 'base_magnitude', 'base_duration', 
                  'value']
    df['name'] = [text.split('\n')[0] for text in df['name_id']] 
    df['id'] = [text.split('\n')[1][1:-1] for text in df['name_id']] 

    df2 = df[['name', 'id', 'type', 'description', 'ingredients', 'fixed',
              'base_cost', 'base_magnitude', 'base_duration', 'value']]
    df2['base_cost'] = pd.to_numeric(df2['base_cost'], errors='coerce')
    df2['base_magnitude'] = pd.to_numeric(df2['base_magnitude'], errors='coerce')
    df2['base_duration'] = pd.to_numeric(df2['base_duration'], errors='coerce')
    df2['value'] = pd.to_numeric(df2['value'], errors='coerce')

    df2.to_pickle('data/effects.pkl')


def get_brew_dataframe():
    ingredients_df = pd.read_pickle('data/ingredients.pkl')

    def get_effects(ingredients):
        effects_list = []
        for ingredient in ingredients:
            effects = list(ingredients_df.loc[ingredients_df.name == ingredient, 
                                    ['effect_1', 'effect_2', 'effect_3', 'effect_4']].values[0])
            effects_list.append(effects)
            
        possible_effects = {}
        for effects in effects_list:
            for effect in effects:
                possible_effects[effect] = possible_effects.get(effect, 0) + 1
        
        created_effects = []
        for effect in possible_effects.keys():
            if possible_effects[effect] >= 2:
                created_effects.append(effect)
        
        return created_effects

    tic = time.perf_counter()
    potion_df = pd.DataFrame()
    potion_data = []
    for i in range(len(ingredients_df)):
        toc = time.perf_counter()
        first = ingredients_df.name[i]
        print(f'Current First Ingredient: {first} \t Total elapsed time: {toc - tic:.2f} seconds')
        for j in range(i+1, len(ingredients_df)):
            second = ingredients_df.name[j]
            effects = get_effects([first, second])
            potion_data.append([first, second, 'NA', effects])
            for k in range(j+1, len(ingredients_df)):
                third = ingredients_df.name[k]
                effects = get_effects([first, second, third])
                potion_data.append([first, second, third, effects])
    toc = time.perf_counter()
    print(f'Total elapsed time: {toc - tic:.2f} seconds')
    potion_df = potion_df.append(potion_data, ignore_index = True)
    potion_df.columns = ['first_ingredient', 'second_ingredient', 'third_ingredient', 'effects']

     ############ remove potions with no effect
    valid_potion_indices = [i for i in range(len(potion_df)) if potion_df.effects[i] != []]
    valid_potions = potion_df.loc[valid_potion_indices]
    valid_potions.reset_index(drop=True, inplace=True)
    del valid_potions['index']

    ############ Remove potions in which an ingredient is unnecessary
    effects_df = pd.read_pickle('data/effects.pkl')

    def get_necessary_ingredients(effect, ingredients):
        possible_ingredients = effect['ingredients'].split('\n') 
        indices = []
        for ingredient in ingredients:
            result = [i for i, item in enumerate(possible_ingredients) if item.startswith(ingredient)]
            if result != []:
                indices.append(result[0])
        indices.sort()
        indices = indices[:2]
        necessary_ingredients = [possible_ingredients[i] for i in indices]
        necessary_ingredients = [ingredient for ingredient in ingredients 
                                if any(necessary_ingredient.startswith(ingredient) 
                                        for necessary_ingredient in necessary_ingredients)]
        return necessary_ingredients
    
    necessary_brews = []
    for i in range(len(valid_potions)):
        brew = valid_potions.iloc[i]
        effects = effects_df.loc[effects_df['name'].isin(brew.effects)]
        ingredients = [brew.first_ingredient, 
                brew.second_ingredient, 
                brew.third_ingredient]
        necessary_ingredients = []
        for effect_index in effects.index:
            effect = effects.loc[effect_index]
            new_necessary_ingredients = get_necessary_ingredients(effect, ingredients)
            for new_necessary_ingredient in new_necessary_ingredients:
                necessary_ingredients.append(new_necessary_ingredient)
        necessary_ingredients = list(set(necessary_ingredients))
        num_ingredients = len([ingredient for ingredient in ingredients if ingredient != 'NA'])
        num_necessary_ingredients = len(necessary_ingredients)
        if num_necessary_ingredients == num_ingredients:
            necessary_brews.append(i)

    necessary_brews = valid_potions.loc[necessary_brews]
    necessary_brews.reset_index(drop=True, inplace=True)
    del necessary_brews['index']

    necessary_brews.to_pickle('data/brews.pkl')



# get_ingredient_dataframe()
# get_effect_dataframe()
# get_brew_dataframe()