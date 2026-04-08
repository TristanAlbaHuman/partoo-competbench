import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuration de la page
st.set_page_config(page_title="Human BI Dashboard", layout="wide")

# --- FONCTIONS TECHNIQUES ---

def make_columns_unique(columns):
    """Évite les erreurs de doublons dans les noms de colonnes."""
    seen = {}
    new_cols = []
    for item in columns:
        item_str = str(item).strip()
        if item_str in seen:
            seen[item_str] += 1
            new_cols.append(f"{item_str}_{seen[item_str]}")
        else:
            seen[item_str] = 0
            new_cols.append(item_str)
    return new_cols

def load_and_process_files(uploaded_files):
    all_avis = []
    all_stats = []

    for f in uploaded_files:
        # Lecture initiale pour détection (ligne 2/3 contient les titres)
        df_detect = pd.read_excel(f, header=None, nrows=5)
        
        # On vérifie le contenu de la ligne 2 (index 1) ou 3 (index 2)
        row_content = str(df_detect.iloc[1:3].values).lower()

        # --- CAS 1 : STATISTIQUES (KPIs de performance) ---
        if any(k in row_content for k in ["vues", "recherche", "appels", "itinéraire"]):
            df = pd.read_excel(f, header=None)
            # Fusion des lignes 1 et 2 pour créer des entêtes propres
            h1 = df.iloc[0].ffill().fillna('')
            h2 = df.iloc[1].fillna('')
            df.columns = make_columns_unique([f"{str(a)} {str(b)}".strip() for a, b in zip(h1, h2)])
            df = df.iloc[2:].copy()
            
            # Conversion date
            date_col = df.columns[0]
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            
            # Conversion numérique des colonnes KPI
            for col in df.columns:
                if any(k in col.lower() for k in ["vues", "appels", "visites", "demandes", "recherches"]):
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            df['Source_Type'] = 'Stats'
            all_stats.append(df)

        # --- CAS 2 : AVIS (E-Réputation) ---
        else:
            # Les avis ont souvent les titres en ligne 2 (skiprows=1)
            df = pd.read_excel(f, skiprows=1)
            df.columns = make_columns_unique([str(c).strip() for c in df.columns])
            
            # Mapping pour uniformiser
            mapping = {
                'Date_Std': ['date de création', 'date'],
                'Agence_Std': ['nom de l\'établissement', 'agence'],
                'Note_Std': ['rating', 'note', 'étoile'],
                'Groupe_Std': ['groupes', 'section']
            }
            for final, keys in mapping.items():
                for c in df.columns:
                    if any(k in c.lower() for k in keys) and final not in df.columns:
                        df = df.rename(columns={c: final})
            
            if 'Date_Std' in df.columns:
                df['Date_Std'] = pd.to_datetime(df['Date_Std'], errors='coerce')
            if 'Note_Std' in df.columns:
                df['Note_Std'] = pd.to_numeric(df['Note_Std'], errors='coerce')
                
            df['Source_Type'] = 'Avis'
            all_avis.append(df)

    final_avis = pd.concat(all_avis, ignore_index=True) if all_avis else pd.DataFrame()
    final_stats = pd.concat(all_stats, ignore_index=True) if all_stats else pd.DataFrame()
    
    return final_avis, final_stats

# --- INTERFACE ---

st.title("📈 Dashboard BI - Human Immobilier")
st.markdown("Analyse croisée de la **Visibilité** (Performance) et de la **Satisfaction** (Avis).")

files = st.sidebar.file_uploader("📂 Déposez tous vos fichiers Excel (Avis & Stats)", accept_multiple_files=True)

if files:
    with st.spinner('Analyse des fichiers en cours...'):
        df_a, df_s = load_and_process_files(files)

    # --- FILTRES ---
    st.sidebar.header("🔍 Filtres")
    
    # Filtre Agence (commun aux deux types si possible)
    liste_agences = []
    if not df_a.empty: liste_agences += df_a['Agence_Std'].unique().tolist()
    # On cherche une colonne agence dans les stats
    col_etab_stats = ""
    if not df_s.empty:
        col_etab_stats = next((c for c in df_s.columns if "établissement" in c.lower() or "magasin" in c.lower()), "")
        if col_etab_stats: liste_agences += df_s[col_etab_stats].unique().tolist()
    
    liste_agences = sorted(list(set([str(a) for a in liste_agences if str(a) != 'nan'])))
    sel_agences = st.sidebar.multiselect("Sélectionner les agences", liste_agences, default=liste_agences[:2] if liste_agences else [])

    # Filtrage des données
    df_a_f = df_a[df_a['Agence_Std'].isin(sel_agences)] if not df_a.empty else df_a
    df_s_f = df_s[df_s[col_etab_stats].isin(sel_agences)] if not df_s.empty and col_etab_stats else df_s

    # --- AFFICHAGE KPIs FLASH ---
    c1, c2, c3, c4 = st.columns(4)
    if not df_a_f.empty:
        c1.metric("Note Moyenne", f"{df_a_f['Note_Std'].mean():.2f} ⭐")
        c2.metric("Total Avis", f"{len(df_a_f):,}")
    
    if not df_s_f.empty:
        vues_cols = [c for c in df_s_f.columns if "vues" in c.lower()]
        actions_cols = [c for c in df_s_f.columns if any(k in c.lower() for k in ["appels", "visites", "demandes"])]
        c3.metric("Visibilité (Vues)", f"{int(df_s_f[vues_cols].sum().sum()):,}")
        c4.metric("Attractivité (Actions)", f"{int(df_s_f[actions_cols].sum().sum()):,}")

    # --- ONGLETS ---
    tab1, tab2 = st.tabs(["⭐ Réputation & Satisfaction", "🚀 Performance & Flux"])

    with tab1:
        if not df_a_f.empty:
            col_l, col_r = st.columns([2, 1])
            with col_l:
                st.subheader("Tendance de la note mensuelle")
                df_evol = df_a_f.set_index('Date_Std').resample('M')['Note_Std'].mean().reset_index()
                fig_note = px.line(df_evol, x='Date_Std', y='Note_Std', markers=True, range_y=[0, 5], template="plotly_white")
                st.plotly_chart(fig_note, use_container_width=True)
            
            with col_r:
                st.subheader("Répartition des Étoiles")
                fig_pie = px.pie(df_a_f, names='Note_Std', hole=0.4, color='Note_Std')
                st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Aucune donnée d'avis à afficher.")

    with tab2:
        if not df_s_f.empty:
            col_l, col_r = st.columns(2)
            
            with col_l:
                st.subheader("Tunnel : Vues vs Actions")
                # Agrégation par mois
                date_col = df_s_f.columns[0]
                df_s_f['Mois'] = df_s_f[date_col].dt.to_period('M').dt.to_timestamp()
                df_tunnel = df_s_f.groupby('Mois').agg({vues_cols[0]: 'sum', actions_cols[0]: 'sum'}).reset_index()
                
                fig_tunnel = go.Figure()
                fig_tunnel.add_trace(go.Bar(x=df_tunnel['Mois'], y=df_tunnel[vues_cols[0]], name="Vues Google"))
                fig_tunnel.add_trace(go.Scatter(x=df_tunnel['Mois'], y=df_tunnel[actions_cols[0]], name="Actions", yaxis="y2", line=dict(color='orange', width=3)))
                fig_tunnel.update_layout(yaxis2=dict(overlaying='y', side='right'), title="Vues (Barres) vs Actions (Ligne)")
                st.plotly_chart(fig_tunnel, use_container_width=True)

            with col_r:
                st.subheader("Top Actions Clients")
                action_sums = df_s_f[actions_cols].sum().reset_index()
                action_sums.columns = ['Type d\'action', 'Volume']
                fig_act = px.bar(action_sums, x='Volume', y='Type d\'action', orientation='h', color='Type d\'action')
                st.plotly_chart(fig_act, use_container_width=True)
        else:
            st.info("Aucune donnée de performance à afficher.")

else:
    st.info("👋 Bonjour ! Pour générer votre dashboard, déposez vos fichiers **Avis** et **Monthly Performance** dans le menu de gauche.")