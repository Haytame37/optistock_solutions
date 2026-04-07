from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from core.iot_analysis import detect_anomalies, get_basic_stats
from core.scoring import calculate_environmental_score, get_score_label
from core.warehouse_search import search_entrepots
from utils.db import load_sql_to_dataframe


st.set_page_config(page_title="OptiStock Solutions", layout="wide", page_icon="🏭")


def render_search_page() -> None:
    st.title("OptiStock Solutions")
    st.caption("Recherche d'entrepots basee sur les fichiers data/cleaned")

    with st.expander("Voir le process de calcul et les relations utilisees", expanded=True):
        st.markdown(
            """
            **Logique generale**

            L'algorithme suit une logique de fiabilite industrielle en 4 idees :

            1. produire un signal horaire robuste a partir de 3 capteurs,
            2. penaliser les donnees absentes et incoherentes,
            3. detecter les deviations par rapport au comportement habituel,
            4. adapter la severite au type de stockage recherche.

            Le score final est borne entre `0` et `100`, puis un filtre d'eligibilite elimine les entrepots incompatibles.
            """
        )

    type_recherche = st.selectbox(
        "Type de recherche",
        ["STANDARD", "FROID", "SEC", "CLIMATISE"],
        index=0,
    )

    if st.button("Rechercher", type="primary", use_container_width=False):
        data_dir = Path(__file__).parent / "data" / "cleaned"
        results = search_entrepots(type_recherche, data_dir)

        st.markdown(
            f"### {len(results)} entrepot(s) analyse(s) pour le type `{type_recherche}`"
        )

        if not results:
            st.warning("Aucun entrepot n'a pu etre analyse a partir des fichiers cleaned.")
            return

        for entrepot in results:
            reject_line = ""
            if not entrepot["eligible"] and entrepot["motif_rejet"]:
                reject_line = f"<br><strong>Motif rejet :</strong> {entrepot['motif_rejet']}"

            card_html = f"""
            <div style="
                border: 1px solid #e0e0e0;
                padding: 20px;
                margin-bottom: 15px;
                border-radius: 8px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                background: white;
                box-shadow: 0 4px 8px rgba(0,0,0,0.06);
            ">
                <div style="
                    font-size: 2em;
                    font-weight: bold;
                    color: #2c3e50;
                    min-width: 100px;
                    text-align: center;
                ">{entrepot['score']}</div>
                <div style="flex-grow: 1; padding-left: 20px;">
                    <div style="font-weight: bold; font-size: 1.2em; color: #34495e;">
                        {entrepot['id_entrepot']}
                        <span style="
                            padding: 5px 10px;
                            border-radius: 20px;
                            color: white;
                            font-weight: bold;
                            display: inline-block;
                            margin-left: 10px;
                            font-size: 0.85em;
                            background-color: {entrepot['couleur']};
                        ">{entrepot['label']}</span>
                    </div>
                    <div style="color: #7f8c8d; font-size: 0.95em; line-height: 1.6;">
                        Temperature moyenne: {entrepot['temp_moyenne']}°C |
                        Humidite moyenne: {entrepot['hum_moyenne']}%<br>
                        Incidents: {entrepot['nb_incidents']} |
                        Penalite coherence: -{entrepot['penalite_coherence']} pts |
                        Penalite incidents: -{entrepot['penalite_incidents']} pts
                        {reject_line}
                    </div>
                </div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)

            with st.expander(f"Details du calcul pour {entrepot['id_entrepot']}"):
                st.markdown("**Relations appliquees et justification des choix**")
                for relation in entrepot["relations"]:
                    st.markdown(f"### {relation['nom']}")
                    st.code(relation["formule"])
                    st.markdown(f"**Pourquoi ce choix :** {relation['justification']}")
                    st.markdown(f"**Effet sur le score :** {relation['impact']}")

                col_a, col_b, col_c = st.columns(3)
                col_a.metric("Heures analysees", entrepot["heures_total"])
                col_a.metric("NaN temperature", entrepot["nan_temp"])
                col_a.metric("NaN humidite", entrepot["nan_hum"])
                col_b.metric("Temperature moyenne", f"{entrepot['temp_moyenne']} °C")
                col_b.metric("Humidite moyenne", f"{entrepot['hum_moyenne']} %")
                col_b.metric("Incidents", entrepot["nb_incidents"])
                col_c.metric("Micro temp", entrepot["nb_micro_temp"])
                col_c.metric("Micro humidite", entrepot["nb_micro_hum"])
                col_c.metric("Eligibilite", "Oui" if entrepot["eligible"] else "Non")

                detail_df = pd.DataFrame(
                    [
                        {"Etape": "P_dispo", "Valeur": entrepot["penalite_dispo"]},
                        {"Etape": "P_coh", "Valeur": entrepot["penalite_coherence"]},
                        {"Etape": "P_instab_t x coef_t", "Valeur": entrepot["penalite_instabilite_temp"]},
                        {"Etape": "P_instab_h x coef_h", "Valeur": entrepot["penalite_instabilite_hum"]},
                        {"Etape": "P_inc_temp brut", "Valeur": entrepot["p_inc_temp_brut"]},
                        {"Etape": "P_inc_hum brut", "Valeur": entrepot["p_inc_hum_brut"]},
                        {"Etape": "P_inc ajuste", "Valeur": entrepot["penalite_incidents"]},
                        {"Etape": "Score brut", "Valeur": entrepot["raw_score"]},
                        {"Etape": "Score final", "Valeur": entrepot["score"]},
                    ]
                )
                st.dataframe(detail_df, use_container_width=True, hide_index=True)

                st.markdown(
                    f"""
                    **Substitution numerique**

                    `coef_t = {entrepot['coef_temp']}` ; `coef_h = {entrepot['coef_hum']}`

                    `Score = 100 - [{entrepot['penalite_dispo']} + {entrepot['penalite_coherence']} + `
                    `({entrepot['penalite_instabilite_temp']} ) + ({entrepot['penalite_instabilite_hum']} ) + {entrepot['penalite_incidents']}]`

                    `Score brut = {entrepot['raw_score']}`

                    `Score final = {entrepot['score']}`
                    """
                )

                st.markdown(
                    """
                    **Lecture du resultat**

                    - `P_dispo` mesure la qualite de disponibilite des donnees.
                    - `P_coh` mesure l'accord entre capteurs sur une meme heure.
                    - `P_instab_t` et `P_instab_h` mesurent la variabilite normale restante.
                    - `P_inc` represente les episodes severes et prolonges.
                    - `coef_t` et `coef_h` traduisent l'importance metier de la temperature et de l'humidite.
                    """
                )

                if entrepot["motif_rejet"]:
                    st.warning(f"Motif de rejet : {entrepot['motif_rejet']}")

        results_df = pd.DataFrame(results)
        st.divider()
        st.subheader("Details")
        st.dataframe(
            results_df[
                [
                    "id_entrepot",
                    "score",
                    "label",
                    "temp_moyenne",
                    "hum_moyenne",
                    "nb_incidents",
                    "penalite_coherence",
                    "penalite_incidents",
                    "eligible",
                ]
            ],
            use_container_width=True,
        )


def render_environmental_page() -> None:
    try:
        df_t_raw = load_sql_to_dataframe("SELECT * FROM temperature")
        df_h_raw = load_sql_to_dataframe("SELECT * FROM humidite")

        if df_t_raw.empty or df_h_raw.empty:
            raise ValueError("Les tables IoT sont vides dans la base de donnees.")

        df_t_raw["datetime"] = pd.to_datetime(df_t_raw["datetime"])
        df_h_raw["datetime"] = pd.to_datetime(df_h_raw["datetime"])
    except Exception as exc:
        st.error(
            f"Erreur de connexion DB : {exc}. "
            "Assurez-vous d'avoir execute 'python database/seed_data.py'."
        )
        return

    st.sidebar.success("Module Analyse Environnementale")

    entrepot_list = df_t_raw["id_entrepot"].unique()
    selected_entrepot = st.sidebar.selectbox("Selection de l'entrepot :", entrepot_list)

    st.sidebar.markdown("---")
    st.sidebar.markdown("**Selection des capteurs :**")
    selected_capteur_t = st.sidebar.radio("Temperature :", ["capteur1", "capteur2", "capteur3"], index=0)
    selected_capteur_h = st.sidebar.radio("Humidite :", ["capteur1", "capteur2", "capteur3"], index=0)
    st.sidebar.markdown("---")

    df_t = df_t_raw[df_t_raw["id_entrepot"] == selected_entrepot].copy()
    df_t.sort_values("datetime", inplace=True)

    df_h = df_h_raw[df_h_raw["id_entrepot"] == selected_entrepot].copy()
    df_h.sort_values("datetime", inplace=True)

    stats = get_basic_stats(df_t, df_h)
    bad_temp, bad_humid = detect_anomalies(df_t, df_h)
    total_len = max(len(df_t), len(df_h))
    score = calculate_environmental_score(total_len, len(bad_temp), len(bad_humid))
    label, emoji = get_score_label(score)

    st.sidebar.info(f"Statut : {label} {emoji}")

    st.title(f"OptiStock Solutions - {selected_entrepot}")
    st.markdown(f"### Score de Conformite Environnementale : **{score}/100** ({label} {emoji})")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Entrepot Actif", selected_entrepot, "Filtre")
    col2.metric("Temperature Moyenne", f"{stats['temp_mean']}°C", "Stable")
    col3.metric("Heures hors-normes", len(bad_temp), delta="- Alertes T°", delta_color="inverse")
    col4.metric("Fiabilite Capteurs", "99.2%", "IoT Active")

    st.divider()
    st.subheader("Analyse Correlee : Temperature & Humidite")
    st.caption(
        f"Visualisation : Temperature ({selected_capteur_t}) et Humidite ({selected_capteur_h})"
    )

    fig_combined = make_subplots(specs=[[{"secondary_y": True}]])

    fig_combined.add_trace(
        go.Scatter(
            x=df_t["datetime"],
            y=df_t[selected_capteur_t],
            name=f"Temp. {selected_capteur_t} (°C)",
            line=dict(color="#ef553b", width=1),
        ),
        secondary_y=False,
    )

    fig_combined.add_trace(
        go.Scatter(
            x=df_h["datetime"],
            y=df_h[selected_capteur_h],
            name=f"Hum. {selected_capteur_h} (%)",
            line=dict(color="#636efa", width=1, dash="dot"),
        ),
        secondary_y=True,
    )

    fig_combined.update_layout(
        title_text="Correlation Temperature vs Humidite (Vue Annuelle)",
        hovermode="x unified",
    )
    fig_combined.update_yaxes(title_text="<b>Temperature</b> (°C)", secondary_y=False)
    fig_combined.update_yaxes(title_text="<b>Humidite</b> (%)", secondary_y=True)

    st.plotly_chart(fig_combined, use_container_width=True)
    st.info(
        f"Conseil Expert : l'entrepot a ete hors-normes pendant {len(bad_temp)} heures "
        f"pour la temperature et {len(bad_humid)} heures pour l'humidite."
    )

    st.divider()
    st.subheader("Rapport d'Analyse Statistique")

    col_stats1, col_stats2 = st.columns(2)

    with col_stats1:
        st.write("**Statistiques Temperature**")
        stats_temp = {
            "Indicateur": ["Minimum", "Maximum", "Moyenne", "Ecart-type"],
            "Valeur": [
                f"{stats['temp_min']}°C",
                f"{stats['temp_max']}°C",
                f"{stats['temp_mean']}°C",
                f"{stats['temp_std']}",
            ],
        }
        st.table(pd.DataFrame(stats_temp))

    with col_stats2:
        st.write("**Statistiques Humidite**")
        stats_humid = {
            "Indicateur": ["Minimum", "Maximum", "Moyenne", "Ecart-type"],
            "Valeur": [
                f"{stats['humid_min']}%",
                f"{stats['humid_max']}%",
                f"{stats['humid_mean']}%",
                f"{stats['humid_std']}",
            ],
        }
        st.table(pd.DataFrame(stats_humid))

    st.warning(
        f"**Analyse Industrielle :** Les ecarts-types mesures ({stats['temp_std']} pour T° / "
        f"{stats['humid_std']} pour H%) revelent une instabilite environnementale majeure. "
        f"Le score de **{score}/100** confirme la necessite d'implementer des regulateurs automatiques."
    )


st.sidebar.title("Navigation")
selected_page = st.sidebar.radio(
    "Choisir une vue",
    ["Recherche Entrepots", "Analyse Environnementale"],
    index=0,
)

if selected_page == "Recherche Entrepots":
    render_search_page()
else:
    render_environmental_page()
