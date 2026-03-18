import pandas as pd
import re
import streamlit as st

DEPT_NAMES = {
    "01": "Ain", "02": "Aisne", "03": "Allier", "04": "Alpes-de-Haute-Provence",
    "05": "Hautes-Alpes", "06": "Alpes-Maritimes", "07": "Ardèche", "08": "Ardennes",
    "09": "Ariège", "10": "Aube", "11": "Aude", "12": "Aveyron",
    "13": "Bouches-du-Rhône", "14": "Calvados", "15": "Cantal", "16": "Charente",
    "17": "Charente-Maritime", "18": "Cher", "19": "Corrèze", "20": "Corse",
    "21": "Côte-d'Or", "22": "Côtes-d'Armor", "23": "Creuse", "24": "Dordogne",
    "25": "Doubs", "26": "Drôme", "27": "Eure", "28": "Eure-et-Loir",
    "29": "Finistère", "30": "Gard", "31": "Haute-Garonne", "32": "Gers",
    "33": "Gironde", "34": "Hérault", "35": "Ille-et-Vilaine", "36": "Indre",
    "37": "Indre-et-Loire", "38": "Isère", "39": "Jura", "40": "Landes",
    "41": "Loir-et-Cher", "42": "Loire", "43": "Haute-Loire", "44": "Loire-Atlantique",
    "45": "Loiret", "46": "Lot", "47": "Lot-et-Garonne", "48": "Lozère",
    "49": "Maine-et-Loire", "50": "Manche", "51": "Marne", "52": "Haute-Marne",
    "53": "Mayenne", "54": "Meurthe-et-Moselle", "55": "Meuse", "56": "Morbihan",
    "57": "Moselle", "58": "Nièvre", "59": "Nord", "60": "Oise", "61": "Orne",
    "62": "Pas-de-Calais", "63": "Puy-de-Dôme", "64": "Pyrénées-Atlantiques",
    "65": "Hautes-Pyrénées", "66": "Pyrénées-Orientales", "67": "Bas-Rhin",
    "68": "Haut-Rhin", "69": "Rhône", "70": "Haute-Saône", "71": "Saône-et-Loire",
    "72": "Sarthe", "73": "Savoie", "74": "Haute-Savoie", "75": "Paris",
    "76": "Seine-Maritime", "77": "Seine-et-Marne", "78": "Yvelines",
    "79": "Deux-Sèvres", "80": "Somme", "81": "Tarn", "82": "Tarn-et-Garonne",
    "83": "Var", "84": "Vaucluse", "85": "Vendée", "86": "Vienne",
    "87": "Haute-Vienne", "88": "Vosges", "89": "Yonne",
    "90": "Territoire de Belfort", "91": "Essonne", "92": "Hauts-de-Seine",
    "93": "Seine-Saint-Denis", "94": "Val-de-Marne", "95": "Val-d'Oise",
}


def extract_cp(addr):
    if pd.isna(addr):
        return None
    m = re.search(r"\b(\d{5})\b", str(addr))
    return m.group(1) if m else None


@st.cache_data(show_spinner="Chargement des données…")
def load_excel(file_bytes: bytes, periode: str) -> dict:
    import io
    xl = pd.ExcelFile(io.BytesIO(file_bytes))

    df_gen = pd.read_excel(xl, sheet_name="Statistiques générales")
    df_gen["periode"] = periode

    df_det = pd.read_excel(xl, sheet_name="Statistiques détaillées")
    df_det["cp"] = df_det["Adresse"].apply(extract_cp)
    df_det["dept"] = df_det["cp"].apply(lambda x: x[:2] if isinstance(x, str) else None)
    df_det["dept_label"] = df_det["dept"].map(DEPT_NAMES)

    df_human = df_det[df_det["Concurrents"].isna()].copy()

    ref = (
        df_human.groupby("Business Id")
        .agg(
            nom=("Nom de l'établissement", "first"),
            adresse=("Adresse", "first"),
            cp=("cp", "first"),
            dept=("dept", "first"),
            dept_label=("dept_label", "first"),
        )
        .reset_index()
    )

    df_cl = pd.read_excel(xl, sheet_name="Établissements classés")
    df_cl = df_cl.merge(ref[["Business Id", "cp", "dept", "dept_label"]], on="Business Id", how="left")
    df_cl["Notation"] = pd.to_numeric(df_cl["Notation"], errors="coerce")
    df_cl["periode"] = periode
    df_cl["statut"] = df_cl["Position"].apply(
        lambda x: "Top 3" if x <= 3 else ("Top 5" if x <= 5 else ("Top 10" if x <= 10 else "Hors Top 10"))
    )

    df_nc = pd.read_excel(xl, sheet_name="Établissements non classés")
    df_nc = df_nc.merge(ref[["Business Id", "cp", "dept", "dept_label"]], on="Business Id", how="left")
    df_nc["periode"] = periode

    return {
        "generales": df_gen,
        "classees": df_cl,
        "non_classees": df_nc,
        "ref": ref,
        "periode": periode,
        "mots_cles": sorted(df_cl["Mot-clé"].unique().tolist()),
        "depts": sorted(ref["dept"].dropna().unique().tolist()),
    }


def merge_datasets(datasets: list) -> dict:
    if len(datasets) == 1:
        return datasets[0]
    return {
        "generales": pd.concat([d["generales"] for d in datasets], ignore_index=True),
        "classees": pd.concat([d["classees"] for d in datasets], ignore_index=True),
        "non_classees": pd.concat([d["non_classees"] for d in datasets], ignore_index=True),
        "ref": datasets[-1]["ref"],
        "periode": " | ".join(d["periode"] for d in datasets),
        "mots_cles": datasets[-1]["mots_cles"],
        "depts": datasets[-1]["depts"],
    }


def apply_filters(data: dict, sel_mots, sel_depts, sel_agences) -> dict:
    cl = data["classees"].copy()
    nc = data["non_classees"].copy()

    cl = cl[cl["Mot-clé"].isin(sel_mots)]
    nc = nc[nc["Mot-clé"].isin(sel_mots)]

    if sel_depts:
        cl = cl[cl["dept"].isin(sel_depts)]
        nc = nc[nc["dept"].isin(sel_depts)]

    if sel_agences:
        cl = cl[cl["Nom de l'établissement"].isin(sel_agences)]
        nc = nc[nc["Nom de l'établissement"].isin(sel_agences)]

    return {"classees": cl, "non_classees": nc}


def seo_score(pos_moy, nb_couverts, total_mots, notation):
    pos_s = max(0, (20 - pos_moy) / 20 * 50) if pos_moy else 0
    cov_s = (nb_couverts / max(total_mots, 1)) * 30
    note_s = max(0, (notation - 3.5) / 1.5 * 20) if notation and not pd.isna(notation) else 0
    return int(min(100, pos_s + cov_s + note_s))


def get_priorite(pos_moy, nb_manquants, notation):
    score = 0
    if pos_moy is None:
        score += 3
    elif pos_moy > 10:
        score += 3
    elif pos_moy > 5:
        score += 2
    else:
        score += 1
    score += min(3, nb_manquants)
    if notation and not pd.isna(notation) and notation < 4.0:
        score += 1
    if score >= 5:
        return "🔴 Urgent"
    elif score >= 3:
        return "🟡 Important"
    return "🟢 Opportunité"
