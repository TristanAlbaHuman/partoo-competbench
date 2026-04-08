import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Partoo BI Dashboard", layout="wide")

# --- STYLE CSS POUR REPRODUIRE L'INTERFACE PARTOO ---
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid #e1e4e8; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 1px solid #e1e4e8; }
    h2, h3 { color: #1a202c; }
    </style>
    """, unsafe_allow_html=True)

# --- FONCTIONS DE CHARGEMENT ---

def load_avis(files):
    all_df = []
    for f in files:
        # Format Avis : Titres en ligne 2
        df = pd.read_excel(f, skiprows=1)
        # Nettoyage colonnes
        df.columns = [str(c).strip() for c in df.columns]
        # Mapping strict
        mapping = {
            'date': ['date de création', 'date'],
            'note': ['rating', 'note', 'étoile'],
            'agence': ['nom de l\'établissement', 'établissement'],
            'reponse': ['réponse', 'reply']
        }
        for final, keys in mapping.items():
            for c in df.columns:
                if any(k in c.lower() for k in keys):
                    df = df.rename(columns={c: final})
                    break
        all_df.append(df)
    return pd.concat(all_df, ignore_index=True) if all_df else pd.DataFrame()

def load_stats(files):
    all_df = []
    for f in files:
        # Format Stats : Double Header (Ligne 1 et 2)
        df_raw = pd.read_excel(f, header=None)
        h1 = df_raw.iloc[0].ffill().fillna('')
        h2 = df_raw.iloc[1].fillna('')
        df_raw.columns = [f"{str(a)} {str(b)}".strip() for a, b in zip(h1, h2)]
        df = df_raw.iloc[2:].copy()
        
        # Identification de la date (souvent 1ère col)
        df = df.rename(columns={df.columns[0]: 'date', df.columns[3]: 'agence'})
        all_df.append(df)
    return pd.concat(all_df, ignore_index=True) if all_df else pd.DataFrame()

# --- SIDEBAR : DOUBLE LOADER ---
st.sidebar.title("🛠️ Configuration")

st.sidebar.subheader("1. Fichiers Avis")
files_avis = st.sidebar.file_uploader("Upload Avis (2021-2025)", type=["xlsx"], accept_multiple_files=True, key="u1")

st.sidebar.subheader("2. Fichiers Stats")
files_stats = st.sidebar.file_uploader("Upload Monthly Performance", type=["xlsx"], accept_multiple_files=True, key="u2")

# --- LOGIQUE DE DONNÉES ---
df_avis = load_avis(files_avis) if files_avis else pd.DataFrame()
df_stats = load_stats(files_stats) if files_stats else pd.DataFrame()

# --- INTERFACE PRINCIPALE ---
st.title("📊 Partoo Analytics - Human Immobilier")

tab1, tab2 = st.tabs(["⭐ Réputation & Avis", "🚀 Performance GMB"])

# --- ONGLET 1 : REPUTATION (Basé sur PARTOO1) ---
with tab1:
    if not df_avis.empty:
        df_avis['note'] = pd.to_numeric(df_avis['note'], errors='coerce')
        df_avis['date'] = pd.to_datetime(df_avis['date'], errors='coerce')
        
        # Filtre agence interne à l'onglet
        agences = sorted(df_avis['agence'].unique().tolist())
        sel_ag = st.multiselect("Filtrer les établissements", agences, default=agences[:3])
        df_res = df_avis[df_avis['agence'].isin(sel_ag)] if sel_ag else df_avis

        # KPIs
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Note Moyenne", f"{df_res['note'].mean():.2f} ⭐")
        c2.metric("Total Avis", len(df_res))
        
        # Taux de réponse
        has_rep = df_res['reponse'].notna().sum()
        taux = (has_rep / len(df_res)) * 100 if len(df_res) > 0 else 0
        c3.metric("Taux de réponse", f"{taux:.1f}%")
        c4.metric("Avis à traiter", len(df_res) - has_rep)

        col_l, col_r = st.columns([2, 1])
        with col_l:
            st.subheader("Répartition des notes")
            df_dist = df_res['note'].value_counts().sort_index(ascending=False).reset_index()
            fig_bar = px.bar(df_dist, x='count', y='note', orientation='h', 
                             color='note', color_continuous_scale='RdYlGn', 
                             text_auto=True)
            st.plotly_chart(fig_bar, use_container_width=True)
        
        with col_r:
            st.subheader("Derniers avis")
            st.dataframe(df_res[['date', 'agence', 'note']].sort_values('date', ascending=False).head(10), use_container_width=True)
    else:
        st.info("Utilisez le loader n°1 pour charger les données d'avis.")

# --- ONGLET 2 : PERFORMANCE (Basé sur PARTOO2/3) ---
with tab2:
    if not df_stats.empty:
        # Conversion numérique des colonnes de données
        for col in df_stats.columns:
            if any(k in col.lower() for k in ["vues", "recherche", "appels", "visites", "itinéraire"]):
                df_stats[col] = pd.to_numeric(df_stats[col], errors='coerce').fillna(0)
        
        # Sélections des colonnes
        vues_cols = [c for c in df_stats.columns if "vues" in c.lower()]
        actions_cols = [c for c in df_stats.columns if any(k in c.lower() for k in ["appels", "visites", "itinéraire"])]
        
        # KPIs
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Vues", f"{int(df_stats[vues_cols].sum().sum()):,}")
        c2.metric("Total Actions", f"{int(df_stats[actions_cols].sum().sum()):,}")
        c3.metric("Recherches", f"{int(df_stats.filter(like='recherche').sum().sum()):,}")

        col_l, col_r = st.columns(2)
        with col_l:
            st.subheader("Actions des utilisateurs")
            df_act = df_stats[actions_cols].sum().reset_index()
            df_act.columns = ['Action', 'Volume']
            fig_pie = px.pie(df_act, values='Volume', names='Action', hole=0.5)
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with col_r:
            st.subheader("Vues par plateforme")
            df_vues = df_stats[vues_cols].sum().reset_index()
            df_vues.columns = ['Source', 'Vues']
            fig_vues = px.bar(df_vues, x='Vues', y='Source', orientation='h', color='Source')
            st.plotly_chart(fig_vues, use_container_width=True)
            
        st.subheader("Détail par établissement")
        st.dataframe(df_stats.drop(columns=['date'], errors='ignore'), use_container_width=True)
    else:
        st.info("Utilisez le loader n°2 pour charger les données de performance.")