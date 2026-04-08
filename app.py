import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Configuration de la page
st.set_page_config(page_title="Human BI - Direction Dashboard", layout="wide")

# --- STYLE CSS (Look & Feel Partoo) ---
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid #e1e4e8; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; }
    .main { background-color: #f0f2f6; }
    </style>
    """, unsafe_allow_html=True)

# --- FONCTIONS DE TRAITEMENT ---

def process_avis(files):
    """Traitement des exports 'Avis' (skip de la ligne 1, header ligne 2)"""
    all_df = []
    for f in files:
        # On lit en sautant la première ligne de déco de Partoo
        df = pd.read_excel(f, skiprows=1)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Mapping des noms de colonnes pour uniformiser 2021-2025
        mapping = {
            'date_creation': ['date de création'],
            'note': ['rating', 'note'],
            'agence': ['nom de l\'établissement'],
            'groupe': ['groupes', 'section'],
            'date_reponse': ['date de la réponse'],
            'reponse': ['réponse']
        }
        for final, keys in mapping.items():
            for c in df.columns:
                if any(k in c.lower() for k in keys) and final not in df.columns:
                    df = df.rename(columns={c: final})
        
        # Nettoyage types
        if 'date_creation' in df.columns:
            df['date_creation'] = pd.to_datetime(df['date_creation'], errors='coerce')
        if 'note' in df.columns:
            df['note'] = pd.to_numeric(df['note'], errors='coerce')
        
        all_df.append(df)
    
    if not all_df: return pd.DataFrame()
    return pd.concat(all_df, ignore_index=True)

def process_stats(files):
    """Traitement des exports 'Performance' (Double header)"""
    all_df = []
    for f in files:
        # On charge les deux lignes d'entête
        df_raw = pd.read_excel(f, header=None)
        # Fusion intelligente des titres (ex: Vues + Ordinateur)
        h1 = df_raw.iloc[0].ffill().fillna('')
        h2 = df_raw.iloc[1].fillna('')
        df_raw.columns = [f"{str(a)} {str(b)}".strip() for a, b in zip(h1, h2)]
        
        df = df_raw.iloc[2:].copy()
        
        # Renommage des colonnes pivots
        df = df.rename(columns={df.columns[0]: 'date', df.columns[3]: 'agence'})
        
        # Conversion numérique des colonnes KPI (Vues, Appels, etc.)
        for col in df.columns:
            if any(k in col.lower() for k in ['vues', 'recherche', 'appels', 'visites', 'itinéraire']):
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        all_df.append(df)
        
    if not all_df: return pd.DataFrame()
    return pd.concat(all_df, ignore_index=True)

# --- SIDEBAR : DOUBLE LOADER & FILTRES ---
st.sidebar.title("🏢 Human BI Dashboard")

with st.sidebar.expander("⭐ CHARGER LES AVIS (2021-25)", expanded=True):
    files_av = st.file_uploader("Fichiers Avis", type=["xlsx"], accept_multiple_files=True, key="av")

with st.sidebar.expander("🚀 CHARGER LES STATS (2024-25)", expanded=True):
    files_st = st.file_uploader("Fichiers Performance", type=["xlsx"], accept_multiple_files=True, key="st")

# Chargement initial
df_av = process_avis(files_av) if files_av else pd.DataFrame()
df_st = process_stats(files_st) if files_stats else pd.DataFrame()

# --- LOGIQUE DE FACETTES (FILTRES) ---
st.sidebar.divider()
st.sidebar.subheader("🔍 Filtrage")

if not df_av.empty or not df_st.empty:
    # 1. Filtre Années
    all_dates = []
    if not df_av.empty: all_dates += df_av['date_creation'].dt.year.dropna().unique().tolist()
    if not df_st.empty: all_dates += df_st['date'].dt.year.dropna().unique().tolist()
    years = sorted(list(set(all_dates)), reverse=True)
    sel_years = st.sidebar.multiselect("Années", years, default=years[:2])

    # 2. Filtre Agences
    list_ag = []
    if not df_av.empty: list_ag += df_av['agence'].unique().tolist()
    if not df_st.empty: list_ag += df_st['agence'].unique().tolist()
    list_ag = sorted(list(set([str(a) for a in list_ag if str(a) != 'nan'])))
    sel_ag = st.sidebar.multiselect("Agences", list_ag)

    # Application des filtres
    if sel_years:
        if not df_av.empty: df_av = df_av[df_av['date_creation'].dt.year.isin(sel_years)]
        if not df_st.empty: df_st = df_st[df_st['date'].dt.year.isin(sel_years)]
    if sel_ag:
        if not df_av.empty: df_av = df_av[df_av['agence'].isin(sel_ag)]
        if not df_st.empty: df_st = df_st[df_st['agence'].isin(sel_ag)]

# --- INTERFACE PRINCIPALE ---
st.title("📊 Tableau de Bord Direction - Human Immobilier")

if df_av.empty and df_st.empty:
    st.info("Veuillez charger vos fichiers dans la barre latérale pour activer le dashboard.")
else:
    tab1, tab2 = st.tabs(["⭐ E-RÉPUTATION & CARE", "🚀 PERFORMANCE & ATTRACTIVITÉ"])

    # --- ONGLET 1 : RÉPUTATION ---
    with tab1:
        if not df_av.empty:
            # KPIs
            df_av['date_reponse'] = pd.to_datetime(df_av['date_reponse'], errors='coerce')
            df_av['delai'] = (df_av['date_reponse'] - df_av['date_creation']).dt.days
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Note Moyenne", f"{df_av['note'].mean():.2f} ⭐")
            c2.metric("Taux de Réponse", f"{(df_av['reponse'].notna().mean()*100):.1f}%")
            c3.metric("Délai de Réponse", f"{df_av['delai'].mean():.1f} j (moy)")
            c4.metric("Volume Avis", f"{len(df_av):,}")

            col_l, col_r = st.columns([2, 1])
            with col_l:
                st.subheader("Évolution de la Satisfaction")
                df_av['Mois'] = df_av['date_creation'].dt.to_period('M').dt.to_timestamp()
                evol = df_av.groupby('Mois')['note'].mean().reset_index()
                fig = px.line(evol, x='Mois', y='note', markers=True, range_y=[3, 5], template="none")
                st.plotly_chart(fig, use_container_width=True)
            
            with col_r:
                st.subheader("Répartition Étoiles")
                fig_pie = px.pie(df_av, names='note', hole=0.5, color='note')
                st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.warning("Chargez les fichiers 'Avis' pour voir cette section.")

    # --- ONGLET 2 : PERFORMANCE ---
    with tab2:
        if not df_st.empty:
            # Détection des colonnes KPI
            vues_cols = [c for c in df_st.columns if 'vues' in c.lower()]
            actions_cols = [c for c in df_st.columns if any(k in c.lower() for k in ['appels', 'visites', 'itinéraire'])]
            
            total_vues = df_st[vues_cols].sum().sum()
            total_actions = df_st[actions_cols].sum().sum()
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Visibilité (Vues Totales)", f"{total_vues:,.0f}")
            c2.metric("Attractivité (Actions)", f"{total_actions:,.0f}")
            c3.metric("Taux de Conversion", f"{(total_actions/total_vues*100):.2f}%" if total_vues > 0 else "0%")

            col_l, col_r = st.columns(2)
            with col_l:
                st.subheader("Tunnel d'Attractivité (Vues vs Actions)")
                df_st['Mois'] = df_st['date'].dt.to_period('M').dt.to_timestamp()
                tunnel = df_st.groupby('Mois').agg({vues_cols[0]:'sum', actions_cols[0]:'sum'}).reset_index()
                
                fig_t = go.Figure()
                fig_t.add_trace(go.Bar(x=tunnel['Mois'], y=tunnel[vues_cols[0]], name="Vues Google", marker_color='#3b82f6'))
                fig_t.add_trace(go.Scatter(x=tunnel['Mois'], y=tunnel[actions_cols[0]], name="Actions", yaxis="y2", line=dict(color='#f59e0b', width=4)))
                fig_t.update_layout(yaxis2=dict(overlaying='y', side='right'), template="none")
                st.plotly_chart(fig_t, use_container_width=True)
            
            with col_r:
                st.subheader("Répartition des Actions")
                act_sums = df_st[actions_cols].sum().reset_index()
                act_sums.columns = ['Action', 'Volume']
                fig_p = px.pie(act_sums, values='Volume', names='Action', hole=0.4)
                st.plotly_chart(fig_p, use_container_width=True)
        else:
            st.warning("Chargez les fichiers 'Monthly Performance' pour voir cette section.")