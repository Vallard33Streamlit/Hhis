import numpy as np
import pandas as pd

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

df = df_hhis.merge(df_trendeo, how="outer", left_on="k", right_on="Code HS6 2022").drop(columns="k")
df.drop(columns=[c for c in df.columns if c[0] == "i"], inplace=True)

df.columns = ["HHi Européen", "HHi Mondial",
              "Taux de couverture Exportations/Importations", "Taux de couverture de transit (Transit/Importations)", "Taux de couverture Exportations/Importations françaises",
              "Premier exporateur vers l'UE", "Premier exportateur mondial", "Deuxième exporateur vers l'UE", "Deuxième exportateur mondial", "Troisième exporateur vers l'UE", "Troisième exportateur mondial", "Quatrième exporateur vers l'UE", "Quatrième exportateur mondial", "Cinquième exporateur vers l'UE", "Cinquième exportateur mondial",
              "Importations", "Exportations", "Valeur des flux transitant dans l'UE", "Importations françaises", "Exportations françaises", "Valeur des échanges mondiaux",
              "Quantités importées", "Quantités exportées", "Quantités transitant dans l'UE", "Quantités importées en France", "Quantité exportées en France", "Quantités totales échangées",
              "Part du premier exportateur vers l'UE", "Part du premier exportateur mondial", "Part du deuxième exportateur vers l'UE", "Part du deuxième exportateur mondial", "Part du troisième exportateur vers l'UE", "Part du troisième exportateur mondial", "Part du quatrième exportateur vers l'UE", "Part du quatrième exportateur mondial", "Part du cinquième exportateur vers l'UE", "Part du cinquième exportateur mondial",
              "Label HS6", "Code HS6 2022", "Code HS6 2017", "Code ISIC", "Label ISIC", "HHI CF", "HHI CDV", "Part UE CF", "Part UE CDV"]


print(df.columns)