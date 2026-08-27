import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import streamlit_antd_components as sac
from openpyxl.styles import Font, PatternFill
from openpyxl.styles import Alignment


st.set_page_config(layout="wide")

df = pd.read_csv(
    "hhis_et_autres.csv",
    dtype={"Code HS6": str, "Code HS4": str, "Code ISIC": str, "Code HS6 2017": str},
)

# Retire les éventuelles colonnes Argos de l'affichage et des exports.
columns_to_remove = [column for column in df.columns if "argos" in column.casefold()]
df = df.drop(columns=columns_to_remove)


@st.cache_data
def load_labels():
    labels_sections = pd.read_csv("labels_sections.csv")
    labels_sections["l_hs2"] = labels_sections["l_hs2"].fillna("").apply(lambda x: x.split(","))
    labels_sections.loc[labels_sections["Niveau"] == "HS2", "l_hs2"] = np.nan
    labels_sections_tree = []
    for s in labels_sections[labels_sections["Niveau"] == "Section"].iterrows():
        dic = {}
        dic["label"] = "Section " + s[1].Catégorie + " - " + s[1].Label
        dic["value"] = s[1].Catégorie
        children = []
        for c in labels_sections[
            labels_sections["Catégorie"].apply(lambda x: x in s[1].l_hs2)
        ].iterrows():
            dic_c = {}
            dic_c["label"] = c[1].Catégorie + " - " + c[1].Label
            dic_c["value"] = c[1].Catégorie
            children.append(dic_c)
        dic["children"] = children
        labels_sections_tree.append(dic)
    return labels_sections, labels_sections_tree


# --- Sidebar : Filtres globaux ---
st.sidebar.header("Filtres globaux")
l_filtres = []

log_values = np.linspace(-3, 6, 901)
filter_v_imp_fr = st.sidebar.checkbox(
    "Filtrer les produits grâce aux importations européennes 2024",
    key="filter_v_imp_fr",
)
if filter_v_imp_fr:
    log_value_v_imp_fr = st.sidebar.select_slider(
        "Importations européennes (en 1000$) supérieur à :",
        options=log_values,
        value=-3,
        format_func=lambda x: f"{10**x:.3f}",
    )
    df = df[df["Importations"] >= 10**log_value_v_imp_fr]
    l_filtres.append(
        ("Importations européennes (en 1000$) supérieur à :", 10**log_value_v_imp_fr)
    )


labels_sections, labels_sections_tree = load_labels()
# Filtre hs2
with st.sidebar.expander(
    "Sélectionner les sections ou catégories HS2 à afficher",
    expanded=False,
    key="container_labels_sections_tree",
):
    selected_categories_index = sac.tree(
        labels_sections_tree,
        open_index=[],
        index=list(labels_sections.index),
        checkbox=True,
        return_index=True,
        key="labels_sections_tree",
        height=500,
    )
    selected_categories = labels_sections.loc[
        selected_categories_index, "Catégorie"
    ].values
    df = df[df["Code HS6"].apply(lambda x: x[:2] in selected_categories)]

# Filtre taux_couverture_imp_exp
filter_by_taux_couverture = st.sidebar.checkbox(
    "Filtrer les produits grâce à un taux de couverture",
    key="filter_by_taux_couverture",
)
if filter_by_taux_couverture:
    taux_couverture = st.sidebar.slider(
        "Rapport entre les exportations et les importations inférieur à :",
        min_value=0.0,
