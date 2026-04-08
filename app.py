import streamlit as st
import pandas as pd
import plotly.express as px
import io

def fix_stats_headers(df_raw):
    """Fusionne la ligne 2 et 3 pour créer des noms de colonnes clairs."""
    # On récupère les deux lignes d'en-tête
    header_top = df_raw.iloc[1].fillna('')  # Ligne 2
    header_bottom = df_raw.iloc[2].fillna('') # Ligne 3
    
    new_columns = []
    current_category = ""
    
    for top, bottom in zip(header_top, header_bottom):
        # Gestion du "Merge" Excel : si le haut est vide, on garde la catégorie précédente
        if str(top).strip() != "":
            current_category = str(top).strip()
        
        if current_category and bottom:
            new_columns.append(f"{current_category} - {bottom}")
        else:
            new_columns.append(str(bottom) if bottom else str(top))
            
    return new_columns

def process_file(uploaded_file):
    # Lecture brute sans header pour analyser la structure
    df_raw = pd.read_excel(uploaded_file, header=None)
    
    # --- DETECTION TYPE ---
    # On regarde la ligne 3 (index 2) pour identifier le contenu
    sample_row = str(df_raw.iloc[2].values).lower()
    
    if "recherches" in sample_row or "vues" in sample_row:
        # C'EST UN FICHIER STATS
        cols = fix_stats_headers(df_raw)
        df = df_raw.iloc[3:].copy() # Données à partir de la ligne 4
        df.columns = cols
        df['Type_Fichier'] = "Stats"
    else:
        # C'EST UN FICHIER AVIS (on garde ta logique d'index fixe)
        df = df_raw.copy()
        df.columns = [f"Col_{i}" for i in range(len(df.columns))]
        # On renomme selon tes besoins Agence/Note/Groupe
        df = df.rename(columns={'Col_0': 'Date', 'Col_3': 'Agence', 'Col_4': 'Groupe', 'Col_14': 'Note'})
        df['Type_Fichier'] = "Avis"

    # Nettoyage Date (Colonne 0 dans les deux cas en général)
    date_col = df.columns[0]
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df = df.dropna(subset=[date_col])
    
    return df

# --- INTERFACE STREAMLIT ---
st.title("📊 Partoo Hub : Avis & Stats")

files = st.sidebar.file_uploader("Charger Avis ou Stats", accept_multiple_files=True)

if files:
    all_data = [process_file(f) for f in files]
    
    # Séparation pour affichage
    df_stats = pd.concat([d for d in all_data if d['Type_Fichier'].iloc[0] == "Stats"], ignore_index=True)
    df_avis = pd.concat([d for d in all_data if d['Type_Fichier'].iloc[0] == "Avis"], ignore_index=True)

    tab1, tab2 = st.tabs(["📈 Statistiques", "⭐ Avis Clients"])

    with tab1:
        if not df_stats.empty:
            st.write("Données de performance (Recherches, Vues, Actions)")
            # Ici tu peux choisir une colonne fusionnée, ex: "Nombre de recherches - Directes"
            target = st.selectbox("Choisir une métrique", [c for c in df_stats.columns if '-' in c])
            fig = px.line(df_stats.sort_values(df_stats.columns[0]), x=df_stats.columns[0], y=target)
            st.plotly_chart(fig)
        else:
            st.info("Chargez des fichiers de statistiques.")

    with tab2:
        if not df_avis.empty:
            st.write("Analyse des notes")
            st.metric("Note Moyenne", f"{df_avis['Note'].mean():.2f} ⭐")
            # Filtres agences ici...
        else:
            st.info("Chargez des fichiers d'avis.")