import pandas as pd
import re
import streamlit as st
import math
import time
import os

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

DEPT_CENTROIDS = {
    "01":(46.2,5.2),"02":(49.5,3.6),"03":(46.3,3.1),"04":(44.1,6.2),
    "05":(44.7,6.4),"06":(43.9,7.2),"07":(44.8,4.5),"08":(49.7,4.7),
    "09":(42.9,1.6),"10":(48.3,4.1),"11":(43.1,2.4),"12":(44.3,2.6),
    "13":(43.5,5.4),"14":(49.1,-0.4),"15":(45.0,2.6),"16":(45.7,0.2),
    "17":(45.7,-0.9),"18":(47.1,2.4),"19":(45.4,1.9),"20":(42.0,9.0),
    "21":(47.3,4.8),"22":(48.4,-2.8),"23":(46.0,2.0),"24":(45.1,0.7),
    "25":(47.2,6.4),"26":(44.8,5.0),"27":(49.1,1.2),"28":(48.4,1.4),
    "29":(48.2,-4.0),"30":(44.0,4.2),"31":(43.6,1.4),"32":(43.6,0.6),
    "33":(44.8,-0.6),"34":(43.6,3.5),"35":(48.1,-1.7),"36":(46.8,1.6),
    "37":(47.2,0.7),"38":(45.2,5.7),"39":(46.7,5.5),"40":(43.9,-0.8),
    "41":(47.6,1.3),"42":(45.5,4.2),"43":(45.1,3.9),"44":(47.3,-1.6),
    "45":(47.9,2.1),"46":(44.6,1.7),"47":(44.4,0.6),"48":(44.5,3.5),
    "49":(47.4,-0.6),"50":(49.1,-1.3),"51":(49.0,4.0),"52":(48.0,5.4),
    "53":(48.1,-0.7),"54":(48.7,6.2),"55":(49.0,5.3),"56":(47.8,-2.9),
    "57":(49.0,6.6),"58":(47.1,3.5),"59":(50.5,3.2),"60":(49.4,2.5),
    "61":(48.6,0.1),"62":(50.5,2.6),"63":(45.8,3.1),"64":(43.3,-0.8),
    "65":(43.2,0.1),"66":(42.6,2.8),"67":(48.6,7.7),"68":(47.8,7.3),
    "69":(45.8,4.8),"70":(47.6,6.1),"71":(46.6,4.5),"72":(48.0,0.2),
    "73":(45.5,6.4),"74":(46.0,6.4),"75":(48.9,2.3),"76":(49.7,1.1),
    "77":(48.6,3.0),"78":(48.8,1.8),"79":(46.5,-0.4),"80":(49.9,2.3),
    "81":(43.9,2.1),"82":(44.0,1.3),"83":(43.5,6.2),"84":(44.0,5.1),
    "85":(46.7,-1.4),"86":(46.6,0.3),"87":(45.8,1.3),"88":(48.2,6.4),
    "89":(47.8,3.6),"90":(47.6,6.9),"91":(48.6,2.3),"92":(48.9,2.2),
    "93":(48.9,2.5),"94":(48.8,2.5),"95":(49.1,2.1),
}


def extract_cp(addr):
    if pd.isna(addr):
        return None
    m = re.search(r"\b(\d{5})\b", str(addr))
    return m.group(1) if m else None


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))


def fallback_coords(cp, dept, nom):
    """Fallback: department centroid only (no jitter, labeled as approximate)."""
    import hashlib
    if dept and dept in DEPT_CENTROIDS:
        base_lat, base_lon = DEPT_CENTROIDS[dept]
        h = int(hashlib.md5(f"{cp}{nom}".encode()).hexdigest()[:8], 16)
        lat_j = ((h % 1000) - 500) / 1000 * 0.15
        lon_j = ((h // 1000 % 1000) - 500) / 1000 * 0.15
        return round(base_lat + lat_j, 5), round(base_lon + lon_j, 5), True  # True = approximate
    return None, None, True


@st.cache_data(show_spinner=False)
def geocode_nominatim_batch(addresses: tuple) -> dict:
    """
    Geocode a batch of addresses via Nominatim.
    Called only on Streamlit Cloud (has internet access).
    Returns dict {address: (lat, lon)}.
    """
    import requests
    HEADERS = {"User-Agent": "PartooSEODashboard/2.0"}
    results = {}
    for addr in addresses:
        try:
            r = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": addr, "format": "json", "limit": 1, "countrycodes": "fr"},
                headers=HEADERS, timeout=6,
            )
            data = r.json()
            if data:
                results[addr] = (float(data[0]["lat"]), float(data[0]["lon"]))
            else:
                results[addr] = (None, None)
        except:
            results[addr] = (None, None)
        time.sleep(1.05)
    return results


def load_coords_csv(coords_path="coords.csv") -> dict:
    """Load pre-geocoded coords from CSV. Returns {address: (lat, lon)}."""
    if not os.path.exists(coords_path):
        return {}
    try:
        df = pd.read_csv(coords_path, encoding="utf-8")
        result = {}
        for _, row in df.iterrows():
            if pd.notna(row.get("lat")) and pd.notna(row.get("lon")):
                result[str(row["adresse"])] = (float(row["lat"]), float(row["lon"]))
        return result
    except Exception as e:
        return {}


@st.cache_data(show_spinner="Chargement des données…")
def load_excel(file_bytes: bytes, periode: str, coords_csv_bytes: bytes = b"") -> dict:
    import io, tempfile

    xl = pd.ExcelFile(io.BytesIO(file_bytes))

    df_gen = pd.read_excel(xl, sheet_name="Statistiques générales")
    df_gen["periode"] = periode

    df_det = pd.read_excel(xl, sheet_name="Statistiques détaillées")
    df_det["cp"] = df_det["Adresse"].apply(extract_cp)
    df_det["dept"] = df_det["cp"].apply(lambda x: x[:2] if isinstance(x, str) else None)
    df_det["Notation"] = pd.to_numeric(df_det["Notation"], errors="coerce")

    # Load coords lookup
    coords_lookup = {}
    if coords_csv_bytes:
        try:
            df_coords = pd.read_csv(io.BytesIO(coords_csv_bytes), encoding="utf-8")
            for _, row in df_coords.iterrows():
                if pd.notna(row.get("lat")) and pd.notna(row.get("lon")):
                    coords_lookup[str(row["adresse"]).strip()] = (float(row["lat"]), float(row["lon"]))
        except:
            pass
    else:
        coords_lookup = load_coords_csv()

    def get_coords(addr, cp, dept, nom):
        key = str(addr).strip() if addr else ""
        if key in coords_lookup:
            return coords_lookup[key][0], coords_lookup[key][1], False  # False = precise
        return fallback_coords(cp, dept, nom)

    # Human reference
    df_human = df_det[df_det["Concurrents"].isna()].copy()
    ref = (
        df_human.groupby("Business Id")
        .agg(nom=("Nom de l'établissement", "first"), adresse=("Adresse", "first"),
             cp=("cp", "first"), dept=("dept", "first"))
        .reset_index()
    )
    ref["dept_label"] = ref["dept"].map(DEPT_NAMES)

    ref["lat"] = None
    ref["lon"] = None
    ref["approx"] = True
    for idx, row in ref.iterrows():
        lat, lon, approx = get_coords(row["adresse"], row["cp"], row["dept"], row["nom"])
        ref.at[idx, "lat"] = lat
        ref.at[idx, "lon"] = lon
        ref.at[idx, "approx"] = approx

    precise_pct = int((~ref["approx"]).sum() / max(len(ref), 1) * 100)

    # Classées
    df_cl = pd.read_excel(xl, sheet_name="Établissements classés")
    df_cl = df_cl.merge(ref[["Business Id", "cp", "dept", "dept_label", "lat", "lon", "approx"]], on="Business Id", how="left")
    df_cl["Notation"] = pd.to_numeric(df_cl["Notation"], errors="coerce")
    df_cl["periode"] = periode
    df_cl["statut"] = df_cl["Position"].apply(
        lambda x: "Top 3" if x <= 3 else ("Top 5" if x <= 5 else ("Top 10" if x <= 10 else "Hors Top 10"))
    )

    # Non classées
    df_nc = pd.read_excel(xl, sheet_name="Établissements non classés")
    df_nc = df_nc.merge(ref[["Business Id", "cp", "dept", "dept_label", "lat", "lon", "approx"]], on="Business Id", how="left")
    df_nc["periode"] = periode

    # Competitors
    df_conc = df_det[df_det["Concurrents"].notna()].copy()
    conc_agg = (
        df_conc.groupby(["Nom de l'établissement", "Concurrents", "Adresse"])
        .agg(cp=("cp", "first"), dept=("dept", "first"),
             pos_moy=("Position", "mean"), pos_min=("Position", "min"),
             notation=("Notation", "mean"), reviews=("reviews", "mean"),
             mots=("Mot-clé", lambda x: list(x.unique())))
        .reset_index()
    )
    conc_agg["lat"] = None
    conc_agg["lon"] = None
    conc_agg["approx"] = True
    for idx, row in conc_agg.iterrows():
        lat, lon, approx = get_coords(row["Adresse"], row["cp"], row["dept"], row["Nom de l'établissement"])
        conc_agg.at[idx, "lat"] = lat
        conc_agg.at[idx, "lon"] = lon
        conc_agg.at[idx, "approx"] = approx
    conc_agg.rename(columns={"Nom de l'établissement": "nom", "Concurrents": "reseau", "Adresse": "adresse"}, inplace=True)

    return {
        "generales": df_gen,
        "classees": df_cl,
        "non_classees": df_nc,
        "ref": ref,
        "concurrents_geo": conc_agg,
        "_df_det": df_det,
        "periode": periode,
        "mots_cles": sorted(df_cl["Mot-clé"].unique().tolist()),
        "depts": sorted(ref["dept"].dropna().unique().tolist()),
        "human_names": sorted(ref["nom"].unique().tolist()),
        "precise_pct": precise_pct,
        "coords_loaded": bool(coords_lookup),
    }


def merge_datasets(datasets: list) -> dict:
    if len(datasets) == 1:
        return datasets[0]
    return {
        "generales": pd.concat([d["generales"] for d in datasets], ignore_index=True),
        "classees": pd.concat([d["classees"] for d in datasets], ignore_index=True),
        "non_classees": pd.concat([d["non_classees"] for d in datasets], ignore_index=True),
        "ref": datasets[-1]["ref"],
        "concurrents_geo": datasets[-1]["concurrents_geo"],
        "periode": " | ".join(d["periode"] for d in datasets),
        "mots_cles": datasets[-1]["mots_cles"],
        "depts": datasets[-1]["depts"],
        "human_names": datasets[-1]["human_names"],
        "precise_pct": datasets[-1].get("precise_pct", 0),
        "coords_loaded": datasets[-1].get("coords_loaded", False),
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


def get_competitors_in_radius(agency_lat, agency_lon, conc_df, radius_km=5):
    if agency_lat is None or agency_lon is None:
        return pd.DataFrame()
    result = []
    for _, row in conc_df.iterrows():
        if row["lat"] is None or row["lon"] is None:
            continue
        try:
            dist = haversine_km(float(agency_lat), float(agency_lon), float(row["lat"]), float(row["lon"]))
            if dist <= radius_km:
                result.append({**row.to_dict(), "distance_km": round(dist, 2)})
        except:
            continue
    if not result:
        return pd.DataFrame()
    return pd.DataFrame(result).sort_values("pos_moy")
