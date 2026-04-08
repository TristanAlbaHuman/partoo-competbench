import streamlit as st
import pandas as pd
import plotly.express as px

# --- FONCTION DE NETTOYAGE DES DOUBLONS ---
def make_columns_unique(columns):
    """Ajoute un suffixe aux noms de colonnes en double (ex: Note, Note.1)."""
    seen = {}
    new_cols = []
    for item in columns:
        if item in seen:
            seen[item] += 1
            new_cols.append(f"{item}.{seen[item]}")
        else:
            seen[item] = 0
            new_cols.append(item)
    return new_cols

def process_universal(uploaded_file):
    preview = pd.read_excel(uploaded_file, header=None, nrows=5)
    header_line = str(preview.iloc[2].values).lower()

    # CAS A : STATISTIQUES
    if any(k in header_line for k in ["recherche", "action", "vues"]):
        df_raw = pd.read_excel(uploaded_file, header=None)
        h1 = df_raw.iloc[1].ffill().fillna('') 
        h2 = df_raw.iloc[2].fillna('')
        
        # Fusion des noms
        raw_cols = [f"{str(a)} - {str(b)}".strip(" -") for a, b in zip(h1, h2)]
        # CRUCIAL : Rendre les colonnes uniques pour éviter DuplicateError
        df_raw.columns = make_columns_unique(raw_cols)
        
        df = df_raw.iloc[3:].copy()
        df['Source_Type'] = "Stats"

    # CAS B : AVIS
    else:
        df = pd.read_excel(uploaded_file, skiprows=2)
        df.columns = make_columns_unique([str(c).strip() for c in df.columns])
        df['Source_Type'] = "Avis"
        
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
    
    # Standardisation Date
    date_col = next((c for c in df.columns if 'date' in c.lower() or 'mois' in c.lower() or 'période' in c.lower()), df.columns[0])
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df = df.dropna(subset=[date_col])
    
    return df

# --- DANS LA SECTION GRAPHIQUE ---
# (Modifiez la ligne px.line comme suit pour gérer les noms d'établissements)

if not df_stats.empty:
    st.subheader("📈 Performance")
    cols_kpi = [c for c in df_stats.columns if " - " in c]
    sel_kpi = st.selectbox("Indicateur", cols_kpi)
    
    # On identifie dynamiquement la colonne qui contient le nom de l'agence/magasin
    # Dans vos logs, on voit "Code magasin" ou "Nom de l'établissement"
    nom_etablissement_col = next((c for c in df_stats.columns if "établissement" in c.lower() or "magasin" in c.lower() or "agence" in c.lower()), None)

    try:
        fig_stats = px.line(
            df_stats.sort_values(df_stats.columns[0]), 
            x=df_stats.columns[0], 
            y=sel_kpi, 
            color=nom_etablissement_col, # Utilise la colonne trouvée dynamiquement
            title=f"Tendance : {sel_kpi}"
        )
        st.plotly_chart(fig_stats, use_container_width=True)
    except Exception as e:
        st.error(f"Erreur d'affichage du graphique : {e}")