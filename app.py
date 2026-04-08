import streamlit as st
import pandas as pd
import numpy as np

def process_universal_partoo(uploaded_file):
    # 1. Lecture brute des premières lignes pour détection
    preview = pd.read_excel(uploaded_file, header=None, nrows=5)
    
    # On regarde la ligne 3 (index 2) qui contient les titres dans les deux formats
    header_row_content = str(preview.iloc[2].values).lower()

    # --- CAS 1 : FICHIER STATS (Double entête) ---
    if "recherche" in header_row_content or "action" in header_row_content:
        df_raw = pd.read_excel(uploaded_file, header=None)
        
        # Fusion des lignes 2 (index 1) et 3 (index 2)
        h1 = df_raw.iloc[1].fillna(method='ffill').fillna('') # Catégories parentes
        h2 = df_raw.iloc[2].fillna('') # Sous-catégories
        
        new_cols = []
        for top, bottom in zip(h1, h2):
            name = f"{top} - {bottom}".strip(" -")
            new_cols.append(name)
            
        df = df_raw.iloc[3:].copy()
        df.columns = new_cols
        df['Source_Type'] = "Stats"

    # --- CAS 2 : FICHIER AVIS (Simple entête ligne 3) ---
    else:
        # On démarre directement à la ligne 3 (skiprows=2)
        df = pd.read_excel(uploaded_file, skiprows=2)
        df.columns = [str(c).strip() for c in df.columns]
        df['Source_Type'] = "Avis"
        
        # Mapping automatique pour uniformiser les Avis
        # On cherche les colonnes par mots-clés pour éviter les erreurs d'index
        mapping = {
            'Date': ['date', 'période', 'mois'],
            'Agence': ['établissement', 'agence', 'nom'],
            'Note': ['note', 'étoile', 'rating'],
            'Groupe': ['groupe', 'entreprise', 'tag']
        }
        
        for final_name, keywords in mapping.items():
            for col in df.columns:
                if any(k in col.lower() for k in keywords):
                    df = df.rename(columns={col: final_name})
                    break

    # --- NETTOYAGE COMMUN ---
    # Identification de la colonne Date
    date_col = next((c for c in df.columns if 'date' in c.lower() or 'mois' in c.lower()), None)
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=[date_col])
        df = df.sort_values(date_col)

    return df

# --- DANS TON APP STREAMLIT ---
st.title("🛡️ Human Immobilier - Hub Partoo")

files = st.sidebar.file_uploader("Glissez vos exports (Stats ou Avis)", accept_multiple_files=True)

if files:
    all_dfs = [process_universal_partoo(f) for f in files]
    
    # Séparation des DataFrames par type pour les onglets
    df_stats = pd.concat([d for d in all_dfs if d['Source_Type'].iloc[0] == "Stats"], ignore_index=True) if any(d['Source_Type'].iloc[0] == "Stats" for d in all_dfs) else pd.DataFrame()
    df_avis = pd.concat([d for d in all_dfs if d['Source_Type'].iloc[0] == "Avis"], ignore_index=True) if any(d['Source_Type'].iloc[0] == "Avis" for d in all_dfs) else pd.DataFrame()

    tab1, tab2 = st.tabs(["📊 Performance (Stats)", "⭐ Réputation (Avis)"])

    with tab1:
        if not df_stats.empty:
            # Sélecteur dynamique basé sur les colonnes fusionnées
            metrics = [c for c in df_stats.columns if " - " in c]
            sel_metric = st.selectbox("Choisir une métrique de performance", metrics)
            fig = px.line(df_stats, x=df_stats.columns[0], y=sel_metric, color='Nom de l\'établissement')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucun fichier 'Stats' détecté.")

    with tab2:
        if not df_avis.empty:
            st.metric("Note Moyenne Globale", f"{df_avis['Note'].mean():.2f} ⭐")
            # Graphique des notes
            fig_avis = px.histogram(df_avis, x="Note", nbins=5, color="Note", title="Répartition des notes")
            st.plotly_chart(fig_avis, use_container_width=True)