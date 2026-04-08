import streamlit as st
import pandas as pd
import plotly.express as px
import io

st.set_page_config(page_title="Human Hub - Partoo Analytics", layout="wide")

# --- FONCTIONS DE TRAITEMENT ---

def process_universal(uploaded_file):
    """Détecte si c'est un fichier Avis ou Stats et le nettoie."""
    # Aperçu pour détection
    preview = pd.read_excel(uploaded_file, header=None, nrows=5)
    header_line = str(preview.iloc[2].values).lower()

    # CAS A : STATISTIQUES (KPIs 2024-2025)
    if any(k in header_line for k in ["recherche", "action", "vues"]):
        df_raw = pd.read_excel(uploaded_file, header=None)
        # On fusionne la ligne 2 et 3 pour les entêtes doubles
        h1 = df_raw.iloc[1].ffill().fillna('') 
        h2 = df_raw.iloc[2].fillna('')
        df_raw.columns = [f"{str(a)} - {str(b)}".strip(" -") for a, b in zip(h1, h2)]
        
        df = df_raw.iloc[3:].copy()
        df['Source_Type'] = "Stats"

    # CAS B : AVIS (Réputation 2021-2025)
    else:
        df = pd.read_excel(uploaded_file, skiprows=2)
        df.columns = [str(c).strip() for c in df.columns]
        df['Source_Type'] = "Avis"
        
        # Harmonisation des colonnes pour la fusion multi-années
        mapping = {
            'Date_Std': ['date', 'période', 'mois'],
            'Agence_Std': ['établissement', 'agence', 'nom'],
            'Note_Std': ['note', 'étoile', 'rating'],
            'Groupe_Std': ['groupe', 'entreprise', 'tag']
        }
        for final, keywords in mapping.items():
            for col in df.columns:
                if any(k in col.lower() for k in keywords):
                    df = df.rename(columns={col: final})
                    break
    
    # Standardisation de la date pour le tri chronologique
    date_col = next((c for c in df.columns if 'date' in c.lower() or 'mois' in c.lower() or 'période' in c.lower()), None)
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=[date_col]).sort_values(date_col)
    
    return df

# --- INTERFACE ---

st.title("🛡️ Human Immobilier : Hub Consolide Partoo")
st.markdown("Uploadez tous vos fichiers (Avis 2021-25 & Stats 2024-25) en vrac.")

files = st.sidebar.file_uploader("Glissez vos fichiers Excel ici", accept_multiple_files=True)

if files:
    all_data = [process_universal(f) for f in files]
    
    # 1. Séparation et Fusion
    df_stats = pd.concat([d for d in all_data if d['Source_Type'].iloc[0] == "Stats"], ignore_index=True) if any(d['Source_Type'].iloc[0] == "Stats" for d in all_data) else pd.DataFrame()
    df_avis = pd.concat([d for d in all_data if d['Source_Type'].iloc[0] == "Avis"], ignore_index=True) if any(d['Source_Type'].iloc[0] == "Avis" for d in all_data) else pd.DataFrame()

    tab1, tab2 = st.tabs(["📈 Performance (Stats 24-25)", "⭐ Réputation (Avis 21-25)"])

    with tab1:
        if not df_stats.empty:
            st.subheader("Analyse des flux et actions")
            # Nettoyage des colonnes numériques
            cols_kpi = [c for c in df_stats.columns if " - " in c]
            for c in cols_kpi:
                df_stats[c] = pd.to_numeric(df_stats[c], errors='coerce')
            
            sel_kpi = st.selectbox("Choisir un indicateur de performance", cols_kpi)
            fig_stats = px.line(df_stats, x=df_stats.columns[0], y=sel_kpi, color='Nom de l\'établissement', title=f"Tendance : {sel_kpi}")
            st.plotly_chart(fig_stats, use_container_width=True)
        else:
            st.info("En attente de fichiers de statistiques (2024-2025).")

    with tab2:
        if not df_avis.empty:
            st.subheader("Analyse de la satisfaction client")
            # Calcul des KPIs Avis
            df_avis['Note_Std'] = pd.to_numeric(df_avis['Note_Std'], errors='coerce')
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Note Moyenne (2021-2025)", f"{df_avis['Note_Std'].mean():.2f} ⭐")
            c2.metric("Total Avis", f"{len(df_avis)}")
            c3.metric("Établissements", df_avis['Agence_Std'].nunique())

            # Graphique Temporel
            df_avis_mensuel = df_avis.set_index('Date_Std').resample('M')['Note_Std'].mean().reset_index()
            fig_avis = px.area(df_avis_mensuel, x='Date_Std', y='Note_Std', title="Évolution de la note moyenne", range_y=[0,5])
            st.plotly_chart(fig_avis, use_container_width=True)
            
            with st.expander("Voir le détail des avis"):
                st.dataframe(df_avis[['Date_Std', 'Agence_Std', 'Note_Std']].sort_values('Date_Std', ascending=False))
        else:
            st.info("En attente de fichiers d'avis (2021-2025).")
else:
    st.warning("Veuillez charger vos fichiers dans la barre latérale pour commencer.")