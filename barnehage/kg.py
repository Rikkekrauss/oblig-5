from flask import Flask
from flask import url_for
from flask import render_template
from flask import request
from flask import redirect
from flask import session
import pandas as pd
from kgmodel import (Foresatt, Barn, Soknad, Barnehage)
from kgcontroller import (evaluer_soknad, form_to_object_soknad, generer_statistikk, insert_soknad, commit_all, select_all_soknader, select_alle_barnehager)

app = Flask(__name__)
app.secret_key = 'BAD_SECRET_KEY' # nødvendig for session


df = pd.read_excel("ssb-barnehager-2015-2023-alder-1-2-aar.xlsm", sheet_name="KOSandel120000")
df.columns = ['Kommune'] + list(df.columns[1:])
df = df.replace('.', pd.NA)
for year in range(2015, 2024):
    df[str(year)] = pd.to_numeric(df[str(year)], errors='coerce')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/barnehager')
def barnehager():
    information = select_alle_barnehager()
    return render_template('barnehager.html', data=information)

@app.route('/behandle', methods=['GET', 'POST'])
def behandle():
    if request.method == 'POST':
        sd = request.form
        soknad_obj = form_to_object_soknad(sd)
        insert_soknad(soknad_obj)  # Lagre søknaden
        
        # Evaluer søknaden
        resultat = evaluer_soknad(soknad_obj)
        
        # Lagre både resultat og skjema data i session
        session['resultat'] = resultat
        session['information'] = sd  # Lagre skjema data
        return redirect(url_for('svar')) 
    else:
        return render_template('soknad.html')

@app.route('/soknader')
def soknader():
    soknader_data = select_all_soknader()
    return render_template('soknader.html', soknader=soknader_data)


@app.route('/svar')
def svar():
    information = session['information']
    return render_template('svar.html', data=information)

@app.route('/commit', methods=['GET'])  # Endret til GET
def commit():
    commit_all()  # Lagre alle data til kgdata.xlsx
    # Hent all data etter lagring
    foresatt_data = pd.read_excel('kgdata.xlsx', sheet_name='foresatt')
    barn_data = pd.read_excel('kgdata.xlsx', sheet_name='barn')
    soknad_data = pd.read_excel('kgdata.xlsx', sheet_name='soknad')
    barnehage_data = pd.read_excel('kgdata.xlsx', sheet_name='barnehage')

    # Opprett en liste for å vise dataene
    return render_template('commit.html', foresatt=foresatt_data.to_dict(orient='records'),
                           barn=barn_data.to_dict(orient='records'),
                           soknad=soknad_data.to_dict(orient='records'),
                           barnehage=barnehage_data.to_dict(orient='records'))

@app.route('/statistikk', methods=['GET', 'POST'])
def statistikk():
    # Hent kommuner
    kommuner = df['Kommune'].unique()
    
    if request.method == 'POST':
        valgt_kommune = request.form.get('kommune')
        chart_html = generer_statistikk(df, valgt_kommune)
        return render_template('statistikk.html', chart_html=chart_html, kommuner=kommuner)
    
    return render_template('statistikk.html', kommuner=kommuner)


if __name__ == '__main__':
    app.run(debug=True, port=8000)

"""
Referanser
[1] https://stackoverflow.com/questions/21668481/difference-between-render-template-and-redirect
"""

"""
Søkeuttrykk

"""