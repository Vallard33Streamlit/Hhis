import streamlit as st
import pandas as pd
import numpy as np
import sys
import os
from io import BytesIO

st.set_page_config(layout="wide")
df_trendeo = pd.read_excel("Fusion_listes_HHI.xlsx", sheet_name="Long list finale").drop(columns=["Indices HHI EU"])
df_hhis = pd.read_excel("hhis_2.xlsx").drop(columns=["product"])

def to_str(x):
    if np.isnan(x):
        return np.nan
    else:
        s = str(int(x))
        if len(s) % 2 == 0:
            return s
        else :
            return "0" + s


df_trendeo["Code HS6 2022"] = df_trendeo["Code HS6 2022"].apply(to_str)
df_trendeo["Code HS6 2017 associé"] = df_trendeo["Code HS6 2017 associé"].apply(to_str)
df_trendeo["Code ISIC Trendeo associé"] = df_trendeo["Code ISIC Trendeo associé"].apply(to_str)
df_hhis["k"] = df_hhis["k"].apply(to_str)

df = df_hhis.merge(df_trendeo, how="outer", left_on="k", right_on="Code HS6 2022")
df.drop(columns=[c for c in df.columns if c[0] == "i"], inplace=True)

order_col = ["Code HS6", "Label HS6", "HHi Européen", "HHi Mondial", "Part UE CF", "Part UE CDV",
             "Taux de couverture Exportations/Importations", "Taux de couverture de transit (Transit/Importations)", "Taux de couverture Exportations/Importations françaises",
             "HHI CF", "HHI CDV", "Code ISIC", "Label ISIC", "Code HS6 2017",
             "Importations", "Exportations", "Valeur des flux transitant dans l'UE", "Importations françaises", "Exportations françaises", "Valeur des échanges mondiaux",
              "Quantités importées", "Quantités exportées", "Quantités transitant dans l'UE", "Quantités importées en France", "Quantité exportées en France", "Quantités totales échangées",
              "Premier exporateur vers l'UE", "Premier exportateur mondial", "Deuxième exporateur vers l'UE", "Deuxième exportateur mondial", "Troisième exporateur vers l'UE", "Troisième exportateur mondial", "Quatrième exporateur vers l'UE", "Quatrième exportateur mondial", "Cinquième exporateur vers l'UE", "Cinquième exportateur mondial",
              "Part du premier exportateur vers l'UE", "Part du premier exportateur mondial", "Part du deuxième exportateur vers l'UE", "Part du deuxième exportateur mondial", "Part du troisième exportateur vers l'UE", "Part du troisième exportateur mondial", "Part du quatrième exportateur vers l'UE", "Part du quatrième exportateur mondial", "Part du cinquième exportateur vers l'UE", "Part du cinquième exportateur mondial"]

df = df[order_col]

# --- Sidebar : Filtres globaux ---
st.sidebar.header("Filtres globaux")

log_values = np.linspace(-3, 6, 901)
filter_v_imp_fr = st.sidebar.checkbox("Filtrer les produits grâce aux importations européennes 2024", key="filter_v_imp_fr")
if filter_v_imp_fr:
    log_value_v_imp_fr = st.sidebar.select_slider("Importations européennes (en 1000$) supérieur à :", options=log_values, value=-3, format_func=lambda x: f"{10**x:.3f}")
    df = df[df["Importations"] >= 10**log_value_v_imp_fr]

# Filtre hs2
hs2_filter = st.sidebar.radio(
    "Filtrer par hs2 pour les produits dans les distributions :",
    options=["Tous", "Uniquement agroalimentaire", "Tous sauf agroalimentaire"],
    index=0
)
if hs2_filter == "Uniquement agroalimentaire":
    df = df[df["hs2"].astype(float) < 25]
elif hs2_filter == "Tous sauf agroalimentaire":
    df = df[df["hs2"].astype(float) >= 25]

# Filtre taux_couverture_imp_exp
taux_couverture_checkbox = st.sidebar.checkbox("Garder uniquement les produits tels que l'UE soit importatrice nette en 2024", key="taux_couverture_checkbox")
if taux_couverture_checkbox:
    df = df[df["taux_couverture_imp_exp"] < 1]
# Filtre taux_couverture_imp_exp
taux_couverture_fr_checkbox = st.sidebar.checkbox("Garder uniquement les produits tels que la France soit importatrice nette en 2024", key="taux_couverture_fr_checkbox")
if taux_couverture_fr_checkbox:
    df = df[df["taux_couverture_imp_exp_fr"] < 1]
# Filtre taux_couverture_transit
filter_by_taux_couverture_transit = st.sidebar.checkbox("Filtrer les produits grâce à un taux de transit", key="filter_by_taux_couverture_transit")
if filter_by_taux_couverture_transit:
    rap_flux_transit = st.sidebar.slider("Rapport entre les flux transitants en Europe et les importations inférieur à :", min_value=0.0, max_value=3.0, value=1.0, step=0.1, format="%.2f")
    df = df[df["taux_couverture_transit"] < rap_flux_transit]
# Filtre hhi_EU
filter_by_hhi_eu = st.sidebar.checkbox("Filtrer les produits grâce à un HHi européen", key="filter_by_hhi_eu")
if filter_by_hhi_eu:
    hhi_eu = st.sidebar.slider("HHi européen supérieur à :", min_value=0.0, max_value=1.0, value=0.25, step=0.01, format="%.2f")
    df = df[df["hhi_EU"] >= hhi_eu]
# Filtre hhi_M
filter_by_hhi_m = st.sidebar.checkbox("Filtrer les produits grâce à un HHi mondial", key="filter_by_hhi_m")
if filter_by_hhi_m:
    hhi_M = st.sidebar.slider("HHi mondial supérieur à :", min_value=0.0, max_value=1.0, value=0.25, step=0.01, format="%.2f")
    df = df[df["hhi_M"] >= hhi_M]


# --- Sélection des méthodes (coef_*) ---
coef_columns = [col for col in df.columns if col.startswith("coef_")]
selected_coefs = st.multiselect(
    "Sélectionne les méthodes à analyser :",
    options=coef_columns,
    default=coef_columns
)

n = (df[selected_coefs].notna().sum(axis=1) == 0).sum()
st.write(f"{n} produits n'ont pas pu être classés")

# --- Paramètres x% et y% ---
x_percent = st.slider("x% (seuil de méthodes où le produit doit être dans le top y%) :", 0, 100, 50)
y_percent = st.slider("y% (seuil de la distribution pour une méthode) :", 0, 100, 10)
# --- Calcul : Produits dans le top y% pour chaque méthode ---
l_thresholds = []
l_cols_thresholds = []
for coef in coef_columns:
    threshold = np.percentile(df[coef].dropna(), 100 - y_percent)
    if coef in selected_coefs:
        l_thresholds.append(threshold)
        l_cols_thresholds.append(coef)
    col = (df[coef] >= threshold).astype(float)
    col[df[coef].isna()] = np.nan
    df[f"in_top_{y_percent}%_{coef[5:]}"] = col

# Affichage des seuils
df_thresholds = pd.DataFrame({"Coef":selected_coefs, "Seuil":l_thresholds})
show_thresholds = st.checkbox("Afficher les seuils", key="show_thresholds")
if show_thresholds:
    st.write("### Seuils appliqués")
    st.dataframe(df_thresholds)

# --- Calcul : Produits avec au moins x% des méthodes dans le top y% ---
n_selected_coefs = len(selected_coefs)
if n_selected_coefs > 0:
    top_y_columns = [f"in_top_{y_percent}%_{coef[5:]}" for coef in selected_coefs]
    df[f"prop_methodes_in_top_{y_percent}%"] = df[top_y_columns].mean(axis=1) * 100
    df = df[df[f"prop_methodes_in_top_{y_percent}%"] >= x_percent]
else:
    st.warning("Sélectionne au moins une méthode (coef_*).")

# Filtre produits agro-alimentaires
hs2_filter2 = st.radio(
    "Afficher :",
    options=["Tous les produits", "Uniquement les produits agroalimentaire", "Tous les produits sauf les agroalimentaires"],
    index=0
)
if hs2_filter2 == "Uniquement les produits agroalimentaire":
    df = df[df["hs2"].astype(float) < 25]
elif hs2_filter2 == "Tous les produits sauf les agroalimentaires":
    df = df[df["hs2"].astype(float) >= 25]

# Modifier l'ordre des colonnes de df
l_cols = ["product", f"prop_methodes_in_top_{y_percent}%", "Description", "v_imp_fr"] + [c for c in df.columns if (str(c)[:3] == "hhi")|(str(c)[0] == "t")] + ["IGPC", "IGPC_rank", "hs4", "hs2", "Description_hs4", "Description_hs2", "2007", "2002"] + [c for c in df.columns if (str(c)[0] == "c")|(str(c)[0] == "N")|(str(c)[0] == "i")]
df = df[l_cols]

# --- Sélection des colonnes à afficher ---
all_columns = df.columns.tolist()
default_columns = df.columns[:11]
selected_columns = st.multiselect(
    "Sélectionne les colonnes à afficher :",
    options=all_columns,
    default=default_columns
)

# --- Affichage du tableau ---
st.write("### Tableau des produits")
st.write(f"Il y a {len(df)} produits (HS6) \"essentiels\"")
st.dataframe(df[selected_columns])

# --- Téléchargement des résultats ---
nom_fichier = st.text_input("Nom du fichier à télécharger (sans extension) :", "resultats_filtres")

format = st.radio(
    "Format",
    options=["csv", "excel"],
    index=0
)

# Bouton de téléchargement
if format == "csv":
    st.download_button(
        label="Télécharger le tableau filtré",
        data=df.to_csv(index=False, sep=";").encode("utf-8"),
        file_name=f"{nom_fichier}.csv",
        mime="text/csv"
    )
else:
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Feuille1')
    st.download_button(
        label="Télécharger le tableau filtré",
        data=output.getvalue(),
        file_name=f"{nom_fichier}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )