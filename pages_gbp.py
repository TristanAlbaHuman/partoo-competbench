"""
Module GBP Intelligence — onglet séparé importé dans app.py
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json, re

COLORS = {
    "human": "#00d4ff", "top3": "#4ade80", "critique": "#f87171",
    "important": "#fbbf24", "stable": "#4ade80", "grid": "#0d2035", "text": "#8bafc8",
}
IMPACT_COLORS = {"Élevé": "#f87171", "Moyen": "#fbbf24", "Faible": "#4ade80"}
EFFORT_BG    = {"Faible": "#1a3d1a", "Moyen": "#3d3300", "Élevé": "#3d1a1a"}

PRIO_COLOR = {"🔴 Critique": "#f87171", "🟡 Important": "#fbbf24", "🟢 Stable": "#4ade80"}
PRIO_BG    = {"🔴 Critique": "#3d1a1a", "🟡 Important": "#3d3300", "🟢 Stable": "#1a3d1a"}

def plotly_dark(fig, height=300):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text"], family="DM Mono, monospace", size=10),
        height=height, margin=dict(t=30, b=20, l=10, r=10),
        xaxis=dict(gridcolor=COLORS["grid"], zeroline=False),
        yaxis=dict(gridcolor=COLORS["grid"], zeroline=False),
        showlegend=False,
    )
    return fig


def build_scorecard(data: dict) -> pd.DataFrame:
    """Construit le scorecard GBP depuis les données chargées."""
    df_det = data.get("_df_det")
    if df_det is None:
        return pd.DataFrame()

    df_det = df_det.copy()
    df_det["Notation"] = pd.to_numeric(df_det["Notation"], errors="coerce")
    df_human = df_det[df_det["Concurrents"].isna()].copy()
    df_conc  = df_det[df_det["Concurrents"].notna()].copy()

    human_kpi = (df_human
        .groupby(["Business Id", "Mot-clé"])
        .agg(pos_moy=("Position","mean"), pos_min=("Position","min"),
             note=("Notation","mean"), avis=("reviews","mean"))
        .reset_index())

    best_per_motcle = (df_conc[df_conc["Position"] <= 3]
        .groupby(["Concurrents","Mot-clé"])
        .agg(pos=("Position","mean"), note=("Notation","mean"), avis=("reviews","mean"))
        .reset_index().sort_values("pos")
        .groupby("Mot-clé").first().reset_index()
        .rename(columns={"Concurrents":"top_reseau","pos":"top_pos","note":"top_note","avis":"top_avis"}))

    merged = human_kpi.merge(best_per_motcle, on="Mot-clé", how="left")
    merged["pos_gap"]  = merged["pos_moy"] - merged["top_pos"]
    merged["avis_gap"] = merged["top_avis"] - merged["avis"]
    merged["note_gap"] = merged["top_note"] - merged["note"]

    def mode_safe(x):
        d = x.dropna(); return d.mode()[0] if len(d) > 0 else None

    # Nom ref
    ref = data.get("ref", pd.DataFrame())
    nom_map = dict(zip(ref["Business Id"], ref["nom"])) if len(ref) > 0 else {}
    dept_map = dict(zip(ref["Business Id"], ref["dept"])) if len(ref) > 0 else {}
    dept_label_map = dict(zip(ref["Business Id"], ref.get("dept_label", ref.get("dept","")))) if len(ref) > 0 else {}

    scorecard = (merged.groupby("Business Id")
        .agg(
            pos_moy=("pos_moy","mean"), pos_min=("pos_min","min"),
            note=("note","mean"), avis=("avis","mean"),
            nb_mots=("Mot-clé","nunique"),
            pos_gap_moy=("pos_gap","mean"), avis_gap_moy=("avis_gap","mean"), note_gap_moy=("note_gap","mean"),
            top_reseau=("top_reseau", mode_safe),
            top_pos=("top_pos","mean"), top_note=("top_note","mean"), top_avis=("top_avis","mean"),
            mots=("Mot-clé", list), pos_par_mot=("pos_moy", list),
        ).reset_index())

    scorecard["nom"] = scorecard["Business Id"].map(nom_map)
    scorecard["dept"] = scorecard["Business Id"].map(dept_map)
    scorecard["dept_label"] = scorecard["Business Id"].map(dept_label_map)

    def priorite(r):
        score = 0
        if r["pos_gap_moy"] > 10: score += 3
        elif r["pos_gap_moy"] > 5: score += 2
        elif r["pos_gap_moy"] > 0: score += 1
        if r["avis_gap_moy"] > 100: score += 3
        elif r["avis_gap_moy"] > 50: score += 2
        elif r["avis_gap_moy"] > 20: score += 1
        if pd.notna(r["note"]) and r["note"] < 4.0: score += 2
        elif pd.notna(r["note"]) and r["note"] < 4.3: score += 1
        if score >= 5: return "🔴 Critique"
        if score >= 3: return "🟡 Important"
        return "🟢 Stable"

    def actions_gbp(r):
        top = r["top_reseau"] if r["top_reseau"] else "meilleur concurrent"
        actions = []
        if pd.notna(r["avis_gap_moy"]) and r["avis_gap_moy"] > 100:
            actions.append({"icon":"💬","titre":"Volume d'avis critique",
                "action":f"Processus systématique de collecte post-transaction. Objectif +{int(min(r['avis_gap_moy'],150))} avis ({int(r['avis'])} actuels vs {int(r['top_avis'])} pour {top}).",
                "impact":"Élevé","effort":"Moyen"})
        elif pd.notna(r["avis_gap_moy"]) and r["avis_gap_moy"] > 30:
            actions.append({"icon":"💬","titre":"Augmenter les avis",
                "action":f"Solliciter par SMS/email post-visite. +{int(r['avis_gap_moy'])} avis à combler vs {top} ({int(r['avis'])} actuels).",
                "impact":"Élevé","effort":"Faible"})
        if pd.notna(r["pos_gap_moy"]) and r["pos_gap_moy"] > 8:
            actions.append({"icon":"📍","titre":"Refonte catégories GBP",
                "action":f"Revoir catégorie primaire (→ 'Agence immobilière'), ajouter 5+ catégories secondaires, vérifier NAP cohérent sur tous annuaires. Pos. {r['pos_moy']:.1f} vs {r['top_pos']:.1f} ({top}).",
                "impact":"Élevé","effort":"Faible"})
        elif pd.notna(r["pos_gap_moy"]) and r["pos_gap_moy"] > 3:
            actions.append({"icon":"🔧","titre":"Signaux locaux GBP",
                "action":f"2 posts/semaine min, répondre à tous les avis sous 48h, compléter services et attributs. Pos. {r['pos_moy']:.1f} vs {r['top_pos']:.1f} ({top}).",
                "impact":"Moyen","effort":"Faible"})
        if pd.notna(r["note"]) and r["note"] < 4.3:
            actions.append({"icon":"⭐","titre":"Gestion de la réputation",
                "action":f"Répondre à chaque avis < 4★ sous 48h avec solution concrète. Note actuelle {r['note']:.2f} (objectif 4.5+).",
                "impact":"Moyen","effort":"Moyen"})
        if pd.notna(r["pos_gap_moy"]) and r["pos_gap_moy"] > 0:
            actions.append({"icon":"📸","titre":"Enrichissement du profil",
                "action":"10+ photos récentes (façade, équipe, biens vendus), mise à jour horaires/téléphone, section Q&A complète.",
                "impact":"Moyen","effort":"Faible"})
        if not actions:
            actions.append({"icon":"✅","titre":"Maintenir la performance",
                "action":"Continuer la cadence actuelle. 1-2 posts GBP/semaine. Surveiller l'activité des concurrents locaux.",
                "impact":"Faible","effort":"Faible"})
        return actions

    scorecard["priorite"] = scorecard.apply(priorite, axis=1)
    scorecard["actions"] = scorecard.apply(actions_gbp, axis=1)
    return scorecard


def render_gbp_tab(data: dict, filtered: dict, sel_mots: list, sel_depts: list, sel_agences: list):
    """Render the full GBP Intelligence tab."""

    sc = build_scorecard(data)
    if len(sc) == 0:
        st.info("Données insuffisantes pour l'analyse GBP.")
        return

    # Apply filters
    if sel_depts:
        sc = sc[sc["dept"].isin(sel_depts)]
    if sel_agences:
        sc = sc[sc["nom"].isin(sel_agences)]

    n_crit   = (sc["priorite"] == "🔴 Critique").sum()
    n_imp    = (sc["priorite"] == "🟡 Important").sum()
    n_stable = (sc["priorite"] == "🟢 Stable").sum()

    # ── Section 1 : Benchmark concurrents
    st.markdown('<div class="section-hdr">⊕ Benchmark — Concurrents qui surclassent Human</div>', unsafe_allow_html=True)

    df_det = data.get("_df_det", pd.DataFrame())
    if len(df_det) > 0:
        df_det2 = df_det.copy()
        df_det2["Notation"] = pd.to_numeric(df_det2["Notation"], errors="coerce")
        df_conc = df_det2[df_det2["Concurrents"].notna()]
        top3 = df_conc[df_conc["Position"] <= 3]

        bench = (top3.groupby("Concurrents")
            .agg(nb_agences=("Nom de l'établissement","nunique"),
                 pos_moy=("Position","mean"),
                 note_moy=("Notation","mean"),
                 avis_moy=("reviews","mean"))
            .reset_index().sort_values("nb_agences", ascending=False))

        human_note = df_det2[df_det2["Concurrents"].isna()]["Notation"].mean()
        human_avis = df_det2[df_det2["Concurrents"].isna()]["reviews"].mean()

        col_bench, col_radar = st.columns([3, 2])

        with col_bench:
            # Tableau benchmark
            bench_display = bench.copy()
            bench_display["avis_gap"] = (bench_display["avis_moy"] - human_avis).round(0).astype(int)
            bench_display["note_gap"] = (bench_display["note_moy"] - human_note).round(2)
            bench_display.columns = ["Réseau","Agences Top3","Pos. moy.","Note","Avis moy.","Δ Avis vs Human","Δ Note vs Human"]

            def color_avis_gap(val):
                if val > 80: return "color: #f87171; font-weight: 700"
                if val > 30: return "color: #fbbf24"
                return "color: #4ade80"
            def color_note_gap(val):
                if val > 0.1: return "color: #f87171"
                return "color: #4ade80"

            st.dataframe(
                bench_display.style
                    .applymap(color_avis_gap, subset=["Δ Avis vs Human"])
                    .applymap(color_note_gap, subset=["Δ Note vs Human"])
                    .format({"Pos. moy.": "{:.1f}", "Note": "{:.2f}", "Avis moy.": "{:.0f}"}),
                use_container_width=True, height=340
            )

        with col_radar:
            # Insight clé
            st.markdown("""
            <div style='background:#060e1a;border:1px solid #0d2035;border-left:4px solid #00d4ff;
                        border-radius:6px;padding:14px 16px;margin-bottom:10px;'>
              <div style='font-family:DM Mono,monospace;font-size:9px;color:#2a5a7a;text-transform:uppercase;margin-bottom:8px;'>Insight principal</div>
              <div style='font-size:13px;color:#e8edf2;font-weight:600;'>Note Human ✅ Compétitive</div>
              <div style='font-size:11px;color:#8bafc8;margin-top:4px;'>La note n'est pas le problème. Le volume d'avis est le levier #1.</div>
            </div>
            """, unsafe_allow_html=True)

            # Avis gap chart
            fig_avis = go.Figure()
            fig_avis.add_trace(go.Bar(
                x=["Human"] + bench["Concurrents"].tolist(),
                y=[human_avis] + bench["avis_moy"].tolist(),
                marker_color=[COLORS["human"]] + ["#1e3a5f"] * len(bench),
                text=[f"{human_avis:.0f}"] + [f"{v:.0f}" for v in bench["avis_moy"]],
                textposition="outside",
            ))
            plotly_dark(fig_avis, 240)
            fig_avis.update_layout(title=dict(text="Avis moyens (Top 3)", font_size=11),
                                   xaxis=dict(tickangle=-30), yaxis_title=None)
            st.plotly_chart(fig_avis, use_container_width=True)

    st.divider()

    # ── Section 2 : KPIs priorité
    st.markdown('<div class="section-hdr">◈ Diagnostic — Scorecard par agence</div>', unsafe_allow_html=True)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Agences analysées", len(sc))
    k2.metric("🔴 Critique", n_crit)
    k3.metric("🟡 Important", n_imp)
    k4.metric("🟢 Stable", n_stable)

    st.markdown("")

    # ── Filtres inline
    fc1, fc2, fc3 = st.columns([2, 3, 2])
    with fc1:
        prio_filter = st.multiselect("Priorité", ["🔴 Critique","🟡 Important","🟢 Stable"],
                                     default=["🔴 Critique","🟡 Important"], key="gbp_prio")
    with fc2:
        search_gbp = st.text_input("🔍 Rechercher une agence", key="gbp_search")
    with fc3:
        sort_by = st.selectbox("Trier par", ["Priorité + avis gap","Position gap","Volume avis gap","Note"], key="gbp_sort")

    sc_filtered = sc[sc["priorite"].isin(prio_filter)] if prio_filter else sc
    if search_gbp:
        sc_filtered = sc_filtered[sc_filtered["nom"].str.contains(search_gbp, case=False, na=False)]

    if sort_by == "Position gap":
        sc_filtered = sc_filtered.sort_values("pos_gap_moy", ascending=False)
    elif sort_by == "Volume avis gap":
        sc_filtered = sc_filtered.sort_values("avis_gap_moy", ascending=False)
    elif sort_by == "Note":
        sc_filtered = sc_filtered.sort_values("note")
    else:
        prio_ord = {"🔴 Critique": 0, "🟡 Important": 1, "🟢 Stable": 2}
        sc_filtered = sc_filtered.assign(_pord=sc_filtered["priorite"].map(prio_ord))
        sc_filtered = sc_filtered.sort_values(["_pord","avis_gap_moy"], ascending=[True,False]).drop("_pord",axis=1)

    st.caption(f"{len(sc_filtered)} agence(s) affichée(s)")

    # ── Scorecards
    for _, row in sc_filtered.iterrows():
        prio = row["priorite"]
        pc = PRIO_COLOR.get(prio, "#8bafc8")
        pb = PRIO_BG.get(prio, "#060e1a")
        top = row["top_reseau"] or "concurrent"
        pos_g = row["pos_gap_moy"]
        avis_g = row["avis_gap_moy"]

        # Résumé 1 ligne (toujours visible)
        col_h1, col_h2, col_h3, col_h4, col_h5, col_expand = st.columns([4,1,1,1,2,1])
        with col_h1:
            st.markdown(f"""
            <div style='display:flex;align-items:center;gap:8px;padding:8px 0;'>
              <div style='width:10px;height:10px;border-radius:50%;background:{pc};flex-shrink:0;'></div>
              <div>
                <div style='font-size:13px;font-weight:600;color:#e8edf2;'>{row['nom']}</div>
                <div style='font-size:10px;color:#2a5a7a;font-family:DM Mono,monospace;'>{row.get('dept','')}&nbsp;{row.get('dept_label','')}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)
        col_h2.metric("Pos.", f"{row['pos_moy']:.1f}")
        col_h3.metric("Note", f"{row['note']:.2f}" if pd.notna(row['note']) else "–")
        col_h4.metric("Avis", f"{int(row['avis'])}" if pd.notna(row['avis']) else "–")
        with col_h5:
            # Action principale en 1 ligne
            if pd.notna(avis_g) and avis_g > 50:
                st.markdown(f"<div style='font-size:11px;color:#fbbf24;padding:8px 0;'>💬 +{int(avis_g)} avis vs {top}</div>", unsafe_allow_html=True)
            elif pd.notna(pos_g) and pos_g > 5:
                st.markdown(f"<div style='font-size:11px;color:#f87171;padding:8px 0;'>📍 Pos. {row['pos_moy']:.0f} vs {row['top_pos']:.0f} ({top})</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='font-size:11px;color:#4ade80;padding:8px 0;'>✅ Performance OK</div>", unsafe_allow_html=True)

        # Scorecard détaillé dans expander
        with st.expander("Voir la fiche complète →", expanded=False):
            c_left, c_mid, c_right = st.columns([2, 2, 3])

            with c_left:
                st.markdown(f"""
                <div style='font-family:DM Mono,monospace;font-size:9px;color:#2a5a7a;text-transform:uppercase;margin-bottom:8px;'>Métriques Human</div>
                <div style='display:grid;grid-template-columns:1fr 1fr;gap:6px;'>
                  <div style='background:#060e1a;border:1px solid #0d2035;border-radius:6px;padding:10px;text-align:center;'>
                    <div style='font-size:1.4rem;font-weight:700;color:{"#f87171" if pd.notna(row["pos_moy"]) and row["pos_moy"]>10 else "#fbbf24" if pd.notna(row["pos_moy"]) and row["pos_moy"]>5 else "#4ade80"};'>{row['pos_moy']:.1f}</div>
                    <div style='font-size:9px;color:#2a5a7a;font-family:DM Mono,monospace;'>Position moy.</div>
                  </div>
                  <div style='background:#060e1a;border:1px solid #0d2035;border-radius:6px;padding:10px;text-align:center;'>
                    <div style='font-size:1.4rem;font-weight:700;color:#00d4ff;'>{row['note']:.2f}</div>
                    <div style='font-size:9px;color:#2a5a7a;font-family:DM Mono,monospace;'>Note ⭐</div>
                  </div>
                  <div style='background:#060e1a;border:1px solid #0d2035;border-radius:6px;padding:10px;text-align:center;'>
                    <div style='font-size:1.4rem;font-weight:700;color:{"#f87171" if pd.notna(row["avis"]) and row["avis"]<80 else "#fbbf24" if pd.notna(row["avis"]) and row["avis"]<130 else "#4ade80"};'>{int(row['avis']) if pd.notna(row['avis']) else "–"}</div>
                    <div style='font-size:9px;color:#2a5a7a;font-family:DM Mono,monospace;'>Avis</div>
                  </div>
                  <div style='background:#060e1a;border:1px solid #0d2035;border-radius:6px;padding:10px;text-align:center;'>
                    <div style='font-size:1.4rem;font-weight:700;color:#8bafc8;'>{int(row['nb_mots'])}</div>
                    <div style='font-size:9px;color:#2a5a7a;font-family:DM Mono,monospace;'>Mots-clés</div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

            with c_mid:
                st.markdown(f"""
                <div style='font-family:DM Mono,monospace;font-size:9px;color:#2a5a7a;text-transform:uppercase;margin-bottom:8px;'>vs {top.upper()} (Top 3)</div>
                <div style='display:grid;grid-template-columns:1fr 1fr;gap:6px;'>
                  <div style='background:#060e1a;border:1px solid #0d2035;border-radius:6px;padding:10px;text-align:center;'>
                    <div style='font-size:1.4rem;font-weight:700;color:#4ade80;'>{row['top_pos']:.1f}</div>
                    <div style='font-size:9px;color:#2a5a7a;font-family:DM Mono,monospace;'>Pos. concurrent</div>
                  </div>
                  <div style='background:#060e1a;border:1px solid #0d2035;border-radius:6px;padding:10px;text-align:center;'>
                    <div style='font-size:1.4rem;font-weight:700;color:#8bafc8;'>{row['top_note']:.2f}</div>
                    <div style='font-size:9px;color:#2a5a7a;font-family:DM Mono,monospace;'>Note concurrent</div>
                  </div>
                  <div style='background:#060e1a;border:1px solid #0d2035;border-radius:6px;padding:10px;text-align:center;'>
                    <div style='font-size:1.4rem;font-weight:700;color:#8bafc8;'>{int(row['top_avis']) if pd.notna(row['top_avis']) else "–"}</div>
                    <div style='font-size:9px;color:#2a5a7a;font-family:DM Mono,monospace;'>Avis concurrent</div>
                  </div>
                  <div style='background:{PRIO_BG.get(prio,"#060e1a")};border:1px solid #0d2035;border-radius:6px;padding:10px;text-align:center;'>
                    <div style='font-size:1rem;font-weight:700;color:{pc};'>{prio}</div>
                    <div style='font-size:9px;color:#2a5a7a;font-family:DM Mono,monospace;'>Priorité</div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

            with c_right:
                st.markdown('<div style="font-family:DM Mono,monospace;font-size:9px;color:#2a5a7a;text-transform:uppercase;margin-bottom:8px;">Actions GBP recommandées</div>', unsafe_allow_html=True)
                for i, action in enumerate(row["actions"], 1):
                    impact_c = IMPACT_COLORS.get(action["impact"], "#8bafc8")
                    effort_bg = EFFORT_BG.get(action["effort"], "#060e1a")
                    st.markdown(f"""
                    <div style='background:#060e1a;border:1px solid #0d2035;border-left:3px solid {pc};
                                border-radius:4px;padding:10px 12px;margin-bottom:6px;'>
                      <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;'>
                        <div style='font-size:12px;font-weight:600;color:#e8edf2;'>{action["icon"]} {action["titre"]}</div>
                        <div style='display:flex;gap:4px;'>
                          <span style='font-size:9px;font-family:DM Mono,monospace;padding:2px 6px;background:{effort_bg};color:{impact_c};border-radius:3px;'>Impact {action["impact"]}</span>
                          <span style='font-size:9px;font-family:DM Mono,monospace;padding:2px 6px;background:#0d1f2d;color:#4a7a9b;border-radius:3px;'>Effort {action["effort"]}</span>
                        </div>
                      </div>
                      <div style='font-size:11px;color:#8bafc8;line-height:1.4;'>{action["action"]}</div>
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown('<hr style="border:0;border-top:1px solid #0d2035;margin:4px 0;">', unsafe_allow_html=True)

    # ── Export CSV
    st.markdown("")
    export_rows = []
    for _, r in sc.iterrows():
        for i, a in enumerate(r["actions"], 1):
            export_rows.append({
                "Agence": r["nom"], "Département": r.get("dept",""), "Priorité": r["priorite"],
                "Position moy.": round(r["pos_moy"],1), "Note": round(r["note"],2) if pd.notna(r["note"]) else "",
                "Avis": int(r["avis"]) if pd.notna(r["avis"]) else "",
                "Top concurrent": r["top_reseau"] or "", "Pos. concurrent": round(r["top_pos"],1) if pd.notna(r["top_pos"]) else "",
                "Avis concurrent": int(r["top_avis"]) if pd.notna(r["top_avis"]) else "",
                f"Action {i} — Titre": a["titre"], f"Action {i} — Détail": a["action"],
                f"Action {i} — Impact": a["impact"], f"Action {i} — Effort": a["effort"],
            })
    df_export = pd.DataFrame(export_rows)
    csv = df_export.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Exporter les plans d'action GBP (CSV équipes terrain)", csv,
                       "plans_action_gbp.csv", "text/csv", use_container_width=True)
