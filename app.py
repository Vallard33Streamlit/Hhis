import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

st.set_page_config(layout="wide")

df=pd.read_csv("hhis_et_autres.csv", dtype={"Code HS6": str, "Code HS4": str, "Code ISIC": str, "Code HS6 2017": str})

# --- Sidebar : Filtres globaux ---
st.sidebar.header("Filtres globaux")

log_values = np.linspace(-3, 6, 901)
filter_v_imp_fr = st.sidebar.checkbox("Filtrer les produits grâce aux importations européennes 2024", key="filter_v_imp_fr")
if filter_v_imp_fr:
    log_value_v_imp_fr = st.sidebar.select_slider("Importations européennes (en 1000$) supérieur à :", options=log_values, value=-3, format_func=lambda x: f"{10**x:.3f}")
    df = df[df["Importations"] >= 10**log_value_v_imp_fr]

# Filtre hs2
hs2_filter = st.sidebar.radio(
    "Filtrer les produits par catégorie :",
    options=["Tous", "Uniquement agroalimentaire", "Tous sauf agroalimentaire"],
    index=0
)
if hs2_filter == "Uniquement agroalimentaire":
    df = df[df["Code HS6"].apply(lambda x : int(x[:2]) < 25)]
elif hs2_filter == "Tous sauf agroalimentaire":
    df = df[df["Code HS6"].apply(lambda x : int(x[:2]) >= 25)]

# Filtre taux_couverture_imp_exp
taux_couverture_checkbox = st.sidebar.checkbox("Garder uniquement les produits tels que l'UE est importatrice nette en 2024", key="taux_couverture_checkbox")
if taux_couverture_checkbox:
    df = df[df["Taux de couverture Exportations/Importations"] < 1]
# Filtre taux_couverture_transit
filter_by_taux_couverture_transit = st.sidebar.checkbox("Filtrer les produits grâce à un taux de transit", key="filter_by_taux_couverture_transit")
if filter_by_taux_couverture_transit:
    rap_flux_transit = st.sidebar.slider("Rapport entre les flux transitants en Europe et les importations inférieur à :", min_value=0.0, max_value=3.0, value=1.0, step=0.1, format="%.2f")
    df = df[df["Taux de couverture de transit (Transit/Importations)"] < rap_flux_transit]
# Filtre taux_couverture_imp_exp
taux_couverture_fr_checkbox = st.sidebar.checkbox("Garder uniquement les produits tels que la France est importatrice nette en 2024", key="taux_couverture_fr_checkbox")
if taux_couverture_fr_checkbox:
    df = df[df["Taux de couverture Exportations/Importations françaises"] < 1]
#Filtre sur éléments équivalent trendeo
eq_trendeo_checkbox = st.sidebar.checkbox("Garder uniquement les produits qui ont une nomenclature trendeo", key="eq_trendeo_checkbox")
if eq_trendeo_checkbox:
    df = df[df["Label ISIC"].notna()]

#Filtre sur les premiers pays
filter_by_countries = st.sidebar.checkbox("Filtrer les produits par pays exportateurs", key="filter_by_countries")
if filter_by_countries:
    st.sidebar.markdown(
        '<p style="font-size: 14px; margin: 0 0 0.5rem 0;">Prendre les <b>n₁</b> premiers exportateurs vers l\'Europe parmi les <b>n₂</b> plus gros exportateurs mondiaux</p>',
        unsafe_allow_html=True
    )
    col1, col2 = st.sidebar.columns(2)
    n1 = col1.selectbox("n₁", range(1, 6), key="n1")
    n2 = col2.selectbox("n₂", range(n1, 6), key="n2")
    rangs = ["Premier", "Deuxième", "Troisième", "Quatrième", "Cinquième"]
    if n1 !=0 :
        s_exp_ue = df[[f"{rang} exporateur vers l'UE" for rang in rangs[:n1]]]
        s_exp_m = df[[f"{rang} exportateur mondial" for rang in rangs[:n2]]]
        mask = (
            s_exp_ue.apply(frozenset, axis=1)
            .combine(s_exp_m.apply(frozenset, axis=1),
                    lambda a, b: len(a & b) == len(a))
        )
        df = df[mask]

n_ess_elasticite = df["Essentialité grâce aux élasticités"].sum()
n_prio = df["Priorité d'Argos"].notna().sum()
# Filtre hhi_EU
st.header("Différents filtres sur les indices HHi et les parts d'investissements")
filter_by_hhi_eu = st.checkbox("Filtrer les produits par l'indice HHi européen", key="filter_by_hhi_eu")
if filter_by_hhi_eu:
    hhi_eu = st.slider("HHi européen supérieur à :", min_value=0.0, max_value=1.0, value=0.25, step=0.01, format="%.2f")
    df = df[df["HHi Européen"] >= hhi_eu]
# Filtre hhi_M
filter_by_hhi_m = st.checkbox("Filtrer les produits par l'indice HHi mondial", key="filter_by_hhi_m")
if filter_by_hhi_m:
    hhi_M = st.slider("HHi mondial supérieur à :", min_value=0.0, max_value=1.0, value=0.25, step=0.01, format="%.2f")
    df = df[df["HHi Mondial"] >= hhi_M]
# Filtre hhi_FR
filter_by_hhi_fr = st.checkbox("Filtrer les produits par l'indice HHi français", key="filter_by_hhi_fr")
if filter_by_hhi_fr:
    hhi_FR = st.slider("HHi français supérieur à :", min_value=0.0, max_value=1.0, value=0.25, step=0.01, format="%.2f")
    df = df[df["HHi Français"] >= hhi_FR]

# Filtre part_UE_CDV
filter_by_part_UE_CDV = st.checkbox("Filtrer les produits par la part européenne du contrôle opérationel", key="filter_by_part_UE_CDV")
if filter_by_part_UE_CDV:
    part_UE_CDV = st.slider("Part UE Contrôle opérationel inférieure à :", min_value=0.0, max_value=1.0, value=0.1, step=0.01, format="%.2f")
    df = df[(df["Part UE Contrôle opérationel"] <= part_UE_CDV)|(df["Part UE Contrôle opérationel"].isna())]
# Filtre part_UE_CF
filter_by_part_UE_CF = st.checkbox("Filtrer les produits par la part européenne du contrôle financier", key="filter_by_part_UE_CF")
if filter_by_part_UE_CF:
    part_UE_CF = st.slider("Part UE Contrôle financier inférieure à :", min_value=0.0, max_value=1.0, value=0.1, step=0.01, format="%.2f")
    df = df[(df["Part UE Contrôle financier"] <= part_UE_CF)|(df["Part UE Contrôle financier"].isna())]
# Filtre hhi_CDV
filter_by_hhi_CDV = st.checkbox("Filtrer les produits par l'indice HHi de contrôle opérationel", key="filter_by_hhi_CDV")
if filter_by_hhi_CDV:
    hhi_CDV = st.slider("HHI Contrôle opérationel supérieur à :", min_value=0.0, max_value=1.0, value=0.25, step=0.01, format="%.2f")
    df = df[(df["HHI Contrôle opérationel"] >= hhi_CDV)|(df["HHI Contrôle opérationel"].isna())]
# Filtre hhi_CF
filter_by_hhi_CF = st.checkbox("Filtrer les produits par l'indice HHi de contrôle financier", key="filter_by_hhi_CF")
if filter_by_hhi_CF:
    hhi_CF = st.slider("HHI Contrôle financier supérieur à :", min_value=0.0, max_value=1.0, value=0.25, step=0.01, format="%.2f")
    df = df[(df["HHI Contrôle financier"] >= hhi_CF)|(df["HHI Contrôle financier"].isna())]



# --- Sélection des colonnes à afficher ---
all_columns = df.columns.tolist()
default_columns = df.columns[:17]
selec_columns = st.checkbox("Sélection des colonnes à afficher", key="selec_columns")
if selec_columns:
    selected_columns = st.multiselect(
        "Sélection des colonnes à afficher",
        options=all_columns,
        default=default_columns,
        label_visibility = "collapsed"
    )
else:
    selected_columns=default_columns

# --- Affichage du tableau ---
st.write("### Tableau des produits")
st.write(f"Il y a {len(df)} produits (HS6) vulnérables, dont {df["Essentialité grâce aux élasticités"].sum()} essentiels selon les critères d'élasticités (sur {n_ess_elasticite}) et {df["Priorité d'Argos"].notna().sum()} prioritaires selon Argos (sur {n_prio}).")
st.dataframe(df[selected_columns])

# --- Téléchargement des résultats ---
nom_fichier = st.text_input("Nom du fichier à télécharger (sans extension) :", value="resultats_filtres", key="nom_fichier")

format = st.radio(
    "Format",
    options=["csv", "excel"],
    index=0
)

# Bouton de téléchargement
if format == "csv":
    if st.button("Préparer le téléchargement"):
        st.download_button(
            label="Télécharger le tableau filtré",
            data=df.to_csv(index=False, sep=";").encode("utf-8"),
            file_name=f"{nom_fichier}.csv",
            mime="text/csv"
        )
else:
    if st.button("Préparer le téléchargement"):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        st.download_button(
            label="Télécharger le tableau filtré",
            data=output.getvalue(),
            file_name=f"{nom_fichier}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )