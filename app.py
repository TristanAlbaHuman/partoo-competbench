import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Human Hub - Partoo Analytics", layout="wide")

# --- 1. FONCTIONS DE NETTOYAGE ---

def make_columns_unique(columns):
    """Évite l'erreur DuplicateError de Plotly/Narwhals."""
    seen = {}
    new_cols = []
    for item in columns:
        item_str = str(item)
        if item_str in seen:
            seen[item_str] += 1
            new_cols.append(f"{item_str}.{seen[item_str]}")
        else:
            seen[item_str] = 0
            new_cols.append(item_str)
    return new_cols

def process_universal(uploaded_file):
    """Détecte le format (Avis ou Stats) et standardise les données."""
    # Aperçu pour détection (ligne 3 / index 2)
    preview = pd.read_excel(uploaded_file, header=None, nrows=5)
    header_line = str(preview.iloc[2].values).lower()

    # CAS A : STATISTIQUES (KPIs)
    if any(k in header_line for k in ["recherche", "action", "vues"]):
        df_raw = pd.read_excel(uploaded_file, header=None)
        # Fusion des lignes d'en-tête 2 et 3
        h1 = df_raw.iloc[1].ffill().fillna('') 
        h2 = df_raw.iloc[2].fillna('')
        raw_cols = [f"{str(a)} - {str(b)}".strip(" -") for a, b in zip(h1, h2)]
        df_raw.columns = make_columns_unique(raw_cols)
        
        df = df_raw.iloc[3:].copy()
        df['Source_Type'] = "Stats"

    # CAS B : AVIS (Réputation)
    else:
        df = pd.read_excel(uploaded_file, skiprows=2)
        df.columns = make_columns_unique([str(c).strip() for c in df.columns])
        df['Source_Type'] = "Avis"
        
        # Harmonisation des colonnes critiques
        mapping = {
            'Date_Std': ['date', 'période', 'mois'],
            'Agence_Std': ['établissement', 'agence', 'nom', 'magasin'],
            'Note_Std': ['note', 'étoile', 'rating'],
        }
        for final, keywords in mapping.items():
            for col in df.columns:
                if any(k in col.lower() for k in keywords):
                    df = df.rename(columns={col: final})
                    break
    
    # Standardisation de la date
    date_col = next((c for c in df.columns if 'date' in c.lower() or 'mois' in c.lower() or 'période' in c.lower()), df.columns[0])
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df = df.dropna(subset=[date_col])
    
    return df

# --- 2. INTERFACE UTILISATEUR ---

st.title("🛡️ Human Immobilier : Hub Partoo")
st.markdown("Fusion automatique des Avis (2021-25) et Statistiques (2024-25).")

files = st.sidebar.file_uploader("Glissez vos fichiers Excel ici", accept_multiple_files=True)

# Initialisation cruciale pour éviter NameError
df_stats = pd.DataFrame()
df_avis = pd.DataFrame()

if files:
    all_data = []
    for f in files:
        try:
            all_data.append(process_universal(f))
        except Exception as e:
            st.sidebar.error(f"Erreur sur {f.name}: {e}")

    if all_data:
        # Séparation des types
        list_stats = [d for d in all_data if d['Source_Type'].iloc[0] == "Stats"]
        list_avis = [d for d in all_data if d['Source_Type'].iloc[0] == "Avis"]
        
        if list_stats:
            df_stats = pd.concat(list_stats, ignore_index=True)
        if list_avis:
            df_avis = pd.concat(list_avis, ignore_index=True)

# --- 3. AFFICHAGE PAR ONGLETS ---

tab1, tab2 = st.tabs(["📈 Performance (Stats)", "⭐ Réputation (Avis)"])

with tab1:
    if not df_stats.empty:
        st.subheader("Analyse des flux et actions")
        # Nettoyage numérique des colonnes KPI
        cols_kpi = [c for c in df_stats.columns if " - " in c]
        for c in cols_kpi:
            df_stats[c] = pd.to_numeric(df_stats[c], errors='coerce')
        
        sel_kpi = st.selectbox("Indicateur de performance", cols_kpi)
        
        # Détection dynamique du nom de l'agence pour la légende
        label_col = next((c for c in df_stats.columns if any(k in c.lower() for k in ["établissement", "magasin", "agence"])), None)
        
        fig_stats = px.line(
            df_stats.sort_values(df_stats.columns[0]), 
            x=df_stats.columns[0], 
            y=sel_kpi, 
            color=label_col,
            title=f"Évolution : {sel_kpi}"
        )
        st.plotly_chart(fig_stats, use_container_width=True)
    else:
        st.info("Aucune donnée statistique détectée. Veuillez charger les fichiers correspondants.")

with tab2:
    if not df_avis.empty:
        st.subheader("Analyse de la satisfaction client")
        if 'Note_Std' in df_avis.columns:
            df_avis['Note_Std'] = pd.to_numeric(df_avis['Note_Std'], errors='coerce')
            
            c1, c2 = st.columns(2)
            c1.metric("Note Moyenne Globale", f"{df_avis['Note_Std'].mean():.2f} ⭐")
            c2.metric("Volume total d'avis", len(df_avis))

            # Graphique Temporel
            # On cherche la colonne date standardisée ou la première colonne
            d_col = 'Date_Std' if 'Date_Std' in df_avis.columns else df_avis.columns[0]
            df_avis_mensuel = df_avis.set_index(d_col).resample('M')['Note_Std'].mean().reset_index()
            
            fig_avis = px.area(df_avis_mensuel, x=d_col, y='Note_Std', title="Évolution de la note moyenne", range_y=[0,5])
            st.plotly_chart(fig_avis, use_container_width=True)
        else:
            st.error("La colonne 'Note' n'a pas été trouvée dans les fichiers d'avis.")
    else:
        st.info("Aucune donnée d'avis détectée (2021-2025).")