import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from textblob import Blobber
from textblob_fr import PatternTagger, PatternAnalyzer

# Initialisation de l'analyseur de sentiment (Français)
try:
    tb = Blobber(pos_tagger=PatternTagger(), analyzer=PatternAnalyzer())
except:
    tb = None

st.set_page_config(page_title="Human BI - Direction Hub", layout="wide")

# --- DESIGN & CSS ---
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 10px; border: 1px solid #e1e4e8; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .action-card { padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1rem; border-left: 5px solid #ff4b4b; background-color: #ffffff; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { background-color: #f1f3f6; border-radius: 4px 4px 0 0; padding: 10px 20px; font-weight: 600; }
    .stTabs [aria-selected="true"] { background-color: #ffffff; border-top: 3px solid #ff4b4b; color: #ff4b4b !important; }
    </style>
    """, unsafe_allow_html=True)

# --- FONCTIONS DE TRAITEMENT ---

def get_sentiment(text):
    if not tb or pd.isna(text) or str(text).strip() == "": return 0
    return tb(str(text)).sentiment[0]

def clean_df_columns(df):
    cols = []
    seen = {}
    for c in df.columns:
        c_str = str(c).strip().replace('\n', ' ')
        if c_str in seen:
            seen[c_str] += 1
            cols.append(f"{c_str}_{seen[c_str]}")
        else:
            seen[c_str] = 0
            cols.append(c_str)
    df.columns = cols
    return df

def load_avis_data(files):
    all_df = []
    for f in files:
        df = pd.read_excel(f, skiprows=1)
        df = clean_df_columns(df)
        mapping = {
            'date_cr': ['date de création', 'creation date'],
            'note': ['rating', 'note', 'étoile'],
            'agence': ['nom de l\'établissement', 'agence'],
            'groupe': ['groupes', 'section'],
            'verbatim': ['content', 'avis', 'commentaire'],
            'reponse': ['réponse', 'reply'],
            'date_rep': ['date de la réponse']
        }
        for final, keys in mapping.items():
            for c in df.columns:
                if any(k in c.lower() for k in keys) and final not in df.columns:
                    df = df.rename(columns={c: final})
        
        if 'verbatim' in df.columns and tb:
            df['sentiment'] = df['verbatim'].apply(get_sentiment)
        all_df.append(df)
    return pd.concat(all_df, ignore_index=True) if all_df else pd.DataFrame()

def load_stats_data(files):
    all_df = []
    for f in files:
        df_raw = pd.read_excel(f, header=None)
        h1 = df_raw.iloc[0].ffill().fillna('')
        h2 = df_raw.iloc[1].fillna('')
        df_raw.columns = clean_df_columns(pd.Index([f"{str(a)} {str(b)}".strip() for a, b in zip(h1, h2)]))
        df = df_raw.iloc[2:].copy()
        df = df.rename(columns={df.columns[0]: 'date', df.columns[3]: 'agence', df.columns[5]: 'groupe'})
        
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        for col in df.columns:
            if any(k in col.lower() for k in ['vues', 'recherche', 'appels', 'visites', 'itinéraire']):
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        all_df.append(df)
    return pd.concat(all_df, ignore_index=True) if all_df else pd.DataFrame()

# --- SIDEBAR & LOADERS ---
st.sidebar.title("🏢 Human BI Engine")

with st.sidebar.expander("📥 1. LOADER AVIS (2021-2025)", expanded=True):
    u_avis = st.file_uploader("Fichiers Avis", type=["xlsx"], accept_multiple_files=True, key="up_av")

with st.sidebar.expander("📥 2. LOADER STATS (2024-2025)", expanded=True):
    u_stats = st.file_uploader("Fichiers Performance", type=["xlsx"], accept_multiple_files=True, key="up_st")

df_av = load_avis_data(u_avis) if u_avis else pd.DataFrame()
df_st = load_stats_data(u_stats) if u_stats else pd.DataFrame()

# --- FILTRES HIÉRARCHIQUES ---
if not df_av.empty or not df_st.empty:
    st.sidebar.divider()
    st.sidebar.subheader("🔍 Filtrage")
    
    # Années
    years = []
    if not df_av.empty: years += df_av['date_cr'].dt.year.dropna().unique().tolist()
    if not df_st.empty: years += df_st['date'].dt.year.dropna().unique().tolist()
    sel_years = st.sidebar.multiselect("Années", sorted(list(set(years)), reverse=True), default=sorted(list(set(years)))[-1:])

    # Agence / Groupe
    all_ag = sorted(list(set(df_av['agence'].dropna().unique().tolist() if not df_av.empty else []) + 
                          (df_st['agence'].dropna().unique().tolist() if not df_st.empty else [])))
    sel_ag = st.sidebar.selectbox("🎯 Agence à piloter", ["Toutes"] + all_ag)

    # Application
    if sel_years:
        if not df_av.empty: df_av = df_av[df_av['date_cr'].dt.year.isin(sel_years)]
        if not df_st.empty: df_st = df_st[df_st['date'].dt.year.isin(sel_years)]
    if sel_ag != "Toutes":
        if not df_av.empty: df_av = df_av[df_av['agence'] == sel_ag]
        if not df_st.empty: df_st = df_st[df_st['agence'] == sel_ag]

# --- DASHBOARD ---
st.title("🛡️ Pilotage Stratégique - Human Immobilier")

if df_av.empty and df_st.empty:
    st.info("👋 Veuillez charger vos fichiers Avis et Performance dans la barre latérale.")
else:
    # --- PLAN D'ACTION (LOGIQUE DIRECTEUR) ---
    st.subheader("📋 Plan d'Action Directeur")
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("<div class='action-card'><strong>🚀 Présence & SEO</strong><br>", unsafe_allow_html=True)
        if not df_st.empty:
            vues = df_st.filter(like='vues').sum().sum()
            iti = df_st.filter(like='itinéraire').sum().sum()
            ratio = (iti/vues*100) if vues > 0 else 0
            if ratio < 3: st.write(f"⚠️ Attractivité faible ({ratio:.1f}%) : Vos photos ou horaires ne déclenchent pas assez d'itinéraires.")
            else: st.write(f"✅ Conversion saine ({ratio:.1f}%) : Votre fiche transforme bien les vues en visites.")
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("<div class='action-card'><strong>⭐ E-Réputation & Care</strong><br>", unsafe_allow_html=True)
        if not df_av.empty:
            no_rep = df_av['reponse'].isna().sum()
            if no_rep > 0: st.write(f"🚨 Urgent : {no_rep} avis n'ont pas encore de réponse.")
            if df_av['note'].mean() < 4.2: st.write("📉 Score < 4.2 : Campagne de récolte d'avis positifs recommandée.")
            else: st.write("✅ Note excellente : Maintenir la qualité de service.")
        st.markdown("</div>", unsafe_allow_html=True)

    # --- ONGLETS ---
    t1, t2, t3 = st.tabs(["⭐ Réputation & Sentiment", "📈 Performance SEO", "🏆 Benchmark"])

    with t1:
        k1, k2, k3, k4 = st.columns(4)
        if not df_av.empty:
            k1.metric("Note Moyenne", f"{df_av['note'].mean():.2f} ⭐")
            k2.metric("Taux de Réponse", f"{(df_av['reponse'].notna().mean()*100):.1f}%")
            if 'sentiment' in df_av.columns:
                k3.metric("Indice Sentiment", f"{df_av['sentiment'].mean():.2f}")
            k4.metric("Volume Avis", f"{len(df_av):,}")

            col_l, col_r = st.columns([2, 1])
            with col_l:
                df_av['Mois'] = df_av['date_cr'].dt.to_period('M').dt.to_timestamp()
                evol = df_av.groupby('Mois')['note'].mean().reset_index()
                st.plotly_chart(px.line(evol, x='Mois', y='note', markers=True, title="Évolution Satisfaction", range_y=[0,5]), use_container_width=True)
            with col_r:
                st.plotly_chart(px.pie(df_av, names='note', hole=0.5, title="Mix Étoiles"), use_container_width=True)

    with t2:
        if not df_st.empty:
            v_cols = [c for c in df_st.columns if 'vues' in c.lower()]
            i_cols = [c for c in df_st.columns if any(k in c.lower() for k in ['appels', 'visites', 'itinéraire'])]
            
            st.subheader("Tunnel : Visibilité vs Actions")
            df_st['Mois'] = df_st['date'].dt.to_period('M').dt.to_timestamp()
            df_g = df_st.groupby('Mois').agg({v_cols[0]:'sum', i_cols[0]:'sum'}).reset_index()
            
            fig = go.Figure()
            fig.add_trace(go.Bar(x=df_g['Mois'], y=df_g[v_cols[0]], name="Vues Google"))
            fig.add_trace(go.Scatter(x=df_g['Mois'], y=df_g[i_cols[0]], name="Actions", yaxis="y2", line=dict(color='orange', width=3)))
            fig.update_layout(yaxis2=dict(overlaying='y', side='right'), title="Corrélation Vues / Actions")
            st.plotly_chart(fig, use_container_width=True)

    with t3:
        if not df_av.empty:
            st.subheader("Benchmark Agences")
            bench = df_av.groupby('agence').agg({'note':'mean', 'agence':'count'}).rename(columns={'agence':'Volume'}).reset_index()
            st.dataframe(bench.sort_values('note', ascending=False), use_container_width=True)