# kgcontroller module
import pandas as pd
import altair as alt
import numpy as np
from dbexcel import *
from kgmodel import *


# CRUD metoder

# Create
# pd.append, pd.concat eller df.loc[-1] = [1,2] df.index = df.index + 1 df = df.sort_index()
def insert_foresatt(f):
    global forelder
    new_id = 1 if forelder.empty else forelder['foresatt_id'].max() + 1
    
    # sjekk for duplikater og sett inn data
    forelder = pd.concat([pd.DataFrame([[new_id,
                                         f.foresatt_navn,
                                         f.foresatt_adresse,
                                         f.foresatt_tlfnr,
                                         f.foresatt_pnr]],
                columns=forelder.columns), forelder], ignore_index=True)
    
    # Lagre til Excel med en gang
    commit_all()
    
    return forelder

def insert_barn(b):
    global barn
    new_id = 1 if barn.empty else barn['barn_id'].max() + 1
    
    # sjekk for duplikater og sett inn data
    barn = pd.concat([pd.DataFrame([[new_id,
                                     b.barn_pnr]],
                columns=barn.columns), barn], ignore_index=True)
    
    # Lagre til Excel med en gang
    commit_all()
    
    return barn

def insert_soknad(s):
    global soknad
    new_id = 1 if soknad.empty else soknad['sok_id'].max() + 1
    
    # sett inn data
    soknad = pd.concat([pd.DataFrame([[new_id,
                                       s.foresatt_1.foresatt_id,
                                       s.foresatt_2.foresatt_id,
                                       s.barn_1.barn_id,
                                       s.fr_barnevern,
                                       s.fr_sykd_familie,
                                       s.fr_sykd_barn,
                                       s.fr_annet,
                                       s.barnehager_prioritert,
                                       s.sosken__i_barnehagen,
                                       s.tidspunkt_oppstart,
                                       s.brutto_inntekt]],
                columns=soknad.columns), soknad], ignore_index=True)
    
    # Lagre til Excel med en gang
    commit_all()
    
    return soknad


# ---------------------------
# Read (select)

def select_alle_barnehager():
    """Returnerer en liste med alle barnehager definert i databasen dbexcel."""
    return barnehage.apply(lambda r: Barnehage(r['barnehage_id'],
                             r['barnehage_navn'],
                             r['barnehage_antall_plasser'],
                             r['barnehage_ledige_plasser']),
         axis=1).to_list()

def select_foresatt(f_navn):
    """OBS! Ignorerer duplikater"""
    series = forelder[forelder['foresatt_navn'] == f_navn]['foresatt_id']
    if series.empty:
        return np.nan
    else:
        return series.iloc[0] # returnerer kun det første elementet i series

def select_barn(b_pnr):
    """OBS! Ignorerer duplikater"""
    series = barn[barn['barn_pnr'] == b_pnr]['barn_id']
    if series.empty:
        return np.nan
    else:
        return series.iloc[0] # returnerer kun det første elementet i series
    
def select_all_soknader():
    """Viser alle søknader med tilknyttede foresatte og barn fra forskjellige ark."""
    resultater = []
    
    # Hent data fra Excel-filen
    foresatt_data = pd.read_excel('kgdata.xlsx', sheet_name='foresatt')
    barn_data = pd.read_excel('kgdata.xlsx', sheet_name='barn')
    soknad_data = pd.read_excel('kgdata.xlsx', sheet_name='soknad')

    for index, row in soknad_data.iterrows():
        foresatt_1_id = row['foresatt_1']
        foresatt_2_id = row['foresatt_2']
        barn_id = row['barn_1']

        # Finn foresatt og barn
        foresatt_1 = foresatt_data.loc[foresatt_data['foresatt_id'] == foresatt_1_id].iloc[0]
        foresatt_2 = foresatt_data.loc[foresatt_data['foresatt_id'] == foresatt_2_id].iloc[0]
        barn = barn_data.loc[barn_data['barn_id'] == barn_id].iloc[0]

        # Lag Soknad-objekt for evaluering
        soknad_objekt = Soknad(
            sok_id=row['sok_id'],
            foresatt_1=Foresatt(foresatt_1_id, foresatt_1['foresatt_navn'], foresatt_1['foresatt_adresse'], foresatt_1['foresatt_tlfnr'], foresatt_1['foresatt_pnr']),
            foresatt_2=Foresatt(foresatt_2_id, foresatt_2['foresatt_navn'], foresatt_2['foresatt_adresse'], foresatt_2['foresatt_tlfnr'], foresatt_2['foresatt_pnr']),
            barn_1=Barn(barn_id, barn['barn_pnr']),
            fr_barnevern=row['fr_barnevern'],
            fr_sykd_familie=row['fr_sykd_familie'],
            fr_sykd_barn=row['fr_sykd_barn'],
            fr_annet=row['fr_annet'],
            barnehager_prioritert=row['barnehager_prioritert'],
            sosken__i_barnehagen=row['sosken__i_barnehagen'],
            tidspunkt_oppstart=row['tidspunkt_oppstart'],
            brutto_inntekt=row['brutto_inntekt']
        )

        # Evaluer søknad for å få status
        status = evaluer_soknad(soknad_objekt)

        # Debugging: Skriv ut detaljene for evaluering
        print(f"Søknad ID: {row['sok_id']}, Status: {status}, Foresatt 1: {foresatt_1['foresatt_navn']}, Foresatt 2: {foresatt_2['foresatt_navn']}, Barn: {barn['barn_pnr']}")

        # Legg til informasjon i resultater
        resultater.append({
            'soknad_id': row['sok_id'],
            'foresatt_1_navn': foresatt_1['foresatt_navn'],
            'foresatt_2_navn': foresatt_2['foresatt_navn'],
            'barn_pnr': barn['barn_pnr'],
            'fr_barnevern': row['fr_barnevern'],
            'fr_sykd_familie': row['fr_sykd_familie'],
            'fr_sykd_barn': row['fr_sykd_barn'],
            'fr_annet': row['fr_annet'],
            'barnehager_prioritert': row['barnehager_prioritert'],
            'sosken_i_barnehagen': row['sosken__i_barnehagen'],
            'tidspunkt_oppstart': row['tidspunkt_oppstart'],
            'brutto_inntekt': row['brutto_inntekt'],
            'status': status  # Her legger vi til den evaluerte statusen
        })

    return resultater







# --- Skriv kode for select_soknad her


# ------------------
# Update


# ------------------
# Delete


# ----- Persistent lagring ------
    

def evaluer_soknad(soknad):
    """Evaluerer søknaden og returnerer 'Tilbud' eller 'Avslag' basert på tilgjengelige plasser."""
    
    # Debugging: Sjekk innholdet i søknaden
    print(f"Evaluering av søknad: {soknad}")

    # Håndter nan-verdier for fortrinnsrett
    barnevern = soknad.fr_barnevern if not pd.isna(soknad.fr_barnevern) else False
    syk_familie = soknad.fr_sykd_familie if not pd.isna(soknad.fr_sykd_familie) else False
    syk_barn = soknad.fr_sykd_barn if not pd.isna(soknad.fr_sykd_barn) else False
    annet = soknad.fr_annet if not pd.isna(soknad.fr_annet) else False

    # Debugging: Sjekk fortrinnsrett
    print(f"Fortrinnsrett - Barnevern: {barnevern}, Sykdom familie: {syk_familie}, Sykdom barn: {syk_barn}, Annet: {annet}")

    # Sjekk fortrinnsrett
    if barnevern or syk_familie or syk_barn or annet:
        return 'Tilbud'
    
    # Sjekk om barnehager_prioritert er gyldig
    if pd.isna(soknad.barnehager_prioritert):
        return 'Avslag'  # Returner avslag hvis prioriterte barnehager ikke er spesifisert

    # Hvis barnehager_prioritert er en enkelt ID (int), konverter til liste for enklere behandling
    if isinstance(soknad.barnehager_prioritert, int):
        barnehager_prioritert = [soknad.barnehager_prioritert]
    elif isinstance(soknad.barnehager_prioritert, list):
        barnehager_prioritert = soknad.barnehager_prioritert
    else:
        # Håndter tilfeller hvor dataen er feilformatert (f.eks. som float)
        return 'Avslag'
    
    # Sjekk for tilgjengelige plasser i hver prioriterte barnehage
    for barnehage_id in barnehager_prioritert:
        barnehage_info = barnehage[barnehage['barnehage_id'] == barnehage_id]

        if not barnehage_info.empty:
            ledige_plasser = barnehage_info['barnehage_ledige_plasser'].values[0]
            print(f"Barnehage ID: {barnehage_id}, Ledige plasser: {ledige_plasser}")  # Debugging
            if ledige_plasser > 0:
                # Oppdater antall ledige plasser
                barnehage.at[barnehage_id - 1, 'barnehage_ledige_plasser'] -= 1
                return 'Tilbud'

    return 'Avslag'


def generer_statistikk(df, kommune):
    """Lager et linjediagram for en valgt kommune og returnerer HTML."""
    data_chosen = df[['Kommune'] + [str(year) for year in range(2015, 2024)]]
    data_chosen = data_chosen[data_chosen['Kommune'] == kommune].melt(id_vars='Kommune', var_name='År', value_name='Prosent').dropna()
    
    chart = alt.Chart(data_chosen).mark_line().encode(
        x='År:O',
        y='Prosent:Q',
        color='Kommune:N'
    ).properties(
        title=f'Prosent av barn i ett- og to-årsalderen i barnehagen for {kommune} (2015-2023)',
        width=800,
        height=400
    )
    
    return chart.to_html()  # Returnerer HTML for grafen


def commit_all():
    """Skriver alle dataframes til excel"""
    with pd.ExcelWriter('kgdata.xlsx', mode='a', if_sheet_exists='replace') as writer:  
        forelder.to_excel(writer, sheet_name='foresatt')
        barnehage.to_excel(writer, sheet_name='barnehage')
        barn.to_excel(writer, sheet_name='barn')
        soknad.to_excel(writer, sheet_name='soknad')
        
# --- Diverse hjelpefunksjoner ---
def form_to_object_soknad(sd):
    """sd - formdata for soknad, type: ImmutableMultiDict fra werkzeug.datastructures
Eksempel:
ImmutableMultiDict([('navn_forelder_1', 'asdf'),
('navn_forelder_2', ''),
('adresse_forelder_1', 'adf'),
('adresse_forelder_2', 'adf'),
('tlf_nr_forelder_1', 'asdfsaf'),
('tlf_nr_forelder_2', ''),
('personnummer_forelder_1', ''),
('personnummer_forelder_2', ''),
('personnummer_barnet_1', '234341334'),
('personnummer_barnet_2', ''),
('fortrinnsrett_barnevern', 'on'),
('fortrinnsrett_sykdom_i_familien', 'on'),
('fortrinnsrett_sykdome_paa_barnet', 'on'),
('fortrinssrett_annet', ''),
('liste_over_barnehager_prioritert_5', ''),
('tidspunkt_for_oppstart', ''),
('brutto_inntekt_husholdning', '')])
    """
    # Lagring i hurtigminne av informasjon om foreldrene (OBS! takler ikke flere foresatte)
    foresatt_1 = Foresatt(0,
                          sd.get('navn_forelder_1'),
                          sd.get('adresse_forelder_1'),
                          sd.get('tlf_nr_forelder_1'),
                          sd.get('personnummer_forelder_1'))
    insert_foresatt(foresatt_1)
    foresatt_2 = Foresatt(0,
                          sd.get('navn_forelder_2'),
                          sd.get('adresse_forelder_2'),
                          sd.get('tlf_nr_forelder_2'),
                          sd.get('personnummer_forelder_2'))
    insert_foresatt(foresatt_2) 
    
    # Dette er ikke elegang; kunne returnert den nye id-en fra insert_ metodene?
    foresatt_1.foresatt_id = select_foresatt(sd.get('navn_forelder_1'))
    foresatt_2.foresatt_id = select_foresatt(sd.get('navn_forelder_2'))
    
    # Lagring i hurtigminne av informasjon om barn (OBS! kun ett barn blir lagret)
    barn_1 = Barn(0, sd.get('personnummer_barnet_1'))
    insert_barn(barn_1)
    barn_1.barn_id = select_barn(sd.get('personnummer_barnet_1'))
    
    # Lagring i hurtigminne av all informasjon for en søknad (OBS! ingen feilsjekk / alternativer)
        
    sok_1 = Soknad(0,
                   foresatt_1,
                   foresatt_2,
                   barn_1,
                   sd.get('fortrinnsrett_barnevern'),
                   sd.get('fortrinnsrett_sykdom_i_familien'),
                   sd.get('fortrinnsrett_sykdome_paa_barnet'),
                   sd.get('fortrinssrett_annet'),
                   sd.get('liste_over_barnehager_prioritert_5'),
                   sd.get('har_sosken_som_gaar_i_barnehagen'),
                   sd.get('tidspunkt_for_oppstart'),
                   sd.get('brutto_inntekt_husholdning'))
    
    return sok_1

# Testing
def test_df_to_object_list():
    assert barnehage.apply(lambda r: Barnehage(r['barnehage_id'],
                             r['barnehage_navn'],
                             r['barnehage_antall_plasser'],
                             r['barnehage_ledige_plasser']),
         axis=1).to_list()[0].barnehage_navn == "Sunshine Preschool"
