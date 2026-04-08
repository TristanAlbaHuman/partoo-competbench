import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from textblob import Blobber
from textblob_fr import PatternTagger, PatternAnalyzer

# Initialisation de l'analyseur de sentiment FR
try:
    tb = Blobber(pos_tagger=PatternTagger(), analyzer=PatternAnalyzer())
except:
    tb = None

st.set_page_config(page_title="Human BI - Pilotage Stratégique", layout="wide")

# --- FONCTION DE NETTOYAGE SÉCURISÉE ---
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
    return tb(str(text)).sentiment[0]

# --- LOADERS ---

def load_avis_data(files):
    all_df = []
    for f in files:
        df = pd.read_excel(f, skiprows=1) if f.name.endswith('.xlsx') else pd.read_csv(f, skiprows=1)
        df.columns = clean_column_list(df.columns)
        mapping = {
            'date_cr': ['date de création'], 'note': ['rating', 'note'],
            'agence': ['nom de l\'établissement'], 'verbatim': ['content', 'avis', 'commentaire'],
            'reponse': ['réponse']
        }
        for final, keys in mapping.items():
            for c in df.columns:
                if any(k in c.lower() for k in keys) and final not in df.columns:
                    df = df.rename(columns={c: final})
        if 'verbatim' in df.columns:
            df['sentiment'] = df['verbatim'].apply(get_sentiment)
        all_df.append(df)
    return pd.concat(all_df, ignore_index=True) if all_df else pd.DataFrame()

def load_stats_data(files):
    all_df = []
    for f in files:
        df_raw = pd.read_excel(f, header=None) if f.name.endswith('.xlsx') else pd.read_csv(f, header=None)
        h1 = df_raw.iloc[0].ffill().fillna('')
        h2 = df_raw.iloc[1].fillna('')
        df_raw.columns = clean_column_list([f"{str(a)} {str(b)}".strip() for a, b in zip(h1, h2)])
        df = df_raw.iloc[2:].copy()
        df = df.rename(columns={df.columns[0]: 'date', df.columns[3]: 'agence'})
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        for col in df.columns:
            if any(k in col.lower() for k in ['vues', 'recherche', 'appels', 'visites', 'itinéraire']):
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        all_df.append(df)
    return pd.concat(all_df, ignore_index=True) if all_df else pd.DataFrame()

# --- SIDEBAR ---
st.sidebar.title("🏢 Human BI Hub")
with st.sidebar.expander("📥 1. LOADER AVIS", expanded=True):
    u_avis = st.file_uploader("Fichiers Avis", type=["xlsx", "csv"], accept_multiple_files=True, key="av")
with st.sidebar.expander("📥 2. LOADER PERFORMANCE", expanded=True):
    u_stats = st.file_uploader("Fichiers Performance", type=["xlsx", "csv"], accept_multiple_files=True, key="st")

df_av = load_avis_data(u_avis) if u_avis else pd.DataFrame()
df_st = load_stats_data(u_stats) if u_stats else pd.DataFrame()

# --- RÉSOLUTION DU TYPEERROR (FILTRE BLINDÉ) ---
sel_ag = "Toutes"
if not df_av.empty or not df_st.empty:
    st.sidebar.divider()
    
    # Méthode robuste pour extraire les noms d'agences
    list_av = df_av['agence'].dropna().astype(str).unique().tolist() if (not df_av.empty and 'agence' in df_av.columns) else []
    list_st = df_st['agence'].dropna().astype(str).unique().tolist() if (not df_st.empty and 'agence' in df_st.columns) else []
    
    # On fusionne les sets, on nettoie les "nan" et on trie
    ag_set = set(list_av) | set(list_st)
    clean_ag_list = sorted([str(x) for x in ag_set if x and str(x).lower() != 'nan'])
    
    sel_ag = st.sidebar.selectbox("🎯 Agence à piloter", ["Toutes"] + clean_ag_list)

    if sel_ag != "Toutes":
        if not df_av.empty and 'agence' in df_av.columns:
            df_av = df_av[df_av['agence'].astype(str) == sel_ag]
        if not df_st.empty and 'agence' in df_st.columns:
            df_st = df_st[df_st['agence'].astype(str) == sel_ag]

# --- DASHBOARD ---
st.title(f"🛡️ Pilotage : {sel_ag}")

if df_av.empty and df_st.empty:
    st.info("Veuillez charger les fichiers dans la barre latérale.")
else:
    tab1, tab2 = st.tabs(["⭐ RÉPUTATION & SENTIMENT", "🚀 VISIBILITÉ MAPS"])

    # --- TAB 1 : REPUTATION ---
    with tab1:
        st.header("Analyse de la Satisfaction")
        
        # 1. Histogramme Note Mensuelle
        st.subheader("Évolution de la note moyenne")
        df_av['date_cr'] = pd.to_datetime(df_av['date_cr'], errors='coerce')
        df_av['Mois'] = df_av['date_cr'].dt.to_period('M').dt.to_timestamp()
        evol = df_av.groupby('Mois')['note'].mean().reset_index()
        fig_evol = px.bar(evol, x='Mois', y='note', color='note', color_continuous_scale='RdYlGn', range_y=[0,5], labels={'note':'Note Moyenne'})
        st.plotly_chart(fig_evol, use_container_width=True)

        col1, col2 = st.columns([1, 1])
        
        # 2. Camembert
        with col1:
            st.subheader("Répartition des Avis")
            fig_pie = px.pie(df_av, names='note', hole=0.4, color='note', 
                             color_discrete_map={5:'#27ae60', 4:'#2ecc71', 3:'#f1c40f', 2:'#e67e22', 1:'#e74c3c'})
            st.plotly_chart(fig_pie, use_container_width=True)
            st.caption("L'objectif est d'avoir > 80% de notes 4 et 5.")

        # 3. Sentiment
        with col2:
            st.subheader("Analyse du Sentiment (IA)")
            avg_sent = df_av['sentiment'].mean() if 'sentiment' in df_av.columns else 0
            st.metric("Humeur Globale", f"{avg_sent:.2f}", delta="Positif" if avg_sent > 0 else "Négatif")
            st.markdown("""
            **Comment améliorer ?**
            - Sollicitez des avis dès la signature du compromis.
            - Répondez aux avis négatifs en moins de 24h pour montrer votre sérieux.
            """)

        st.divider()
        st.subheader("💬 Verbatims : Ce que disent vos clients")
        if 'verbatim' in df_av.columns:
            col_pos, col_neg = st.columns(2)
            with col_pos:
                st.success("**Top Avis Positifs**")
                st.table(df_av.sort_values('sentiment', ascending=False).head(3)[['note', 'verbatim']])
            with col_neg:
                st.error("**Avis nécessitant une attention**")
                st.table(df_av.sort_values('sentiment', ascending=True).head(3)[['note', 'verbatim']])

    # --- TAB 2 : VISIBILITÉ ---
    with tab2:
        st.header("Analyse de la Présence Google")
        if not df_st.empty:
            # Graphiques empilés
            v_cols = [c for c in df_st.columns if 'vues' in c.lower()]
            i_cols = [c for c in df_st.columns if any(k in c.lower() for k in ['appels', 'site web', 'itinéraire'])]

            st.subheader("1. Volume de Visibilité (Où les gens vous voient)")
            fig_v = px.line(df_st.sort_values('date'), x='date', y=v_cols, title="Vues Google Search vs Maps")
            st.plotly_chart(fig_v, use_container_width=True)
            
            st.subheader("2. Interactions (Ce que les gens font)")
            fig_i = px.bar(df_st.sort_values('date'), x='date', y=i_cols, barmode='group', title="Appels, Itinéraires et Clics Web")
            st.plotly_chart(fig_i, use_container_width=True)

            st.info("""
            **💡 Optimisations GBP prioritaires :**
            - **Itinéraires bas ?** Ajoutez des photos de la vitrine et de l'environnement proche pour aider au repérage.
            - **Vues Search faibles ?** Publiez un 'Post Google' chaque semaine avec vos nouveaux biens.
            - **Appels faibles ?** Vérifiez que vos horaires sont à jour, surtout les jours fériés.
            """)
        else:
            st.warning("Chargez les fichiers de performance pour voir l'analyse SEO.")