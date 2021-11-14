from flask import Flask, render_template, url_for, request
import pandas as pd
from optimization import create_model

ingredients_df = pd.read_pickle('data/ingredients.pkl')
ingredients = ingredients_df['name']
app = Flask(__name__)

#@app.route('/')
#def index():
#    return render_template('index.html')

@app.route('/')
def my_form():
    z = -1
    inventory = [0 for i in ingredients]
    stats = [0,0,0,0,0,0]
    inventory_df = pd.DataFrame({'ingredient':ingredients, 'inventory':inventory})
    return render_template('my-form.html', inventory_df=inventory_df, stats = stats, z = z, df=[])

@app.route('/', methods=['GET', 'POST'])
def my_form_post():
    #print(request.form)
    alchemy_skill = int(request.form['Alchemy Skill'])
    alchemist_perk = int(request.form['Alchemist Perk'])
    physician_perk = 0
    benefactor_perk = 0
    poisoner_perk = 0
    if request.form.__contains__('Physician Perk'):
        physician_perk = 1
    if request.form.__contains__('Benefactor Perk'):
        benefactor_perk = 1
    if request.form.__contains__('Poisoner Perk'):
        poisoner_perk = 1
    stat_names = ['Alchemy Skill', 'Alchemist Perk', 'Fortify Alchemy', 
            'Physician Perk', 'Benefactor Perk', 'Poisoner Perk']
    stats = [alchemy_skill, alchemist_perk, 0, 
                physician_perk, benefactor_perk, poisoner_perk]
                
    for i in range(len(stat_names)):
        print(f'{stat_names[i]}: {stats[i]}')

    inventory = []
    for i in ingredients:
        inventory.append(int(request.form[i]))
    inventory_df = pd.DataFrame({'ingredient':ingredients,'inventory':inventory})

    [z, df] = create_model(inventory, stats)

    remaining_inventory = inventory

    for i in range(len(df)):
        brew = df.iloc[i]
        

    indices = [i for i in range(len(df))]
    names = df['name']
    counts = df['count']
    values = df['value']
    first_ingredient = df['first_ingredient']
    second_ingredient = df['second_ingredient']
    third_ingredient = df['third_ingredient']
    descriptions = df['descriptions']
    return render_template('my-form.html', inventory_df=inventory_df, ingredients = ingredients, stats=stats, z=int(z), df=df)

if __name__ == "__main__":
    app.run(debug=True)