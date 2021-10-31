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
    inventory_df = pd.DataFrame({'ingredient':ingredients, 'inventory':inventory})
    return render_template('my-form.html', inventory_df=inventory_df, z = z, df=[])

@app.route('/', methods=['GET', 'POST'])
def my_form_post():

    inventory = []
    for i in ingredients:
        inventory.append(int(request.form[i]))
    inventory_df = pd.DataFrame({'ingredient':ingredients,'inventory':inventory})
    [z, df] = create_model(inventory)

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
    return render_template('my-form.html', inventory_df=inventory_df, ingredients = ingredients, z=int(z), df=df)

if __name__ == "__main__":
    app.run(debug=True)