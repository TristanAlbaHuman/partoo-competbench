# PARTOO · SEO Local Dashboard — Human Immobilier

Application Streamlit de suivi du benchmark SEO local PARTOO.

## 🚀 Lancement local

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 🌐 Déploiement Streamlit Cloud (gratuit)

1. **Crée un repo GitHub** et pousse ces fichiers :
   ```
   app.py
   data_processing.py
   requirements.txt
   sample_data.xlsx        ← ton export PARTOO de démo
   .streamlit/config.toml
   ```

2. **Va sur** [share.streamlit.io](https://share.streamlit.io)

3. **New app** → sélectionne ton repo → `app.py` → **Deploy**

4. ✅ URL publique partageable en 2 minutes

## 🔄 Mise à jour mensuelle

Tu peux :
- **Glisser le nouvel export** directement dans l'interface (file uploader dans la sidebar)
- Ou remplacer `sample_data.xlsx` dans le repo pour mettre à jour la démo

## 📊 Fonctionnalités

| Onglet | Contenu |
|--------|---------|
| **Vue d'ensemble** | KPIs, distribution positions, couverture mots-clés, top départements |
| **Benchmark** | Comparatif 11 réseaux, tableaux, scatter position × note |
| **Agences** | Score SEO, classées/non classées, recherche, exports CSV |
| **Plans d'action** | Priorisation 🔴🟡🟢, actions détaillées, export CSV |

## 🔍 Filtres disponibles

- Mots-clés
- Département
- Agence(s)
- Période (si multi-exports chargés)
