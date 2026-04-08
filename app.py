import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Human Immobilier - Business Intelligence", layout="wide")

# --- STYLES CSS ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- FONCTIONS DE TRAITEMENT ---

def load_all_data(files):
    all_avis = []
    all_stats = []
    
    for f in files:
        # On lit les premières lignes pour identifier le type
        preview = pd.read_excel(f, header=None, nrows=5)
        header_content = str(preview.iloc[2].values).lower()

        # TRAITEMENT STATS (Performances)
        if any(k in header_content for k in ["recherche", "action", "vue"]):
            df = pd.read_excel(f, header=None)
            h1 = df.iloc[1].ffill().fillna('')
            h2 = df.iloc[2].fillna('')
            df.columns = [f"{str(a)} - {str(b)}".strip(" -") for a, b in zip(h1, h2)]
            df = df.iloc[3:].copy()
            df['Source'] = 'Stats'
            all_stats.append(df)
            
        # TRAITEMENT AVIS (Réputation)
        else:
            df = pd.read_excel(f, skiprows=2)
            df.columns = [str(c).strip() for c in df.columns]
            # Mapping flexible
            mapping = {'Date': ['date'], 'Note': ['note', 'étoile'], 'Agence': ['établissement', 'agence']}
            for final, keys in mapping.items():
                for c in df.columns:
                    if any(k in c.lower() for k in keys):
                        df = df.rename(columns={c: final})
            df['Source'] = 'Avis'
            all_avis.append(df)
            
    return pd.concat(all_avis) if all_avis else pd.DataFrame(), \
           pd.concat(all_stats) if all_stats else pd.DataFrame()

# --- CHARGEMENT ---
files = st.sidebar.file_uploader("📥 Déposez vos exports Partoo (Avis & Stats)", accept_multiple_files=True)

if files:
    df_avis, df_stats = load_all_data(files)

    # Nettoyage des dates et types
    if not df_avis.empty:
        df_avis['Date'] = pd.to_datetime(df_avis['Date'], errors='coerce')
        df_avis['Note'] = pd.to_numeric(df_avis['Note'], errors='coerce')
    if not df_stats.empty:
        # On prend la première colonne comme date (Mois)
        date_col_stats = df_stats.columns[0]
        df_stats[date_col_stats] = pd.to_datetime(df_stats[date_col_stats], errors='coerce')
        # Conversion numérique des colonnes de données
        for col in df_stats.columns:
            if " - " in col: df_stats[col] = pd.to_numeric(df_stats[col], errors='coerce')

    # --- FILTRES ---
    st.sidebar.header("🔍 Facettes & Filtres")
    # Agence unique ou Groupe
    all_agences = sorted(df_avis['Agence'].unique().tolist()) if not df_avis.empty else []
    sel_agence = st.sidebar.multiselect("Filtrer par Agence", all_agences, default=all_agences[:5] if all_agences else [])

    # Application des filtres
    if sel_agence:
        df_avis_f = df_avis[df_avis['Agence'].isin(sel_agence)]
        # Pour les stats, on cherche la colonne établissement
        etab_col = next((c for c in df_stats.columns if "établissement" in c.lower()), None)
        df_stats_f = df_stats[df_stats[etab_col].isin(sel_agence)] if etab_col else df_stats
    else:
        df_avis_f, df_stats_f = df_avis, df_stats

    # --- DASHBOARD MAIN ---
    st.title("📈 Business Intelligence - E-Réputation")
    
    # 1. KPIs FLASH
    c1, c2, c3, c4 = st.columns(4)
    if not df_avis_f.empty:
        c1.metric("Score Moyen", f"{df_avis_f['Note'].mean():.2f} ⭐")
        c2.metric("Total Avis", f"{len(df_avis_f):,}")
    if not df_stats_f.empty:
        search_cols = [c for c in df_stats_f.columns if "recherche" in c.lower()]
        action_cols = [c for c in df_stats_f.columns if "action" in c.lower()]
        c3.metric("Recherches", f"{int(df_stats_f[search_cols].sum().sum()):,}")
        c4.metric("Actions Clients", f"{int(df_stats_f[action_cols].sum().sum()):,}")

    # 2. ONGLETS
    tab_rep, tab_perf = st.tabs(["⭐ Réputation & Satisfaction", "🚀 Visibilité & Attractivité"])

    with tab_rep:
        col_l, col_r = st.columns([2, 1])
        with col_l:
            st.subheader("Tendance de la note")
            df_m = df_avis_f.set_index('Date').resample('M')['Note'].mean().reset_index()
            fig = px.line(df_m, x='Date', y='Note', markers=True, range_y=[0,5], template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
        with col_r:
            st.subheader("Mix des Notes")
            fig_pie = px.pie(df_avis_f, names='Note', hole=0.4, color='Note', 
                             color_discrete_map={5:'#2ecc71', 4:'#9b59b6', 3:'#f1c40f', 2:'#e67e22', 1:'#e74c3c'})
            st.plotly_chart(fig_pie, use_container_width=True)

    with tab_perf:
        col_l, col_r = st.columns(2)
        with col_l:
            st.subheader("Tunnel : Vues vs Actions")
            views = [c for c in df_stats_f.columns if "vues" in c.lower()]
            acts = [c for c in df_stats_f.columns if "action" in c.lower()]
            df_v_a = df_stats_f.groupby(df_stats_f.columns[0])[[views[0], acts[0]]].sum().reset_index()
            fig_dual = go.Figure()
            fig_dual.add_trace(go.Bar(x=df_v_a[df_v_a.columns[0]], y=df_v_a[views[0]], name="Vues Google"))
            fig_dual.add_trace(go.Scatter(x=df_v_a[df_v_a.columns[0]], y=df_v_a[acts[0]], name="Actions", yaxis="y2"))
            fig_dual.update_layout(yaxis2=dict(overlaying='y', side='right'), template="plotly_white")
            st.plotly_chart(fig_dual, use_container_width=True)
            
        with col_r:
            st.subheader("Détail des Actions")
            actions_data = df_stats_f[acts].sum().reset_index()
            actions_data.columns = ['Action', 'Volume']
            fig_act = px.bar(actions_data, x='Volume', y='Action', orientation='h', text_auto='.2s')
            st.plotly_chart(fig_act, use_container_width=True)

else:
    st.info("💡 Chargez vos fichiers Excel pour générer le dashboard de pilotage.")