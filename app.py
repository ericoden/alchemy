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
    return render_template('my-form.html', ingredients = ingredients)

@app.route('/', methods=['POST'])
def my_form_post():
    inventory = []
    for i in ingredients:
        inventory.append(int(request.form[i]))
    [z, df] = create_model(inventory)
    return 'Optimal Objective: ' + z

if __name__ == "__main__":
    app.run(debug=True)