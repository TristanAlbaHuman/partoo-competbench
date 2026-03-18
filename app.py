import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io

from data_processing import (
    load_excel, merge_datasets, apply_filters,
    seo_score, get_priorite, DEPT_NAMES
)

# ──────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="PARTOO · SEO Local – Human Immobilier",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# CUSTOM CSS
# ──────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=DM+Sans:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #04090f !important;
    border-right: 1px solid #0d2035;
}
section[data-testid="stSidebar"] * { color: #8bafc8 !important; }
section[data-testid="stSidebar"] .stMultiSelect label,
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stFileUploader label {
    font-family: 'DM Mono', monospace !important;
    font-size: 10px !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    color: #2a5a7a !important;
}
section[data-testid="stSidebar"] .stFileUploader {
    border: 1px dashed #0d2035 !important;
    border-radius: 6px !important;
    padding: 4px !important;
}

/* Main area */
.main .block-container { padding: 1.5rem 2rem 2rem 2rem; max-width: 100%; }

/* Metric cards */
div[data-testid="metric-container"] {
    background: #04090f;
    border: 1px solid #0d2035;
    border-radius: 8px;
    padding: 14px 18px !important;
}
div[data-testid="metric-container"] label {
    font-family: 'DM Mono', monospace !important;
    font-size: 10px !important;
    letter-spacing: 0.14em !important;
    text-transform: uppercase !important;
    color: #2a5a7a !important;
}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-size: 1.9rem !important;
    font-weight: 700 !important;
    color: #00d4ff !important;
}
div[data-testid="metric-container"] [data-testid="stMetricDelta"] { font-size: 0.7rem !important; }

/* Tabs */
button[data-baseweb="tab"] {
    font-family: 'DM Mono', monospace !important;
    font-size: 11px !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: #2a5a7a !important;
    border-bottom: 2px solid transparent !important;
    padding: 8px 16px !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #00d4ff !important;
    border-bottom-color: #00d4ff !important;
}
div[data-testid="stHorizontalBlock"] > div { gap: 12px; }

/* Dataframe */
div[data-testid="stDataFrame"] { border: 1px solid #0d2035 !important; border-radius: 8px !important; }

/* Section headers */
.section-hdr {
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #2a5a7a;
    border-bottom: 1px solid #0d2035;
    padding-bottom: 6px;
    margin: 20px 0 12px 0;
}
.kpi-row { display: flex; gap: 12px; margin-bottom: 16px; }
.badge {
    display: inline-block;
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    padding: 2px 8px;
    border-radius: 20px;
    border: 1px solid;
}
</style>
""", unsafe_allow_html=True)

COLORS = {
    "human":     "#00d4ff",
    "top3":      "#4ade80",
    "top5":      "#60a5fa",
    "top10":     "#fbbf24",
    "hors":      "#f97316",
    "nonclasse": "#f87171",
    "bg":        "#04090f",
    "grid":      "#0d2035",
    "text":      "#8bafc8",
}

STATUT_COLORS = {
    "Top 3":       COLORS["top3"],
    "Top 5":       COLORS["top5"],
    "Top 10":      COLORS["top10"],
    "Hors Top 10": COLORS["hors"],
    "Non classé":  COLORS["nonclasse"],
}

def plotly_layout(fig, height=320, legend=False):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text"], family="DM Mono, monospace", size=10),
        height=height,
        margin=dict(t=30, b=20, l=10, r=10),
        showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=-0.4, font_size=10) if legend else {},
        xaxis=dict(gridcolor=COLORS["grid"], zeroline=False),
        yaxis=dict(gridcolor=COLORS["grid"], zeroline=False),
    )
    return fig


# ──────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding:4px 0 16px 0;'>
      <div style='font-family:DM Mono,monospace;font-size:10px;letter-spacing:.16em;color:#00d4ff;margin-bottom:4px;'>PARTOO</div>
      <div style='font-size:15px;font-weight:700;color:#e8edf2;'>Human Immobilier</div>
      <div style='font-family:DM Mono,monospace;font-size:10px;color:#1e3a57;margin-top:2px;'>SEO LOCAL BENCHMARK</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ── File upload
    st.markdown("**📂 Imports PARTOO**")
    uploaded = st.file_uploader(
        "Charger export(s) .xlsx",
        type=["xlsx"],
        accept_multiple_files=True,
        help="Glissez un ou plusieurs exports. Chaque fichier = une période.",
    )

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

    # ── Filters
    st.markdown("**🔍 Filtres**")

    sel_periodes = []
    all_periodes = data["generales"]["periode"].unique().tolist() if "periode" in data["generales"].columns else [data["periode"]]
    if len(all_periodes) > 1:
        sel_periodes = st.multiselect("Période(s)", all_periodes, default=all_periodes)
    else:
        sel_periodes = all_periodes

    sel_mots = st.multiselect(
        "Mots-clés",
        data["mots_cles"],
        default=data["mots_cles"],
    )

    dept_opts = data["depts"]
    dept_fmt = {d: f"{d} – {DEPT_NAMES.get(d, '')}" for d in dept_opts}
    sel_depts = st.multiselect(
        "Département(s)",
        dept_opts,
        default=[],
        format_func=lambda x: dept_fmt.get(x, x),
    )

    all_agences = sorted(data["ref"]["nom"].unique().tolist())
    sel_agences = st.multiselect("Agence(s)", all_agences, default=[])

    st.divider()
    st.caption(f"v1.0 · {data['periode']}")


# ──────────────────────────────────────────────
# FILTERED DATA
# ──────────────────────────────────────────────
if not sel_mots:
    st.warning("Sélectionne au moins un mot-clé dans les filtres.")
    st.stop()

f = apply_filters(data, sel_mots, sel_depts, sel_agences)
cl = f["classees"]
nc = f["non_classees"]
total_mots = len(sel_mots)


# ──────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────
st.markdown(f"""
<div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;'>
  <div>
    <h2 style='margin:0;font-size:1.3rem;color:#e8edf2;font-weight:700;'>Competitive Benchmark – Human Immobilier</h2>
    <p style='margin:2px 0 0 0;font-family:DM Mono,monospace;font-size:10px;color:#2a5a7a;letter-spacing:.1em;'>
      PARTOO · {data['periode']} · {', '.join(sel_mots)}
    </p>
  </div>
</div>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# TABS
# ──────────────────────────────────────────────
tab_ov, tab_bench, tab_ag, tab_plan = st.tabs([
    "◈  Vue d'ensemble",
    "⊕  Benchmark",
    "◎  Agences",
    "◆  Plans d'action",
])


# ══════════════════════════════════════════════
# TAB 1 – VUE D'ENSEMBLE
# ══════════════════════════════════════════════
with tab_ov:

    # ── KPIs
    nb_total   = data["ref"]["Business Id"].nunique()
    nb_cl      = cl["Business Id"].nunique()
    nb_nc      = nc["Business Id"].nunique()
    nb_top3    = cl[cl["statut"] == "Top 3"]["Business Id"].nunique()
    pos_moy    = cl["Position"].mean() if len(cl) else 0
    notes      = pd.to_numeric(cl["Notation"], errors="coerce").dropna()
    note_moy   = notes.mean() if len(notes) else 0
    avis_moy   = cl["reviews"].mean() if len(cl) else 0

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Réseau total", nb_total)
    c2.metric("Classées", nb_cl, delta=f"{nb_cl/nb_total*100:.0f}% du réseau")
    c3.metric("Non classées", nb_nc, delta=f"-{nb_nc}", delta_color="inverse")
    c4.metric("Top 3 🥇", nb_top3, delta=f"{nb_top3/max(nb_cl,1)*100:.0f}% des classées")
    c5.metric("Position moyenne", f"{pos_moy:.1f}" if pos_moy else "–")
    c6.metric("Note moyenne", f"{note_moy:.2f} ⭐" if note_moy else "–")

    st.markdown("")

    # ── Row 2
    col_a, col_b, col_c = st.columns([2, 2, 3])

    with col_a:
        st.markdown('<div class="section-hdr">Distribution des statuts</div>', unsafe_allow_html=True)
        statut_data = []
        for s, rng in [("Top 3",(1,3)),("Top 5",(4,5)),("Top 10",(6,10)),("Hors Top 10",(11,20))]:
            n = cl[cl["Position"].between(rng[0], rng[1])]["Business Id"].nunique()
            statut_data.append({"Statut": s, "Agences": n})
        statut_data.append({"Statut": "Non classé", "Agences": nb_nc})
        df_stat = pd.DataFrame(statut_data)
        fig = px.bar(df_stat, x="Statut", y="Agences",
                     color="Statut",
                     color_discrete_map=STATUT_COLORS,
                     text="Agences")
        fig.update_traces(textposition="outside")
        fig = plotly_layout(fig, height=300)
        fig.update_layout(xaxis_title=None, yaxis_title=None, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.markdown('<div class="section-hdr">Couverture par mot-clé</div>', unsafe_allow_html=True)
        mk_rows = []
        for mk in sel_mots:
            n_cl = cl[cl["Mot-clé"] == mk]["Business Id"].nunique()
            n_nc = nc[nc["Mot-clé"] == mk]["Business Id"].nunique()
            p = cl[cl["Mot-clé"] == mk]["Position"].mean()
            mk_rows.append({"Mot-clé": mk, "Classées": n_cl, "Non classées": n_nc, "Pos. moy": round(p, 1) if p else None})
        df_mk = pd.DataFrame(mk_rows)
        fig2 = px.bar(df_mk.melt(id_vars="Mot-clé", value_vars=["Classées","Non classées"]),
                      x="Mot-clé", y="value", color="variable",
                      color_discrete_map={"Classées": COLORS["human"], "Non classées": COLORS["nonclasse"]},
                      text="value", barmode="group")
        fig2.update_traces(textposition="outside")
        fig2 = plotly_layout(fig2, height=300, legend=True)
        fig2.update_layout(xaxis_title=None, yaxis_title=None)
        st.plotly_chart(fig2, use_container_width=True)

    with col_c:
        st.markdown('<div class="section-hdr">Top 15 départements (agences classées)</div>', unsafe_allow_html=True)
        dept_grp = (
            cl.groupby(["dept", "dept_label"])
            .agg(n=("Business Id", "nunique"), pos=("Position","mean"))
            .reset_index()
            .sort_values("n", ascending=False)
            .head(15)
        )
        dept_grp["label"] = dept_grp["dept"] + " – " + dept_grp["dept_label"].fillna("")
        fig3 = px.bar(dept_grp, x="n", y="label", orientation="h",
                      color="pos",
                      color_continuous_scale=["#4ade80","#fbbf24","#f87171"],
                      text="n")
        fig3.update_traces(textposition="outside")
        fig3 = plotly_layout(fig3, height=380)
        fig3.update_layout(
            yaxis=dict(autorange="reversed", gridcolor=COLORS["grid"]),
            xaxis_title=None, yaxis_title=None,
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig3, use_container_width=True)

    # ── Position distribution
    st.markdown('<div class="section-hdr">Distribution détaillée des positions</div>', unsafe_allow_html=True)
    col_h1, col_h2, col_h3 = st.columns(len(sel_mots) if sel_mots else 1)
    cols_mk = [col_h1, col_h2, col_h3] if len(sel_mots) >= 3 else ([col_h1, col_h2] if len(sel_mots) == 2 else [col_h1])
    for i, mk in enumerate(sel_mots[:3]):
        with cols_mk[i]:
            sub = cl[cl["Mot-clé"] == mk]
            fig_h = px.histogram(sub, x="Position", nbins=20,
                                  color_discrete_sequence=[COLORS["human"]],
                                  title=mk)
            fig_h = plotly_layout(fig_h, height=220)
            fig_h.update_layout(title_font_size=11, xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fig_h, use_container_width=True)


# ══════════════════════════════════════════════
# TAB 2 – BENCHMARK CONCURRENTS
# ══════════════════════════════════════════════
with tab_bench:

    gen = data["generales"]
    if sel_periodes:
        gen = gen[gen["periode"].isin(sel_periodes)]
    gen_f = gen[gen["Mot-clé"].isin(sel_mots)]

    # Agrégation par concurrent
    conc = (
        gen_f.groupby("Concurrents")
        .agg(
            apparition=("% d'apparition", "mean"),
            position=("Position moyenne", "mean"),
            note=("Note moyenne", "mean"),
            avis=("Nb d'avis moyen", "mean"),
        )
        .reset_index()
        .sort_values("apparition", ascending=False)
    )
    conc["is_human"] = conc["Concurrents"].str.lower().str.contains("human")

    # ── Human highlight KPIs
    human_row = conc[conc["is_human"]].iloc[0] if conc["is_human"].any() else None
    if human_row is not None:
        rank = int(conc.reset_index(drop=True)[conc.reset_index(drop=True)["is_human"]].index[0]) + 1
        h1, h2, h3, h4 = st.columns(4)
        h1.metric("Visibilité Human", f"{human_row['apparition']:.0f}%")
        h2.metric("Position moyenne", f"{human_row['position']:.1f}", delta="↑ meilleur réseau", delta_color="normal")
        h3.metric("Note clients", f"{human_row['note']:.2f} ⭐")
        h4.metric("Rang visibilité", f"#{rank} / {len(conc)}")
        st.markdown("")

    # ── Comparatif barres
    col_b1, col_b2 = st.columns(2)

    with col_b1:
        st.markdown('<div class="section-hdr">Visibilité (% d\'apparition)</div>', unsafe_allow_html=True)
        conc_s = conc.sort_values("apparition")
        colors = [COLORS["human"] if h else "#1e3a5f" for h in conc_s["is_human"]]
        fig_app = go.Figure(go.Bar(
            y=conc_s["Concurrents"], x=conc_s["apparition"],
            orientation="h", marker_color=colors,
            text=conc_s["apparition"].round(0).astype(int).astype(str) + "%",
            textposition="outside",
        ))
        plotly_layout(fig_app, height=380)
        fig_app.update_layout(xaxis_range=[0, 105], xaxis_title=None, yaxis_title=None)
        st.plotly_chart(fig_app, use_container_width=True)

    with col_b2:
        st.markdown('<div class="section-hdr">Position moyenne (↓ = mieux)</div>', unsafe_allow_html=True)
        conc_p = conc.sort_values("position")
        colors_p = [COLORS["top3"] if h else "#1e3a5f" for h in conc_p["is_human"]]
        fig_pos = go.Figure(go.Bar(
            x=conc_p["Concurrents"], y=conc_p["position"],
            marker_color=colors_p,
            text=conc_p["position"].round(1),
            textposition="outside",
        ))
        plotly_layout(fig_pos, height=380)
        fig_pos.update_layout(
            yaxis=dict(autorange="reversed", gridcolor=COLORS["grid"]),
            xaxis=dict(tickangle=-30, gridcolor=COLORS["grid"]),
            xaxis_title=None, yaxis_title=None,
        )
        st.plotly_chart(fig_pos, use_container_width=True)

    # ── Tableau comparatif
    st.markdown('<div class="section-hdr">Tableau comparatif complet</div>', unsafe_allow_html=True)

    pivot = gen_f.pivot_table(
        index="Concurrents",
        columns="Mot-clé",
        values=["% d'apparition", "Position moyenne", "Note moyenne"],
        aggfunc="mean",
    ).round(2)
    pivot.columns = [f"{v} | {k}" for v, k in pivot.columns]
    pivot = pivot.reset_index().sort_values(f"% d'apparition | {sel_mots[0]}" if sel_mots else pivot.columns[1], ascending=False)

    def highlight_human(row):
        style = [""] * len(row)
        if "human" in str(row.iloc[0]).lower():
            style = ["background-color: #0a2a3f; color: #00d4ff; font-weight: 700"] * len(row)
        return style

    st.dataframe(
        pivot.style.apply(highlight_human, axis=1).format(precision=1),
        use_container_width=True,
        height=350,
    )

    # ── Détail par mot-clé
    st.markdown('<div class="section-hdr">Détail par mot-clé</div>', unsafe_allow_html=True)
    for mk in sel_mots:
        df_mk = gen_f[gen_f["Mot-clé"] == mk].sort_values("Position moyenne")
        with st.expander(f"🔑  {mk}", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                colors_mk = [COLORS["human"] if "human" in str(c).lower() else "#1e3a5f"
                             for c in df_mk["Concurrents"]]
                fig_mk = go.Figure(go.Bar(
                    x=df_mk["Concurrents"], y=df_mk["% d'apparition"],
                    marker_color=colors_mk,
                    text=df_mk["% d'apparition"].round(0).astype(int).astype(str) + "%",
                    textposition="outside",
                ))
                plotly_layout(fig_mk, height=280)
                fig_mk.update_layout(
                    title=dict(text="Visibilité", font_size=11),
                    xaxis=dict(tickangle=-30), yaxis_title=None,
                )
                st.plotly_chart(fig_mk, use_container_width=True)
            with c2:
                fig_sc = px.scatter(
                    df_mk, x="Position moyenne", y="Note moyenne",
                    size="Nb d'avis moyen", text="Concurrents",
                    color=df_mk["Concurrents"].apply(lambda x: "Human" if "human" in x.lower() else "Concurrent"),
                    color_discrete_map={"Human": COLORS["human"], "Concurrent": "#334d66"},
                    size_max=30,
                )
                fig_sc.update_traces(textposition="top center", textfont_size=9)
                plotly_layout(fig_sc, height=280)
                fig_sc.update_layout(
                    title=dict(text="Position vs Note", font_size=11),
                    xaxis=dict(autorange="reversed"),
                    showlegend=False,
                )
                st.plotly_chart(fig_sc, use_container_width=True)


# ══════════════════════════════════════════════
# TAB 3 – AGENCES
# ══════════════════════════════════════════════
with tab_ag:

    sub1, sub2, sub3 = st.tabs(["🏢  Classées", "⚠️  Non classées", "📋  Tableau complet"])

    # ── Classées
    with sub1:
        ag = (
            cl.groupby(["Business Id", "Nom de l'établissement", "dept", "dept_label"])
            .agg(
                pos_moy=("Position", "mean"),
                pos_min=("Position", "min"),
                notation=("Notation", lambda x: pd.to_numeric(x, errors="coerce").mean()),
                reviews=("reviews", "mean"),
                nb_cl=("Mot-clé", "nunique"),
                mots_cl=("Mot-clé", lambda x: ", ".join(sorted(x.unique()))),
            )
            .reset_index()
        )
        ag["score"] = ag.apply(
            lambda r: seo_score(r["pos_moy"], r["nb_cl"], total_mots, r["notation"]), axis=1
        )

        # KPIs
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Agences classées", len(ag))
        k2.metric("Couvrent 3 mots-clés", int((ag["nb_cl"] == 3).sum()))
        k3.metric("Score SEO > 70", int((ag["score"] >= 70).sum()))
        k4.metric("Note moy. réseau", f"{ag['notation'].mean():.2f} ⭐" if len(ag) else "–")

        st.markdown("")

        # Score SEO chart – top 30
        top30 = ag.nlargest(30, "score")
        fig_sc = px.bar(
            top30, x="Nom de l'établissement", y="score",
            color="score",
            color_continuous_scale=["#f87171", "#fbbf24", "#4ade80"],
            text="score",
            title="Score SEO Local – Top 30 agences",
        )
        fig_sc.update_traces(textposition="outside")
        plotly_layout(fig_sc, height=320)
        fig_sc.update_layout(
            coloraxis_showscale=False, xaxis=dict(tickangle=-40, tickfont_size=9),
            yaxis_title=None, xaxis_title=None,
        )
        st.plotly_chart(fig_sc, use_container_width=True)

        # Tableau agences classées
        st.markdown('<div class="section-hdr">Détail agences classées</div>', unsafe_allow_html=True)
        display = ag[["Nom de l'établissement","dept","dept_label","pos_moy","pos_min","notation","reviews","nb_cl","mots_cl","score"]].copy()
        display.columns = ["Agence","Dept","Département","Pos. moy.","Meill. pos.","Note","Avis moy.","Nb mots-clés","Mots-clés couverts","Score SEO"]
        display["Pos. moy."] = display["Pos. moy."].round(1)
        display["Note"] = display["Note"].round(2)
        display["Avis moy."] = display["Avis moy."].round(0)
        def color_score(val):
            if pd.isna(val): return ""
            color = "#1a3d1a" if val >= 70 else ("#3d3300" if val >= 40 else "#3d1a1a")
            return f"background-color: {color}"

        def color_pos(val):
            if pd.isna(val): return ""
            color = "#1a3d1a" if val <= 3 else ("#3d3300" if val <= 10 else "#3d1a1a")
            return f"background-color: {color}"

        st.dataframe(
            display.sort_values("Score SEO", ascending=False)
            .style.applymap(color_score, subset=["Score SEO"])
                  .applymap(color_pos, subset=["Pos. moy."]),
            use_container_width=True,
            height=420,
        )
        # Export
        csv = display.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Export CSV – Agences classées", csv, "classees.csv", "text/csv")

    # ── Non classées
    with sub2:
        nc_ag = (
            nc.groupby(["Business Id", "Nom de l'établissement", "dept", "dept_label"])
            .agg(
                mots_nc=("Mot-clé", lambda x: ", ".join(sorted(x.unique()))),
                nb_nc=("Mot-clé", "nunique"),
            )
            .reset_index()
        )
        ids_cl = set(cl["Business Id"].unique())
        nc_ag["aussi_classee"] = nc_ag["Business Id"].isin(ids_cl)
        nc_ag["priorite"] = nc_ag.apply(
            lambda r: "🔴 Critique (aucun classement)" if not r["aussi_classee"] else "🟡 Gaps à combler", axis=1
        )

        k1, k2, k3 = st.columns(3)
        k1.metric("Agences non classées", len(nc_ag))
        k2.metric("🔴 Critique (0 classement)", int((~nc_ag["aussi_classee"]).sum()))
        k3.metric("🟡 Gaps partiels", int(nc_ag["aussi_classee"].sum()))

        st.markdown("")

        # Par département
        nc_dept = (
            nc_ag.groupby(["dept","dept_label"])
            .size().reset_index(name="count")
            .sort_values("count", ascending=False)
            .head(15)
        )
        nc_dept["label"] = nc_dept["dept"] + " – " + nc_dept["dept_label"].fillna("")
        fig_nc = px.bar(
            nc_dept, x="label", y="count",
            color="count", color_continuous_scale=["#fbbf24","#f87171"],
            text="count", title="Non classées par département (Top 15)",
        )
        fig_nc.update_traces(textposition="outside")
        plotly_layout(fig_nc, height=300)
        fig_nc.update_layout(coloraxis_showscale=False, xaxis=dict(tickangle=-30), xaxis_title=None, yaxis_title=None)
        st.plotly_chart(fig_nc, use_container_width=True)

        st.dataframe(
            nc_ag[["Nom de l'établissement","dept","dept_label","mots_nc","nb_nc","priorite"]]
            .rename(columns={"Nom de l'établissement":"Agence","dept":"Dept","dept_label":"Département",
                              "mots_nc":"Mots-clés manquants","nb_nc":"Nb gaps","priorite":"Priorité"})
            .sort_values(["Priorité","Nb gaps"], ascending=[True,False]),
            use_container_width=True,
            height=380,
        )
        csv_nc = nc_ag.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Export CSV – Non classées", csv_nc, "non_classees.csv", "text/csv")

    # ── Tableau complet
    with sub3:
        search = st.text_input("🔍 Rechercher une agence")
        type_sel = st.selectbox("Filtre type", ["Toutes","Classée","Non classée"])

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
# TAB 4 – PLANS D'ACTION
# ══════════════════════════════════════════════
with tab_plan:

    # Construire les plans
    ag_map: dict = {}
    for _, row in cl.iterrows():
        bid = row["Business Id"]
        if bid not in ag_map:
            ag_map[bid] = {
                "nom": row["Nom de l'établissement"],
                "dept": row["dept"], "dept_label": row["dept_label"],
                "positions": [], "notes": [], "reviews": [], "mots_cl": set(), "mots_nc": set(),
            }
        ag_map[bid]["positions"].append(row["Position"])
        ag_map[bid]["mots_cl"].add(row["Mot-clé"])
        if pd.notna(row["Notation"]): ag_map[bid]["notes"].append(float(row["Notation"]))
        if pd.notna(row["reviews"]): ag_map[bid]["reviews"].append(float(row["reviews"]))

    for _, row in nc.iterrows():
        bid = row["Business Id"]
        if bid not in ag_map:
            ag_map[bid] = {
                "nom": row["Nom de l'établissement"],
                "dept": row["dept"], "dept_label": row["dept_label"],
                "positions": [], "notes": [], "reviews": [], "mots_cl": set(), "mots_nc": set(),
            }
        ag_map[bid]["mots_nc"].add(row["Mot-clé"])

    plans = []
    for bid, a in ag_map.items():
        pos_moy = sum(a["positions"]) / len(a["positions"]) if a["positions"] else None
        note_moy = sum(a["notes"]) / len(a["notes"]) if a["notes"] else None
        rev_moy = sum(a["reviews"]) / len(a["reviews"]) if a["reviews"] else None
        nb_cl = len(a["mots_cl"])
        nb_nc = len(a["mots_nc"])
        score = seo_score(pos_moy, nb_cl, total_mots, note_moy) if pos_moy else 0
        priorite = get_priorite(pos_moy, nb_nc, note_moy)

        actions = []
        if pos_moy is None:
            actions.append("Activer / créer la fiche Google Business Profile pour tous les mots-clés cibles")
        elif pos_moy > 10:
            actions.append("Optimiser fiche GBP : catégories, photos, description locale, services")
        elif pos_moy > 5:
            actions.append("Renforcer signaux locaux : posts GBP réguliers, Q&A, attributs")
        if nb_nc > 0:
            actions.append(f"Combler les gaps sur : {', '.join(sorted(a['mots_nc']))} — vérifier cohérence catégories GBP")
        if note_moy and not pd.isna(note_moy):
            if note_moy < 4.0:
                actions.append(f"Note critique ({note_moy:.2f}) — répondre aux avis négatifs + processus de collecte")
            elif note_moy < 4.3:
                actions.append(f"Note à améliorer ({note_moy:.2f}) — encourager les clients satisfaits à laisser un avis")
        if rev_moy and rev_moy < 30:
            actions.append(f"Volume d'avis très faible ({rev_moy:.0f}) — lancer une campagne de sollicitation")
        if not actions:
            actions.append("Maintenir les bonnes pratiques — surveiller la concurrence locale")

        plans.append({
            "id": bid, "nom": a["nom"], "dept": a["dept"], "dept_label": a["dept_label"],
            "pos_moy": round(pos_moy, 1) if pos_moy else None,
            "note_moy": round(note_moy, 2) if note_moy else None,
            "rev_moy": round(rev_moy) if rev_moy else None,
            "nb_cl": nb_cl, "nb_nc": nb_nc, "score": score,
            "priorite": priorite, "actions": actions,
            "mots_cl": sorted(a["mots_cl"]), "mots_nc": sorted(a["mots_nc"]),
        })

    plans.sort(key=lambda x: ({"🔴 Urgent": 0, "🟡 Important": 1, "🟢 Opportunité": 2}.get(x["priorite"], 3), -x["score"]))

    counts = {p: sum(1 for x in plans if x["priorite"] == p) for p in ["🔴 Urgent", "🟡 Important", "🟢 Opportunité"]}

    # KPIs
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Total agences analysées", len(plans))
    p2.metric("🔴 Urgent", counts.get("🔴 Urgent", 0))
    p3.metric("🟡 Important", counts.get("🟡 Important", 0))
    p4.metric("🟢 Opportunité", counts.get("🟢 Opportunité", 0))

    st.markdown("")

    # Filtre priorité
    col_pf, col_search, col_exp = st.columns([3, 4, 2])
    with col_pf:
        prio_sel = st.selectbox("Priorité", ["Toutes", "🔴 Urgent", "🟡 Important", "🟢 Opportunité"])
    with col_search:
        search_plan = st.text_input("🔍 Rechercher une agence", key="plan_search")
    with col_exp:
        st.markdown("<br>", unsafe_allow_html=True)
        export_plan = st.button("⬇️ Export CSV", key="export_plan")

    visible = plans
    if prio_sel != "Toutes":
        visible = [p for p in visible if p["priorite"] == prio_sel]
    if search_plan:
        visible = [p for p in visible if search_plan.lower() in p["nom"].lower()]

    st.caption(f"{len(visible)} agence(s) affichée(s)")

    # Affichage plans
    for plan in visible:
        prio_color = {"🔴 Urgent": "#f87171", "🟡 Important": "#fbbf24", "🟢 Opportunité": "#4ade80"}.get(plan["priorite"], "#8bafc8")
        score_color = "#4ade80" if plan["score"] >= 70 else ("#fbbf24" if plan["score"] >= 40 else "#f87171")
        pos_color = "#4ade80" if (plan["pos_moy"] and plan["pos_moy"] <= 3) else ("#fbbf24" if (plan["pos_moy"] and plan["pos_moy"] <= 10) else "#f87171")

        with st.expander(f"{plan['priorite']}  {plan['nom']}  ·  {plan['dept']} {plan['dept_label'] or ''}"):
            col_kpi, col_act = st.columns([1, 2])

            with col_kpi:
                st.markdown(f"""
                <div style='display:grid;grid-template-columns:1fr 1fr;gap:8px;'>
                  <div style='background:#060e1a;border:1px solid #0d2035;border-radius:6px;padding:10px;'>
                    <div style='font-family:DM Mono,monospace;font-size:9px;color:#2a5a7a;text-transform:uppercase;letter-spacing:.12em;'>Score SEO</div>
                    <div style='font-size:1.6rem;font-weight:700;color:{score_color};'>{plan['score']}</div>
                  </div>
                  <div style='background:#060e1a;border:1px solid #0d2035;border-radius:6px;padding:10px;'>
                    <div style='font-family:DM Mono,monospace;font-size:9px;color:#2a5a7a;text-transform:uppercase;letter-spacing:.12em;'>Position</div>
                    <div style='font-size:1.6rem;font-weight:700;color:{pos_color};'>{plan['pos_moy'] or '–'}</div>
                  </div>
                  <div style='background:#060e1a;border:1px solid #0d2035;border-radius:6px;padding:10px;'>
                    <div style='font-family:DM Mono,monospace;font-size:9px;color:#2a5a7a;text-transform:uppercase;letter-spacing:.12em;'>Note</div>
                    <div style='font-size:1.6rem;font-weight:700;color:#00d4ff;'>{plan['note_moy'] or '–'}</div>
                  </div>
                  <div style='background:#060e1a;border:1px solid #0d2035;border-radius:6px;padding:10px;'>
                    <div style='font-family:DM Mono,monospace;font-size:9px;color:#2a5a7a;text-transform:uppercase;letter-spacing:.12em;'>Avis</div>
                    <div style='font-size:1.6rem;font-weight:700;color:#00d4ff;'>{plan['rev_moy'] or '–'}</div>
                  </div>
                </div>
                <div style='margin-top:10px;'>
                  <div style='font-family:DM Mono,monospace;font-size:9px;color:#2a5a7a;text-transform:uppercase;letter-spacing:.12em;margin-bottom:6px;'>Couverture mots-clés</div>
                """, unsafe_allow_html=True)
                for mk in data["mots_cles"]:
                    ok = mk in plan["mots_cl"]
                    missing = mk in plan["mots_nc"]
                    icon = "✓" if ok else ("✗" if missing else "–")
                    color = "#4ade80" if ok else ("#f87171" if missing else "#2a5a7a")
                    st.markdown(f"<span style='font-family:DM Mono,monospace;font-size:11px;color:{color};'>{icon} {mk}</span>", unsafe_allow_html=True)

            with col_act:
                st.markdown("""
                <div style='font-family:DM Mono,monospace;font-size:9px;color:#2a5a7a;text-transform:uppercase;letter-spacing:.12em;margin-bottom:8px;'>
                  Actions recommandées
                </div>
                """, unsafe_allow_html=True)
                for i, action in enumerate(plan["actions"], 1):
                    st.markdown(f"""
                    <div style='display:flex;gap:10px;margin-bottom:8px;padding:10px 12px;background:#060e1a;border:1px solid #0d2035;border-left:3px solid {prio_color};border-radius:4px;'>
                      <span style='font-family:DM Mono,monospace;font-size:10px;color:#2a5a7a;flex-shrink:0;'>{i}.</span>
                      <span style='font-size:12px;color:#8bafc8;'>{action}</span>
                    </div>
                    """, unsafe_allow_html=True)

    # Export CSV
    if export_plan:
        rows = []
        for p in visible:
            rows.append({
                "Agence": p["nom"], "Département": p["dept"], "Dept label": p["dept_label"],
                "Priorité": p["priorite"], "Score SEO": p["score"],
                "Position moy.": p["pos_moy"], "Note": p["note_moy"], "Avis": p["rev_moy"],
                "Mots-clés couverts": ", ".join(p["mots_cl"]),
                "Mots-clés manquants": ", ".join(p["mots_nc"]),
                "Actions": " | ".join(p["actions"]),
            })
        df_export = pd.DataFrame(rows)
        st.download_button(
            "📥 Télécharger le plan d'action",
            df_export.to_csv(index=False).encode("utf-8"),
            f"plan_action_seo_{data['periode'].replace(' ','_')}.csv",
            "text/csv",
        )
