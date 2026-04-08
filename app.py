import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from textblob import Blobber
from textblob_fr import PatternTagger, PatternAnalyzer

# Initialisation Sentiment
try:
    tb = Blobber(pos_tagger=PatternTagger(), analyzer=PatternAnalyzer())
except:
    tb = None

st.set_page_config(page_title="Human BI - Pilotage GMB", layout="wide")

# --- FONCTIONS TECHNIQUES ---

def clean_cols(df_cols):
    new_cols = []
    seen = {}
    for c in df_cols:
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

def load_avis(files):
    all_df = []
    for f in files:
        df = pd.read_excel(f, skiprows=1)
        df.columns = clean_cols(df.columns)
        mapping = {'date': ['date de création'], 'note': ['rating', 'note'], 'agence': ['nom de l\'établissement'], 'verbatim': ['content', 'avis', 'commentaire'], 'reponse': ['réponse']}
        for final, keys in mapping.items():
            for c in df.columns:
                if any(k in c.lower() for k in keys) and final not in df.columns:
                    df = df.rename(columns={c: final})
        if 'verbatim' in df.columns:
            df['sentiment'] = df['verbatim'].apply(get_sentiment)
        all_df.append(df)
    return pd.concat(all_df, ignore_index=True) if all_df else pd.DataFrame()

def load_stats(files):
    all_df = []
    for f in files:
        df_raw = pd.read_excel(f, header=None)
        h1 = df_raw.iloc[0].ffill().fillna('')
        h2 = df_raw.iloc[1].fillna('')
        df_raw.columns = clean_cols([f"{str(a)} {str(b)}".strip() for a, b in zip(h1, h2)])
        df = df_raw.iloc[2:].copy()
        df = df.rename(columns={df.columns[0]: 'date', df.columns[3]: 'agence', df.columns[5]: 'groupe'})
        for col in df.columns:
            if any(k in col.lower() for k in ['vues', 'recherche', 'appels', 'visites', 'itinéraire']):
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        all_df.append(df)
    return pd.concat(all_df, ignore_index=True) if all_df else pd.DataFrame()

# --- SIDEBAR & FILTRES ---
st.sidebar.title("🏢 Human BI Engine")
u_avis = st.sidebar.file_uploader("📥 Avis (2021-25)", type=["xlsx"], accept_multiple_files=True)
u_stats = st.sidebar.file_uploader("📥 Stats (2024-25)", type=["xlsx"], accept_multiple_files=True)

df_av = load_avis(u_avis) if u_avis else pd.DataFrame()
df_st = load_stats(u_stats) if u_stats else pd.DataFrame()

if not df_av.empty or not df_st.empty:
    st.sidebar.divider()
    all_ag = sorted(list(set(df_av['agence'].astype(str).unique().tolist() if not df_av.empty else []) + (df_st['agence'].astype(str).unique().tolist() if not df_st.empty else [])))
    sel_ag = st.sidebar.selectbox("🎯 Agence à piloter", ["Toutes"] + all_ag)
    
    if sel_ag != "Toutes":
        if not df_av.empty: df_av = df_av[df_av['agence'] == sel_ag]
        if not df_st.empty: df_st = df_st[df_st['agence'] == sel_ag]

# --- DASHBOARD ---
st.title("🛡️ Dashboard Stratégique Human Immobilier")

if df_av.empty and df_st.empty:
    st.info("Chargez les fichiers dans la sidebar pour activer l'analyse.")
else:
    tab1, tab2 = st.tabs(["⭐ RÉPUTATION & SENTIMENT", "🚀 VISIBILITÉ MAPS"])

    # --- ONGLET 1 : REPUTATION ---
    with tab1:
        st.header("Analyse de la Satisfaction Client")
        
        c1, c2 = st.columns([2, 1])
        
        with c1:
            st.subheader("Histogramme de la note moyenne par mois")
            df_av['date'] = pd.to_datetime(df_av['date'], errors='coerce')
            df_av['Mois'] = df_av['date'].dt.to_period('M').dt.to_timestamp()
            evol = df_av.groupby('Mois')['note'].mean().reset_index()
            fig_hist = px.bar(evol, x='Mois', y='note', color='note', color_continuous_scale='RdYlGn', range_y=[0,5])
            st.plotly_chart(fig_hist, use_container_width=True)
            
        with c2:
            st.subheader("Répartition des Avis")
            fig_pie = px.pie(df_av, names='note', hole=0.4, color='note', color_discrete_map={5:'#27ae60', 4:'#2ecc71', 3:'#f1c40f', 2:'#e67e22', 1:'#e74c3c'})
            st.plotly_chart(fig_pie, use_container_width=True)

        st.divider()
        st.subheader("💬 Analyse des Sentiments & Verbatims")
        col_sent1, col_sent2 = st.columns([1, 2])
        
        with col_sent1:
            avg_sent = df_av['sentiment'].mean()
            st.metric("Score de Sentiment", f"{avg_sent:.2f}", delta="Positif" if avg_sent > 0 else "Négatif")
            st.info("""
            **C'est quoi ?** L'analyse de sentiment scanne les mots utilisés. 
            - Proche de 1 : Les clients sont ravis (mots : 'super', 'merci').
            - Proche de -1 : Colère ou déception.
            """)
        
        with col_sent2:
            st.write("**Exemples concrets (Avis récents) :**")
            # Top 3 Positifs et Top 3 Négatifs
            if 'verbatim' in df_av.columns:
                samples = pd.concat([df_av.sort_values('sentiment').head(3), df_av.sort_values('sentiment').tail(3)])
                st.dataframe(samples[['note', 'verbatim', 'sentiment']], use_container_width=True)

        with st.expander("💡 Comment améliorer votre Réputation sur Google ?"):
            st.write("""
            1. **Le taux de réponse :** Répondez à 100% des avis, même les 5/5 sans texte. Google adore la réactivité.
            2. **Mots-clés dans les réponses :** Intégrez naturellement des mots comme "Vente appartement [Ville]" dans vos réponses pour booster le SEO local.
            3. **Le 'Fraîcheur' Score :** Un avis 5/5 d'il y a 6 mois a moins de poids qu'un 4/5 de la semaine dernière. Sollicitez vos clients dès la signature de l'acte authentique.
            """)

    # --- ONGLET 2 : VISIBILITÉ MAPS ---
    with tab2:
        st.header("Analyse de la Visibilité & Performance")
        
        # On empile les graphiques verticalement comme demandé
        if not df_st.empty:
            df_st['date'] = pd.to_datetime(df_st['date'], errors='coerce')
            
            # Graphique 1 : Vues
            st.subheader("1. Origine de votre Visibilité (Ordinateur vs Mobile)")
            vues_cols = [c for c in df_st.columns if 'vues' in c.lower()]
            fig_vues = px.line(df_st.sort_values('date'), x='date', y=vues_cols, title="Vues Google (Search & Maps)")
            st.plotly_chart(fig_vues, use_container_width=True)
            
            st.info("**Analyse :** Si le Mobile domine largement, vos photos de couverture et vos horaires doivent être parfaits (usage en déplacement).")

            # Graphique 2 : Actions
            st.subheader("2. Actions Clients (Attractivité)")
            act_cols = [c for c in df_st.columns if any(k in c.lower() for k in ['appels', 'site web', 'itinéraire'])]
            fig_act = px.bar(df_st.sort_values('date'), x='date', y=act_cols, barmode='group', title="Conversion : Appels, Itinéraires et Clics Web")
            st.plotly_chart(fig_act, use_container_width=True)

            with st.expander("💡 Comment booster votre Visibilité Maps ?"):
                st.write("""
                1. **Photos Hebdomadaires :** Les fiches avec + de 100 photos reçoivent 500% de demandes d'itinéraires en plus. Postez des photos de vos nouvelles exclusivités.
                2. **Attributs GBP :** Remplissez bien les attributs (Parking, Accessibilité, Rendez-vous en ligne).
                3. **Le bouton 'Site Web' :** Assurez-vous que le lien pointe vers la page spécifique de l'agence et non la home nationale de Human Immobilier pour un meilleur SEO local.
                4. **Google Posts :** Publiez vos actualités (nouveau conseiller, baisse de prix) une fois par semaine. C'est du contenu gratuit qui occupe de la place sur l'écran du client.
                """)
        else:
            st.warning("Chargez les fichiers de Performance pour voir les graphiques.")