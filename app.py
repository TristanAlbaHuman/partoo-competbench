import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from textblob import Blobber
from textblob_fr import PatternTagger, PatternAnalyzer

# Initialisation de l'analyseur de sentiment (Français)
try:
    tb = Blobber(pos_tagger=PatternTagger(), analyzer=PatternAnalyzer())
except Exception:
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

# --- FONCTIONS DE NETTOYAGE ---

def clean_column_list(column_names):
    new_cols = []
    seen = {}
    for c in column_names:
        c_str = str(c).strip().replace('\n', ' ')
        if c_str in seen:
            seen[c_str] += 1
            new_cols.append(f"{c_str}_{seen[c_str]}")
        else:
            seen[c_str] = 0
            new_cols.append(c_str)
    return new_cols

def get_sentiment(text):
    if not tb or pd.isna(text) or str(text).strip() == "": return 0
    try:
        return tb(str(text)).sentiment[0]
    except:
        return 0

# --- LOADERS ---

def load_avis_data(files):
    all_df = []
    for f in files:
        df = pd.read_excel(f, skiprows=1) if f.name.endswith('.xlsx') else pd.read_csv(f, skiprows=1)
        df.columns = clean_column_list(df.columns)
        mapping = {
            'date_cr': ['date de création'], 'note': ['rating', 'note'],
            'agence': ['nom de l\'établissement', 'agence'], 'groupe': ['groupes'],
            'verbatim': ['content', 'avis', 'commentaire'],
            'reponse': ['réponse'], 'date_rep': ['date de la réponse']
        }
        for final, keys in mapping.items():
            for c in df.columns:
                if any(k in c.lower() for k in keys) and final not in df.columns:
                    df = df.rename(columns={c: final})
        if 'verbatim' in df.columns and tb:
            df['sentiment'] = df['verbatim'].apply(get_sentiment)
        all_df.append(df)
    return pd.concat(all_df, ignore_index=True) if all_df else pd.DataFrame()

def load_performance_data(files):
    all_df = []
    for f in files:
        df_raw = pd.read_excel(f, header=None) if f.name.endswith('.xlsx') else pd.read_csv(f, header=None)
        h1 = df_raw.iloc[0].ffill().fillna('')
        h2 = df_raw.iloc[1].fillna('')
        combined_names = [f"{str(a)} {str(b)}".strip() for a, b in zip(h1, h2)]
        df_raw.columns = clean_column_list(combined_names)
        df = df_raw.iloc[2:].copy()
        df = df.rename(columns={df.columns[0]: 'date', df.columns[3]: 'agence', df.columns[5]: 'groupe'})
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        for col in df.columns:
            if any(k in col.lower() for k in ['vues', 'recherche', 'appels', 'visites', 'itinéraire']):
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        all_df.append(df)
    return pd.concat(all_df, ignore_index=True) if all_df else pd.DataFrame()

# --- SIDEBAR ---
st.sidebar.title("🏢 Human BI Engine")

with st.sidebar.expander("📥 1. LOADER AVIS", expanded=True):
    u_avis = st.file_uploader("Fichiers Avis", type=["xlsx", "csv"], accept_multiple_files=True, key="avis_up")

with st.sidebar.expander("📥 2. LOADER PERFORMANCE", expanded=True):
    u_stats = st.file_uploader("Fichiers Performance", type=["xlsx", "csv"], accept_multiple_files=True, key="stats_up")

df_av = load_avis_data(u_avis) if u_avis else pd.DataFrame()
df_st = load_performance_data(u_stats) if u_stats else pd.DataFrame()

# --- FILTRES (CORRECTION DU TYPEERROR ICI) ---
if not df_av.empty or not df_st.empty:
    st.sidebar.divider()
    
    # Récupération des agences de façon sécurisée (on force tout en string pour le tri)
    list_ag_av = df_av['agence'].astype(str).dropna().unique().tolist() if (not df_av.empty and 'agence' in df_av.columns) else []
    list_ag_st = df_st['agence'].astype(str).dropna().unique().tolist() if (not df_st.empty and 'agence' in df_st.columns) else []
    
    all_ag = sorted(list(set(list_ag_av + list_ag_st)))
    
    sel_ag = st.sidebar.selectbox("🎯 Agence à piloter", ["Toutes"] + all_ag)

    if sel_ag != "Toutes":
        if not df_av.empty and 'agence' in df_av.columns:
            df_av = df_av[df_av['agence'].astype(str) == sel_ag]
        if not df_st.empty and 'agence' in df_st.columns:
            df_st = df_st[df_st['agence'].astype(str) == sel_ag]

# --- DASHBOARD ---
st.title("🛡️ Pilotage Direction - Human Immobilier")

if df_av.empty and df_st.empty:
    st.info("Veuillez charger les fichiers dans la barre latérale.")
else:
    # --- PLAN D'ACTION ---
    st.subheader("📋 Plan d'Action Directeur")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<div class='action-card'><strong>🚀 Présence & SEO</strong><br>", unsafe_allow_html=True)
        if not df_st.empty:
            vues = df_st.filter(like='vues').sum().sum()
            iti = df_st.filter(like='itinéraire').sum().sum()
            ratio = (iti/vues*100) if vues > 0 else 0
            if ratio < 3: st.write(f"⚠️ Conversion Itinéraire faible ({ratio:.1f}%). Revoyez vos photos GMB.")
            else: st.write(f"✅ Excellente attractivité ({ratio:.1f}%).")
        else: st.write("Aucune donnée de performance chargée.")
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("<div class='action-card'><strong>⭐ E-Réputation</strong><br>", unsafe_allow_html=True)
        if not df_av.empty:
            no_rep = df_av['reponse'].isna().sum() if 'reponse' in df_av.columns else 0
            if no_rep > 0: st.write(f"🚨 {no_rep} avis n'ont pas de réponse !")
            if 'note' in df_av.columns and df_av['note'].mean() < 4.5: st.write("📉 Note moyenne < 4.5.")
        else: st.write("Aucune donnée d'avis chargée.")
        st.markdown("</div>", unsafe_allow_html=True)

    # --- TABS ---
    t1, t2, t3 = st.tabs(["⭐ Réputation & Sentiment", "📈 Visibilité Maps", "🏆 Benchmark"])

    with t1:
        if not df_av.empty:
            m1, m2, m3 = st.columns(3)
            m1.metric("Note Moyenne", f"{df_av['note'].mean():.2f} ⭐")
            if 'sentiment' in df_av.columns:
                m2.metric("Indice Sentiment", f"{df_av['sentiment'].mean():.2f}")
            m3.metric("Total Avis", len(df_av))
            
            df_av['Mois'] = pd.to_datetime(df_av['date_cr']).dt.to_period('M').dt.to_timestamp()
            evol = df_av.groupby('Mois')['note'].mean().reset_index()
            st.plotly_chart(px.line(evol, x='Mois', y='note', markers=True, range_y=[0,5], title="Tendance satisfaction"), use_container_width=True)

    with t2:
        if not df_st.empty:
            v_cols = [c for c in df_st.columns if 'vues' in c.lower()]
            i_cols = [c for c in df_st.columns if any(k in c.lower() for k in ['appels', 'site web', 'itinéraire'])]
            
            col_l, col_r = st.columns(2)
            with col_l:
                st.subheader("Source de Visibilité")
                st.plotly_chart(px.line(df_st, x='date', y=v_cols), use_container_width=True)
            with col_r:
                st.subheader("Actions Clients")
                st.plotly_chart(px.bar(df_st, x='date', y=i_cols), use_container_width=True)

    with t3:
        if not df_av.empty:
            st.subheader("Benchmark Agences du Groupe")
            bench = df_av.groupby('agence').agg({'note':'mean', 'date_cr':'count'}).reset_index()
            st.dataframe(bench.sort_values('note', ascending=False), use_container_width=True)