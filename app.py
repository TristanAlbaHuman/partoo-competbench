import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import io

from data_processing import (
    load_excel, merge_datasets, apply_filters,
    seo_score, get_priorite, DEPT_NAMES,
    get_competitors_in_radius, haversine_km
)

st.set_page_config(
    page_title="PARTOO · SEO Local – Human Immobilier",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=DM+Sans:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
section[data-testid="stSidebar"] { background: #04090f !important; border-right: 1px solid #0d2035; }
section[data-testid="stSidebar"] * { color: #8bafc8 !important; }
section[data-testid="stSidebar"] .stMultiSelect label,
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stFileUploader label {
    font-family: 'DM Mono', monospace !important; font-size: 10px !important;
    letter-spacing: 0.12em !important; text-transform: uppercase !important; color: #2a5a7a !important;
}
.main .block-container { padding: 1.5rem 2rem 2rem 2rem; max-width: 100%; }
div[data-testid="metric-container"] {
    background: #04090f; border: 1px solid #0d2035; border-radius: 8px; padding: 14px 18px !important;
}
div[data-testid="metric-container"] label {
    font-family: 'DM Mono', monospace !important; font-size: 10px !important;
    letter-spacing: 0.14em !important; text-transform: uppercase !important; color: #2a5a7a !important;
}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-size: 1.9rem !important; font-weight: 700 !important; color: #00d4ff !important;
}
button[data-baseweb="tab"] {
    font-family: 'DM Mono', monospace !important; font-size: 11px !important;
    letter-spacing: 0.1em !important; text-transform: uppercase !important; color: #2a5a7a !important;
}
button[data-baseweb="tab"][aria-selected="true"] { color: #00d4ff !important; }
.section-hdr {
    font-family: 'DM Mono', monospace; font-size: 10px; letter-spacing: 0.16em;
    text-transform: uppercase; color: #2a5a7a; border-bottom: 1px solid #0d2035;
    padding-bottom: 6px; margin: 20px 0 12px 0;
}
</style>
""", unsafe_allow_html=True)

COLORS = {
    "human": "#00d4ff", "top3": "#4ade80", "top5": "#60a5fa",
    "top10": "#fbbf24", "hors": "#f97316", "nonclasse": "#f87171",
    "grid": "#0d2035", "text": "#8bafc8",
}
STATUT_COLORS = {
    "Top 3": "#4ade80", "Top 5": "#60a5fa", "Top 10": "#fbbf24",
    "Hors Top 10": "#f97316", "Non classé": "#f87171",
}
PRIO_COLORS = {"🔴 Urgent": "#f87171", "🟡 Important": "#fbbf24", "🟢 Opportunité": "#4ade80"}

def plotly_layout(fig, height=320, legend=False):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text"], family="DM Mono, monospace", size=10),
        height=height, margin=dict(t=30, b=20, l=10, r=10),
        showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=-0.4, font_size=10) if legend else {},
        xaxis=dict(gridcolor=COLORS["grid"], zeroline=False),
        yaxis=dict(gridcolor=COLORS["grid"], zeroline=False),
    )
    return fig

# ── SIDEBAR
with st.sidebar:
    st.markdown("""
    <div style='padding:4px 0 16px 0;'>
      <div style='font-family:DM Mono,monospace;font-size:10px;letter-spacing:.16em;color:#00d4ff;margin-bottom:4px;'>PARTOO</div>
      <div style='font-size:15px;font-weight:700;color:#e8edf2;'>Human Immobilier</div>
      <div style='font-family:DM Mono,monospace;font-size:10px;color:#1e3a57;margin-top:2px;'>SEO LOCAL BENCHMARK</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    st.markdown("**📂 Imports PARTOO**")
    uploaded = st.file_uploader("Charger export(s) .xlsx", type=["xlsx"], accept_multiple_files=True)

    DEFAULT = "sample_data.xlsx"
    datasets = []
    if uploaded:
        for f in uploaded:
            periode = f.name.replace(".xlsx", "").replace("_", " ")
            datasets.append(load_excel(f.read(), periode))
    else:
        try:
            with open(DEFAULT, "rb") as f:
                datasets.append(load_excel(f.read(), "Mars 2026"))
            st.caption("📌 Démo : export Mars 2026")
        except FileNotFoundError:
            st.warning("Chargez un export PARTOO pour commencer.")
            st.stop()

    data = merge_datasets(datasets)
    st.divider()

    st.markdown("**🔍 Filtres**")
    all_periodes = data["generales"]["periode"].unique().tolist()
    sel_periodes = st.multiselect("Période(s)", all_periodes, default=all_periodes) if len(all_periodes) > 1 else all_periodes

    sel_mots = st.multiselect("Mots-clés", data["mots_cles"], default=data["mots_cles"])

    dept_opts = data["depts"]
    dept_fmt = {d: f"{d} – {DEPT_NAMES.get(d,'')}" for d in dept_opts}
    sel_depts = st.multiselect("Département(s)", dept_opts, default=[], format_func=lambda x: dept_fmt.get(x, x))

    # FIXED: only Human agency names
    sel_agences = st.multiselect("Agence(s)", data["human_names"], default=[])

    st.divider()
    st.caption(f"v2.0 · {data['periode']}")

if not sel_mots:
    st.warning("Sélectionne au moins un mot-clé.")
    st.stop()

f = apply_filters(data, sel_mots, sel_depts, sel_agences)
cl = f["classees"]
nc = f["non_classees"]
total_mots = len(sel_mots)
conc_geo = data["concurrents_geo"]

st.markdown(f"""
<div style='margin-bottom:8px;'>
  <h2 style='margin:0;font-size:1.3rem;color:#e8edf2;font-weight:700;'>Competitive Benchmark – Human Immobilier</h2>
  <p style='margin:2px 0 0 0;font-family:DM Mono,monospace;font-size:10px;color:#2a5a7a;'>
    PARTOO · {data['periode']} · {', '.join(sel_mots)}
  </p>
</div>
""", unsafe_allow_html=True)

tab_ov, tab_bench, tab_ag, tab_map, tab_plan = st.tabs([
    "◈  Vue d'ensemble", "⊕  Benchmark", "◎  Agences", "🗺  Carte", "◆  Plans d'action",
])

# ══════════════════════════════════════════════
# TAB 1 – VUE D'ENSEMBLE
# ══════════════════════════════════════════════
with tab_ov:
    nb_total = data["ref"]["Business Id"].nunique()
    nb_cl = cl["Business Id"].nunique()
    nb_nc = nc["Business Id"].nunique()
    nb_top3 = cl[cl["statut"] == "Top 3"]["Business Id"].nunique()
    pos_moy = cl["Position"].mean() if len(cl) else 0
    notes = pd.to_numeric(cl["Notation"], errors="coerce").dropna()
    note_moy = notes.mean() if len(notes) else 0

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Réseau total", nb_total)
    c2.metric("Classées", nb_cl, delta=f"{nb_cl/max(nb_total,1)*100:.0f}% du réseau")
    c3.metric("Non classées", nb_nc, delta=f"-{nb_nc}", delta_color="inverse")
    c4.metric("Top 3 🥇", nb_top3, delta=f"{nb_top3/max(nb_cl,1)*100:.0f}% des classées")
    c5.metric("Position moyenne", f"{pos_moy:.1f}" if pos_moy else "–")
    c6.metric("Note moyenne", f"{note_moy:.2f} ⭐" if note_moy else "–")

    st.markdown("")
    col_a, col_b, col_c = st.columns([2, 2, 3])

    with col_a:
        st.markdown('<div class="section-hdr">Distribution des statuts</div>', unsafe_allow_html=True)
        statut_data = []
        for s, rng in [("Top 3",(1,3)),("Top 5",(4,5)),("Top 10",(6,10)),("Hors Top 10",(11,20))]:
            n = cl[cl["Position"].between(rng[0], rng[1])]["Business Id"].nunique()
            statut_data.append({"Statut": s, "Agences": n})
        statut_data.append({"Statut": "Non classé", "Agences": nb_nc})
        fig = px.bar(pd.DataFrame(statut_data), x="Statut", y="Agences",
                     color="Statut", color_discrete_map=STATUT_COLORS, text="Agences")
        fig.update_traces(textposition="outside")
        plotly_layout(fig, 300)
        fig.update_layout(xaxis_title=None, yaxis_title=None, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.markdown('<div class="section-hdr">Couverture par mot-clé</div>', unsafe_allow_html=True)
        mk_rows = []
        for mk in sel_mots:
            n_cl = cl[cl["Mot-clé"] == mk]["Business Id"].nunique()
            n_nc = nc[nc["Mot-clé"] == mk]["Business Id"].nunique()
            p = cl[cl["Mot-clé"] == mk]["Position"].mean()
            mk_rows.append({"Mot-clé": mk, "Classées": n_cl, "Non classées": n_nc})
        fig2 = px.bar(pd.DataFrame(mk_rows).melt(id_vars="Mot-clé", value_vars=["Classées","Non classées"]),
                      x="Mot-clé", y="value", color="variable",
                      color_discrete_map={"Classées": COLORS["human"], "Non classées": COLORS["nonclasse"]},
                      text="value", barmode="group")
        fig2.update_traces(textposition="outside")
        plotly_layout(fig2, 300, legend=True)
        fig2.update_layout(xaxis_title=None, yaxis_title=None)
        st.plotly_chart(fig2, use_container_width=True)

    with col_c:
        st.markdown('<div class="section-hdr">Top 15 départements</div>', unsafe_allow_html=True)
        dept_grp = (cl.groupby(["dept","dept_label"])
            .agg(n=("Business Id","nunique"), pos=("Position","mean"))
            .reset_index().sort_values("n", ascending=False).head(15))
        dept_grp["label"] = dept_grp["dept"] + " – " + dept_grp["dept_label"].fillna("")
        fig3 = px.bar(dept_grp, x="n", y="label", orientation="h",
                      color="pos", color_continuous_scale=["#4ade80","#fbbf24","#f87171"], text="n")
        fig3.update_traces(textposition="outside")
        plotly_layout(fig3, 380)
        fig3.update_layout(yaxis=dict(autorange="reversed", gridcolor=COLORS["grid"]),
                           xaxis_title=None, yaxis_title=None, coloraxis_showscale=False)
        st.plotly_chart(fig3, use_container_width=True)

# ══════════════════════════════════════════════
# TAB 2 – BENCHMARK
# ══════════════════════════════════════════════
with tab_bench:
    gen = data["generales"]
    if sel_periodes:
        gen = gen[gen["periode"].isin(sel_periodes)]
    gen_f = gen[gen["Mot-clé"].isin(sel_mots)]

    conc = (gen_f.groupby("Concurrents")
        .agg(apparition=("% d'apparition","mean"), position=("Position moyenne","mean"),
             note=("Note moyenne","mean"), avis=("Nb d'avis moyen","mean"))
        .reset_index().sort_values("apparition", ascending=False))
    conc["is_human"] = conc["Concurrents"].str.lower().str.contains("human")

    human_row = conc[conc["is_human"]].iloc[0] if conc["is_human"].any() else None
    if human_row is not None:
        rank = int(conc.reset_index(drop=True)[conc.reset_index(drop=True)["is_human"]].index[0]) + 1
        h1, h2, h3, h4 = st.columns(4)
        h1.metric("Visibilité Human", f"{human_row['apparition']:.0f}%")
        h2.metric("Position moyenne", f"{human_row['position']:.1f}", delta="↑ meilleur réseau")
        h3.metric("Note clients", f"{human_row['note']:.2f} ⭐")
        h4.metric("Rang visibilité", f"#{rank} / {len(conc)}")
        st.markdown("")

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        st.markdown('<div class="section-hdr">Visibilité (% d\'apparition)</div>', unsafe_allow_html=True)
        conc_s = conc.sort_values("apparition")
        colors = [COLORS["human"] if h else "#1e3a5f" for h in conc_s["is_human"]]
        fig_app = go.Figure(go.Bar(
            y=conc_s["Concurrents"], x=conc_s["apparition"], orientation="h",
            marker_color=colors, text=conc_s["apparition"].round(0).astype(int).astype(str)+"%",
            textposition="outside"))
        plotly_layout(fig_app, 380)
        fig_app.update_layout(xaxis_range=[0,105], xaxis_title=None, yaxis_title=None)
        st.plotly_chart(fig_app, use_container_width=True)

    with col_b2:
        st.markdown('<div class="section-hdr">Position moyenne (↓ = mieux)</div>', unsafe_allow_html=True)
        conc_p = conc.sort_values("position")
        colors_p = [COLORS["top3"] if h else "#1e3a5f" for h in conc_p["is_human"]]
        fig_pos = go.Figure(go.Bar(
            x=conc_p["Concurrents"], y=conc_p["position"], marker_color=colors_p,
            text=conc_p["position"].round(1), textposition="outside"))
        plotly_layout(fig_pos, 380)
        fig_pos.update_layout(
            yaxis=dict(autorange="reversed", gridcolor=COLORS["grid"]),
            xaxis=dict(tickangle=-30), xaxis_title=None, yaxis_title=None)
        st.plotly_chart(fig_pos, use_container_width=True)

    st.markdown('<div class="section-hdr">Tableau comparatif</div>', unsafe_allow_html=True)
    pivot = gen_f.pivot_table(
        index="Concurrents", columns="Mot-clé",
        values=["% d'apparition","Position moyenne","Note moyenne"], aggfunc="mean").round(2)
    pivot.columns = [f"{v} | {k}" for v, k in pivot.columns]
    pivot = pivot.reset_index()
    if sel_mots:
        try:
            pivot = pivot.sort_values(f"% d'apparition | {sel_mots[0]}", ascending=False)
        except:
            pass

    def highlight_human(row):
        if "human" in str(row.iloc[0]).lower():
            return ["background-color: #0a2a3f; color: #00d4ff; font-weight: 700"] * len(row)
        return [""] * len(row)

    st.dataframe(pivot.style.apply(highlight_human, axis=1).format(precision=1),
                 use_container_width=True, height=350)

# ══════════════════════════════════════════════
# TAB 3 – AGENCES
# ══════════════════════════════════════════════
with tab_ag:
    sub1, sub2, sub3 = st.tabs(["🏢  Classées", "⚠️  Non classées", "📋  Tableau complet"])

    with sub1:
        ag = (cl.groupby(["Business Id","Nom de l'établissement","dept","dept_label"])
            .agg(pos_moy=("Position","mean"), pos_min=("Position","min"),
                 notation=("Notation", lambda x: pd.to_numeric(x, errors="coerce").mean()),
                 reviews=("reviews","mean"), nb_cl=("Mot-clé","nunique"),
                 mots_cl=("Mot-clé", lambda x: ", ".join(sorted(x.unique()))))
            .reset_index())
        ag["score"] = ag.apply(lambda r: seo_score(r["pos_moy"], r["nb_cl"], total_mots, r["notation"]), axis=1)

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Agences classées", len(ag))
        k2.metric("Couvrent 3 mots-clés", int((ag["nb_cl"] == 3).sum()))
        k3.metric("Score SEO > 70", int((ag["score"] >= 70).sum()))
        k4.metric("Note moy.", f"{ag['notation'].mean():.2f} ⭐" if len(ag) else "–")

        top30 = ag.nlargest(30, "score")
        fig_sc = px.bar(top30, x="Nom de l'établissement", y="score",
                        color="score", color_continuous_scale=["#f87171","#fbbf24","#4ade80"],
                        text="score", title="Score SEO Local – Top 30 agences")
        fig_sc.update_traces(textposition="outside")
        plotly_layout(fig_sc, 320)
        fig_sc.update_layout(coloraxis_showscale=False,
                              xaxis=dict(tickangle=-40, tickfont_size=9),
                              yaxis_title=None, xaxis_title=None)
        st.plotly_chart(fig_sc, use_container_width=True)

        display = ag[["Nom de l'établissement","dept","dept_label","pos_moy","pos_min","notation","reviews","nb_cl","mots_cl","score"]].copy()
        display.columns = ["Agence","Dept","Département","Pos. moy.","Meill. pos.","Note","Avis moy.","Nb mots-clés","Mots-clés couverts","Score SEO"]
        display["Pos. moy."] = display["Pos. moy."].round(1)
        display["Note"] = display["Note"].round(2)
        display["Avis moy."] = display["Avis moy."].round(0)

        def color_score(val):
            if pd.isna(val): return ""
            return f"background-color: {'#1a3d1a' if val >= 70 else '#3d3300' if val >= 40 else '#3d1a1a'}"
        def color_pos(val):
            if pd.isna(val): return ""
            return f"background-color: {'#1a3d1a' if val <= 3 else '#3d3300' if val <= 10 else '#3d1a1a'}"

        st.dataframe(
            display.sort_values("Score SEO", ascending=False)
                   .style.applymap(color_score, subset=["Score SEO"])
                         .applymap(color_pos, subset=["Pos. moy."]),
            use_container_width=True, height=420)
        st.download_button("⬇️ Export CSV", display.to_csv(index=False).encode("utf-8"), "classees.csv", "text/csv")

    with sub2:
        nc_ag = (nc.groupby(["Business Id","Nom de l'établissement","dept","dept_label"])
            .agg(mots_nc=("Mot-clé", lambda x: ", ".join(sorted(x.unique()))),
                 nb_nc=("Mot-clé","nunique"))
            .reset_index())
        nc_ag["aussi_classee"] = nc_ag["Business Id"].isin(set(cl["Business Id"].unique()))
        nc_ag["priorite"] = nc_ag.apply(
            lambda r: "🔴 Critique (aucun classement)" if not r["aussi_classee"] else "🟡 Gaps à combler", axis=1)

        k1, k2, k3 = st.columns(3)
        k1.metric("Non classées", len(nc_ag))
        k2.metric("🔴 Critique", int((~nc_ag["aussi_classee"]).sum()))
        k3.metric("🟡 Gaps partiels", int(nc_ag["aussi_classee"].sum()))

        nc_dept = (nc_ag.groupby(["dept","dept_label"]).size().reset_index(name="count")
            .sort_values("count", ascending=False).head(15))
        nc_dept["label"] = nc_dept["dept"] + " – " + nc_dept["dept_label"].fillna("")
        fig_nc = px.bar(nc_dept, x="label", y="count",
                        color="count", color_continuous_scale=["#fbbf24","#f87171"], text="count")
        fig_nc.update_traces(textposition="outside")
        plotly_layout(fig_nc, 300)
        fig_nc.update_layout(coloraxis_showscale=False, xaxis=dict(tickangle=-30),
                              xaxis_title=None, yaxis_title=None)
        st.plotly_chart(fig_nc, use_container_width=True)

        st.dataframe(
            nc_ag[["Nom de l'établissement","dept","dept_label","mots_nc","nb_nc","priorite"]]
            .rename(columns={"Nom de l'établissement":"Agence","dept":"Dept","dept_label":"Département",
                              "mots_nc":"Mots-clés manquants","nb_nc":"Nb gaps","priorite":"Priorité"})
            .sort_values(["Priorité","Nb gaps"], ascending=[True,False]),
            use_container_width=True, height=380)
        st.download_button("⬇️ Export CSV", nc_ag.to_csv(index=False).encode("utf-8"), "non_classees.csv", "text/csv")

    with sub3:
        search = st.text_input("🔍 Rechercher")
        type_sel = st.selectbox("Type", ["Toutes","Classée","Non classée"])
        cl_exp = cl[["Nom de l'établissement","Mot-clé","Position","Notation","reviews","dept","dept_label","statut","periode"]].copy()
        cl_exp["Type"] = "Classée"
        nc_exp = nc[["Nom de l'établissement","Mot-clé","dept","dept_label","periode"]].copy()
        nc_exp[["Position","Notation","reviews","statut"]] = None
        nc_exp["Type"] = "Non classée"
        full = pd.concat([cl_exp, nc_exp], ignore_index=True)
        if search:
            full = full[full["Nom de l'établissement"].str.contains(search, case=False, na=False)]
        if type_sel != "Toutes":
            full = full[full["Type"] == type_sel]
        st.dataframe(full.sort_values("Nom de l'établissement"), use_container_width=True, height=500)
        st.download_button("⬇️ Export CSV complet", full.to_csv(index=False).encode("utf-8"), "export_complet.csv", "text/csv")


# ══════════════════════════════════════════════
# TAB 4 – CARTE
# ══════════════════════════════════════════════
with tab_map:
    st.markdown('<div class="section-hdr">Carte SEO Local – Agences & Concurrents</div>', unsafe_allow_html=True)

    # Build per-agency stats for map
    ag_map_stats = (cl.groupby(["Business Id","Nom de l'établissement","dept","dept_label","lat","lon"])
        .agg(pos_moy=("Position","mean"), pos_min=("Position","min"),
             notation=("Notation", lambda x: pd.to_numeric(x, errors="coerce").mean()),
             reviews=("reviews","mean"), nb_cl=("Mot-clé","nunique"),
             mots_cl=("Mot-clé", lambda x: ", ".join(sorted(x.unique()))))
        .reset_index())
    ag_map_stats["score"] = ag_map_stats.apply(
        lambda r: seo_score(r["pos_moy"], r["nb_cl"], total_mots, r["notation"]), axis=1)

    nc_ids = set(nc["Business Id"].unique())
    cl_ids = set(cl["Business Id"].unique())

    ag_map_stats["priorite"] = ag_map_stats.apply(
        lambda r: get_priorite(r["pos_moy"],
                                len([i for i in data["mots_cles"] if i not in r["mots_cl"]]),
                                r["notation"]), axis=1)

    # Also add non-classified agencies
    nc_ref = data["ref"][data["ref"]["Business Id"].isin(nc_ids - cl_ids)].copy()
    nc_ref["priorite"] = "🔴 Urgent"
    nc_ref["pos_moy"] = None
    nc_ref["score"] = 0
    nc_ref["mots_cl"] = ""
    nc_ref["notation"] = None
    nc_ref["reviews"] = None

    col_map1, col_map2 = st.columns([3, 2])

    with col_map1:
        # Map controls
        mc1, mc2 = st.columns(2)
        with mc1:
            show_conc = st.checkbox("Afficher les concurrents", value=True)
        with mc2:
            radius_km = st.slider("Radius concurrents (km)", 1, 20, 5)

        # Filter by priority
        prio_filter = st.multiselect("Filtrer par priorité",
            ["🔴 Urgent","🟡 Important","🟢 Opportunité"],
            default=["🔴 Urgent","🟡 Important","🟢 Opportunité"])

        # Build Folium map
        valid = ag_map_stats[ag_map_stats["lat"].notna() & ag_map_stats["priorite"].isin(prio_filter)]
        nc_valid = nc_ref[nc_ref["lat"].notna()]

        if len(valid) > 0:
            center_lat = valid["lat"].mean()
            center_lon = valid["lon"].mean()
        else:
            center_lat, center_lon = 46.2, 2.2

        m = folium.Map(location=[center_lat, center_lon], zoom_start=6,
                       tiles="OpenStreetMap", prefer_canvas=True)

        PRIO_ICON_COLORS = {
            "🔴 Urgent": "red",
            "🟡 Important": "orange",
            "🟢 Opportunité": "green",
        }

        # Plot Human agencies
        for _, row in valid.iterrows():
            icon_color = PRIO_ICON_COLORS.get(row["priorite"], "blue")
            popup_html = f"""
            <div style='font-family:sans-serif;min-width:220px'>
              <b style='color:#1a3a5c;font-size:13px'>{row["Nom de l'établissement"]}</b><br>
              <span style='color:#666;font-size:11px'>{row["dept"]} – {row.get("dept_label","")}</span>
              <hr style='margin:6px 0'>
              <table style='font-size:11px;width:100%'>
                <tr><td>⭐ Note</td><td><b>{f'{row["notation"]:.2f}' if pd.notna(row.get("notation")) else '–'}</b></td></tr>
                <tr><td>💬 Avis</td><td><b>{int(row["reviews"]) if pd.notna(row.get("reviews")) else '–'}</b></td></tr>
                <tr><td>📍 Pos. moy.</td><td><b>{f'{row["pos_moy"]:.1f}' if pd.notna(row.get("pos_moy")) else '–'}</b></td></tr>
                <tr><td>🎯 Score SEO</td><td><b>{row["score"]}</b></td></tr>
              </table>
              <div style='margin-top:6px;font-size:10px;color:#888'>Mots-clés : {row["mots_cl"]}</div>
              <div style='margin-top:4px;font-size:11px;'>{row["priorite"]}</div>
            </div>
            """
            folium.Marker(
                location=[row["lat"], row["lon"]],
                popup=folium.Popup(popup_html, max_width=260),
                tooltip=f"🏠 {row['Nom de l\'établissement']}",
                icon=folium.Icon(color=icon_color, icon="home", prefix="fa"),
            ).add_to(m)

        # Plot non-classified
        for _, row in nc_valid.iterrows():
            if row["Business Id"] in cl_ids:
                continue
            popup_html = f"""
            <div style='font-family:sans-serif;min-width:200px'>
              <b style='color:#c0392b'>{row["nom"]}</b><br>
              <span style='color:#666;font-size:11px'>{row["dept"]} – {row.get("dept_label","")}</span>
              <hr style='margin:6px 0'>
              <div style='font-size:11px;color:#e74c3c'>⚠️ Non classée – aucun mot-clé positionné</div>
            </div>
            """
            folium.Marker(
                location=[row["lat"], row["lon"]],
                popup=folium.Popup(popup_html, max_width=240),
                tooltip=f"⚠️ {row['nom']} (non classée)",
                icon=folium.Icon(color="red", icon="times", prefix="fa"),
            ).add_to(m)

        # Plot competitors in radius of selected/all agencies
        if show_conc and len(conc_geo) > 0:
            shown_conc = set()
            for _, ag_row in valid.head(50).iterrows():  # limit to 50 agencies for perf
                nearby = get_competitors_in_radius(ag_row["lat"], ag_row["lon"], conc_geo, radius_km)
                for _, c_row in nearby.iterrows():
                    key = (c_row["nom"], round(c_row["lat"],3), round(c_row["lon"],3))
                    if key in shown_conc:
                        continue
                    shown_conc.add(key)
                    popup_conc = f"""
                    <div style='font-family:sans-serif;min-width:200px'>
                      <b style='color:#8B4513'>{c_row["nom"]}</b><br>
                      <span style='font-size:10px;color:#666'>{c_row["reseau"].upper()}</span>
                      <hr style='margin:6px 0'>
                      <table style='font-size:11px;width:100%'>
                        <tr><td>📍 Pos. moy.</td><td><b>{f'{c_row["pos_moy"]:.1f}' if pd.notna(c_row.get("pos_moy")) else '–'}</b></td></tr>
                        <tr><td>⭐ Note</td><td><b>{f'{c_row["notation"]:.2f}' if pd.notna(c_row.get("notation")) else '–'}</b></td></tr>
                        <tr><td>💬 Avis</td><td><b>{int(c_row["reviews"]) if pd.notna(c_row.get("reviews")) else '–'}</b></td></tr>
                        <tr><td>📏 Distance</td><td><b>{c_row["distance_km"]} km</b></td></tr>
                      </table>
                      <div style='font-size:10px;color:#888;margin-top:4px'>Mots-clés: {", ".join(c_row["mots"]) if isinstance(c_row.get("mots"), list) else ""}</div>
                    </div>
                    """
                    folium.Marker(
                        location=[c_row["lat"], c_row["lon"]],
                        popup=folium.Popup(popup_conc, max_width=240),
                        tooltip=f"🏢 {c_row['nom']} ({c_row['reseau']})",
                        icon=folium.Icon(color="gray", icon="building", prefix="fa"),
                    ).add_to(m)

        map_data = st_folium(m, width="100%", height=520, returned_objects=["last_object_clicked"])

    with col_map2:
        st.markdown('<div class="section-hdr">Légende</div>', unsafe_allow_html=True)
        for prio, color in [("🟢 Opportunité","#4ade80"),("🟡 Important","#fbbf24"),("🔴 Urgent","#f87171")]:
            n = int((ag_map_stats["priorite"] == prio).sum())
            st.markdown(f"""
            <div style='display:flex;align-items:center;gap:10px;margin-bottom:8px;
                        background:#060e1a;border:1px solid #0d2035;border-left:3px solid {color};
                        border-radius:4px;padding:8px 12px;'>
              <span style='font-size:16px;'>{prio.split()[0]}</span>
              <div>
                <div style='font-size:12px;color:{color};font-weight:600;'>{prio.split("  ")[-1] if "  " in prio else " ".join(prio.split()[1:])}</div>
                <div style='font-size:10px;color:#2a5a7a;font-family:DM Mono,monospace;'>{n} agence(s)</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style='display:flex;align-items:center;gap:10px;margin-bottom:8px;
                    background:#060e1a;border:1px solid #0d2035;border-left:3px solid #94a3b8;
                    border-radius:4px;padding:8px 12px;'>
          <span style='font-size:16px;'>🏢</span>
          <div>
            <div style='font-size:12px;color:#94a3b8;font-weight:600;'>Concurrents</div>
            <div style='font-size:10px;color:#2a5a7a;font-family:DM Mono,monospace;'>Dans radius {radius_km}km</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # If user clicked an agency on the map, show competitor analysis
        st.markdown('<div class="section-hdr" style="margin-top:20px">Analyse concurrents proches</div>', unsafe_allow_html=True)

        # Agency selector for radius analysis
        ag_sel_name = st.selectbox(
            "Sélectionner une agence",
            [""] + sorted(ag_map_stats["Nom de l'établissement"].tolist()),
            key="map_ag_sel"
        )

        if ag_sel_name:
            ag_row = ag_map_stats[ag_map_stats["Nom de l'établissement"] == ag_sel_name].iloc[0]
            nearby = get_competitors_in_radius(ag_row["lat"], ag_row["lon"], conc_geo, radius_km)

            if len(nearby) == 0:
                st.info(f"Aucun concurrent trouvé dans {radius_km}km")
            else:
                # Aggregate by reseau
                reseau_agg = (nearby.groupby("reseau")
                    .agg(nb=("nom","count"), pos_moy=("pos_moy","mean"),
                         notation=("notation","mean"), reviews=("reviews","mean"))
                    .reset_index().sort_values("pos_moy"))

                st.markdown(f"**{len(nearby)} concurrent(s) trouvé(s)** dans {radius_km}km")

                # Compare Human vs local competitors
                human_pos = ag_row["pos_moy"]
                human_note = ag_row["notation"]
                local_pos = nearby["pos_moy"].mean() if len(nearby) > 0 else None
                local_note = nearby["notation"].mean() if len(nearby) > 0 else None

                c1, c2 = st.columns(2)
                c1.metric("Pos. moy. Human", f"{human_pos:.1f}" if pd.notna(human_pos) else "–",
                          delta=f"{human_pos - local_pos:.1f} vs concurrents" if local_pos and pd.notna(human_pos) else None,
                          delta_color="inverse")
                c2.metric("Note Human", f"{human_note:.2f}" if pd.notna(human_note) else "–",
                          delta=f"{human_note - local_note:+.2f} vs concurrents" if local_note and pd.notna(human_note) else None)

                st.markdown("**Par réseau concurrent**")
                for _, rrow in reseau_agg.iterrows():
                    better = pd.notna(human_pos) and rrow["pos_moy"] < human_pos
                    color = "#f87171" if better else "#4ade80"
                    st.markdown(f"""
                    <div style='background:#060e1a;border:1px solid #0d2035;border-left:3px solid {color};
                                border-radius:4px;padding:8px 12px;margin-bottom:6px;'>
                      <div style='font-size:12px;font-weight:600;color:#e8edf2;'>{rrow["reseau"].upper()}</div>
                      <div style='font-size:10px;color:#4a7a9b;font-family:DM Mono,monospace;'>
                        {int(rrow["nb"])} agence(s) · Pos. moy. <b style='color:{color}'>{rrow["pos_moy"]:.1f}</b>
                        · Note <b>{rrow["notation"]:.2f}⭐</b> · Avis moy. {int(rrow["reviews"]) if pd.notna(rrow["reviews"]) else "–"}
                      </div>
                      {"<div style='font-size:10px;color:#f87171;margin-top:3px;'>⚠️ Mieux positionné – analyser leurs pratiques</div>" if better else ""}
                    </div>
                    """, unsafe_allow_html=True)

                # Best practices from top local competitor
                best_local = nearby[nearby["pos_moy"] == nearby["pos_moy"].min()].iloc[0]
                st.markdown("**🏆 Meilleur concurrent local**")
                st.markdown(f"""
                <div style='background:#060e1a;border:1px solid #00d4ff33;border-radius:6px;padding:12px;'>
                  <div style='font-size:12px;font-weight:600;color:#00d4ff;'>{best_local["nom"]}</div>
                  <div style='font-size:10px;color:#4a7a9b;'>{best_local["reseau"].upper()} · {best_local["distance_km"]}km</div>
                  <div style='font-size:11px;color:#8bafc8;margin-top:8px;'>
                    📍 Position {best_local["pos_moy"]:.1f} · ⭐ {best_local["notation"]:.2f} · 💬 {int(best_local["reviews"]) if pd.notna(best_local.get("reviews")) else "–"} avis
                  </div>
                  <div style='font-size:10px;color:#2a5a7a;margin-top:6px;'>Mots-clés : {", ".join(best_local["mots"]) if isinstance(best_local.get("mots"), list) else ""}</div>
                  <div style='margin-top:8px;font-size:10px;color:#fbbf24;'>
                    💡 Best practices probables : volume d'avis élevé, GBP optimisé, photos professionnelles
                  </div>
                </div>
                """, unsafe_allow_html=True)


# ══════════════════════════════════════════════
# TAB 5 – PLANS D'ACTION
# ══════════════════════════════════════════════
with tab_plan:
    ag_map2: dict = {}
    for _, row in cl.iterrows():
        bid = row["Business Id"]
        if bid not in ag_map2:
            ag_map2[bid] = {
                "nom": row["Nom de l'établissement"], "dept": row["dept"], "dept_label": row["dept_label"],
                "positions": [], "notes": [], "reviews": [], "mots_cl": set(), "mots_nc": set(),
            }
        ag_map2[bid]["positions"].append(row["Position"])
        ag_map2[bid]["mots_cl"].add(row["Mot-clé"])
        if pd.notna(row["Notation"]): ag_map2[bid]["notes"].append(float(row["Notation"]))
        if pd.notna(row["reviews"]): ag_map2[bid]["reviews"].append(float(row["reviews"]))

    for _, row in nc.iterrows():
        bid = row["Business Id"]
        if bid not in ag_map2:
            ag_map2[bid] = {
                "nom": row["Nom de l'établissement"], "dept": row["dept"], "dept_label": row["dept_label"],
                "positions": [], "notes": [], "reviews": [], "mots_cl": set(), "mots_nc": set(),
            }
        ag_map2[bid]["mots_nc"].add(row["Mot-clé"])

    plans = []
    for bid, a in ag_map2.items():
        pos_moy = sum(a["positions"]) / len(a["positions"]) if a["positions"] else None
        note_moy = sum(a["notes"]) / len(a["notes"]) if a["notes"] else None
        rev_moy = sum(a["reviews"]) / len(a["reviews"]) if a["reviews"] else None
        nb_cl_count = len(a["mots_cl"])
        nb_nc_count = len(a["mots_nc"])
        score = seo_score(pos_moy, nb_cl_count, total_mots, note_moy) if pos_moy else 0
        priorite = get_priorite(pos_moy, nb_nc_count, note_moy)

        actions = []
        if pos_moy is None:
            actions.append("Activer / créer la fiche Google Business Profile pour tous les mots-clés cibles")
        elif pos_moy > 10:
            actions.append("Optimiser fiche GBP : catégories, photos, description locale, services")
        elif pos_moy > 5:
            actions.append("Renforcer signaux locaux : posts GBP réguliers, Q&A, attributs")
        if nb_nc_count > 0:
            actions.append(f"Combler les gaps sur : {', '.join(sorted(a['mots_nc']))} — vérifier cohérence catégories GBP")
        if note_moy and not pd.isna(note_moy):
            if note_moy < 4.0:
                actions.append(f"Note critique ({note_moy:.2f}) — répondre aux avis négatifs + processus de collecte")
            elif note_moy < 4.3:
                actions.append(f"Note à améliorer ({note_moy:.2f}) — encourager les clients satisfaits")
        if rev_moy and rev_moy < 30:
            actions.append(f"Volume d'avis très faible ({rev_moy:.0f}) — campagne de sollicitation")
        if not actions:
            actions.append("Maintenir les bonnes pratiques — surveiller la concurrence locale")

        plans.append({
            "id": bid, "nom": a["nom"], "dept": a["dept"], "dept_label": a["dept_label"],
            "pos_moy": round(pos_moy, 1) if pos_moy else None,
            "note_moy": round(note_moy, 2) if note_moy else None,
            "rev_moy": round(rev_moy) if rev_moy else None,
            "nb_cl": nb_cl_count, "nb_nc": nb_nc_count, "score": score,
            "priorite": priorite, "actions": actions,
            "mots_cl": sorted(a["mots_cl"]), "mots_nc": sorted(a["mots_nc"]),
        })

    plans.sort(key=lambda x: ({"🔴 Urgent": 0, "🟡 Important": 1, "🟢 Opportunité": 2}.get(x["priorite"], 3), -x["score"]))
    counts = {p: sum(1 for x in plans if x["priorite"] == p) for p in ["🔴 Urgent","🟡 Important","🟢 Opportunité"]}

    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Total agences", len(plans))
    p2.metric("🔴 Urgent", counts.get("🔴 Urgent", 0))
    p3.metric("🟡 Important", counts.get("🟡 Important", 0))
    p4.metric("🟢 Opportunité", counts.get("🟢 Opportunité", 0))
    st.markdown("")

    col_pf, col_search, col_exp = st.columns([3, 4, 2])
    with col_pf:
        prio_sel = st.selectbox("Priorité", ["Toutes","🔴 Urgent","🟡 Important","🟢 Opportunité"])
    with col_search:
        search_plan = st.text_input("🔍 Rechercher", key="plan_search")
    with col_exp:
        st.markdown("<br>", unsafe_allow_html=True)
        export_plan = st.button("⬇️ Export CSV", key="export_plan")

    visible = plans
    if prio_sel != "Toutes":
        visible = [p for p in visible if p["priorite"] == prio_sel]
    if search_plan:
        visible = [p for p in visible if search_plan.lower() in p["nom"].lower()]

    st.caption(f"{len(visible)} agence(s) affichée(s)")

    for plan in visible:
        prio_color = PRIO_COLORS.get(plan["priorite"], "#8bafc8")
        score_color = "#4ade80" if plan["score"] >= 70 else ("#fbbf24" if plan["score"] >= 40 else "#f87171")
        pos_color = "#4ade80" if (plan["pos_moy"] and plan["pos_moy"] <= 3) else ("#fbbf24" if (plan["pos_moy"] and plan["pos_moy"] <= 10) else "#f87171")

        with st.expander(f"{plan['priorite']}  {plan['nom']}  ·  {plan['dept']} {plan['dept_label'] or ''}"):
            col_kpi, col_act = st.columns([1, 2])
            with col_kpi:
                st.markdown(f"""
                <div style='display:grid;grid-template-columns:1fr 1fr;gap:8px;'>
                  <div style='background:#060e1a;border:1px solid #0d2035;border-radius:6px;padding:10px;'>
                    <div style='font-family:DM Mono,monospace;font-size:9px;color:#2a5a7a;text-transform:uppercase;'>Score SEO</div>
                    <div style='font-size:1.6rem;font-weight:700;color:{score_color};'>{plan['score']}</div>
                  </div>
                  <div style='background:#060e1a;border:1px solid #0d2035;border-radius:6px;padding:10px;'>
                    <div style='font-family:DM Mono,monospace;font-size:9px;color:#2a5a7a;text-transform:uppercase;'>Position</div>
                    <div style='font-size:1.6rem;font-weight:700;color:{pos_color};'>{plan['pos_moy'] or '–'}</div>
                  </div>
                  <div style='background:#060e1a;border:1px solid #0d2035;border-radius:6px;padding:10px;'>
                    <div style='font-family:DM Mono,monospace;font-size:9px;color:#2a5a7a;text-transform:uppercase;'>Note</div>
                    <div style='font-size:1.6rem;font-weight:700;color:#00d4ff;'>{plan['note_moy'] or '–'}</div>
                  </div>
                  <div style='background:#060e1a;border:1px solid #0d2035;border-radius:6px;padding:10px;'>
                    <div style='font-family:DM Mono,monospace;font-size:9px;color:#2a5a7a;text-transform:uppercase;'>Avis</div>
                    <div style='font-size:1.6rem;font-weight:700;color:#00d4ff;'>{plan['rev_moy'] or '–'}</div>
                  </div>
                </div>
                <div style='margin-top:10px;font-family:DM Mono,monospace;font-size:9px;color:#2a5a7a;text-transform:uppercase;margin-bottom:6px;'>Couverture</div>
                """, unsafe_allow_html=True)
                for mk in data["mots_cles"]:
                    ok = mk in plan["mots_cl"]
                    missing = mk in plan["mots_nc"]
                    icon = "✓" if ok else ("✗" if missing else "–")
                    color = "#4ade80" if ok else ("#f87171" if missing else "#2a5a7a")
                    st.markdown(f"<span style='font-family:DM Mono,monospace;font-size:11px;color:{color};'>{icon} {mk}</span>", unsafe_allow_html=True)

            with col_act:
                st.markdown('<div style="font-family:DM Mono,monospace;font-size:9px;color:#2a5a7a;text-transform:uppercase;margin-bottom:8px;">Actions recommandées</div>', unsafe_allow_html=True)
                for i, action in enumerate(plan["actions"], 1):
                    st.markdown(f"""
                    <div style='display:flex;gap:10px;margin-bottom:8px;padding:10px 12px;background:#060e1a;
                                border:1px solid #0d2035;border-left:3px solid {prio_color};border-radius:4px;'>
                      <span style='font-family:DM Mono,monospace;font-size:10px;color:#2a5a7a;flex-shrink:0;'>{i}.</span>
                      <span style='font-size:12px;color:#8bafc8;'>{action}</span>
                    </div>
                    """, unsafe_allow_html=True)

    if export_plan:
        rows = [{"Agence": p["nom"], "Département": p["dept"], "Priorité": p["priorite"],
                 "Score SEO": p["score"], "Position moy.": p["pos_moy"], "Note": p["note_moy"],
                 "Avis": p["rev_moy"], "Mots-clés couverts": ", ".join(p["mots_cl"]),
                 "Mots-clés manquants": ", ".join(p["mots_nc"]), "Actions": " | ".join(p["actions"])}
                for p in visible]
        st.download_button("📥 Télécharger", pd.DataFrame(rows).to_csv(index=False).encode("utf-8"),
                           f"plan_action_{data['periode'].replace(' ','_')}.csv", "text/csv")
