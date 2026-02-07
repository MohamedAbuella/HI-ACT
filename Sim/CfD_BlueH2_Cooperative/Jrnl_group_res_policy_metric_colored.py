# -*- coding: utf-8 -*-
"""
Created on Wed Jan 28 04:30:06 2026

Elsevier-ready heatmaps: all 12 metrics,
metric-specific LIGHT colors, black font, integer formatting.
Colorbar titles restored (as in original code).
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap

# ============================================================
# FONT CONFIGURATION (USER-ADJUSTABLE)
# ============================================================

FONT_SIZES = {
    "axis_label": 22,        # X and Y axis titles
    "axis_ticks": 20,        # X and Y axis tick labels
    "cbar_label": 20,        # Colorbar title
    "cbar_ticks": 20,        # Colorbar tick labels
    "annotation": 20,        # Numbers inside heatmap cells
    "na_annotation": 20      # "NA" text inside heatmap cells
}

# FONT_SIZES = {
#     "axis_label": 18,        # X and Y axis titles
#     "axis_ticks": 16,        # X and Y axis tick labels
#     "cbar_label": 16,        # Colorbar title
#     "cbar_ticks": 16,        # Colorbar tick labels
#     "annotation": 16,        # Numbers inside heatmap cells
#     "na_annotation": 16      # "NA" text inside heatmap cells
# }


# ============================================================
# DEFINE ROOT PATHS
# ============================================================
# 
PI_CO2_CfD_folder = "CfD_BlueH2_Cooperative"
# PI_CO2_CfD_folder = "CfD_GreyH2_Cooperative"

### Summary_Res_folder = "Summary_Results_0_250_100_500"
Summary_Res_folder = "Summary_Results_25_250_100_500"



ROOT = Path(__file__).resolve().parent
INPUT_DIR = ROOT / "Output" / PI_CO2_CfD_folder / Summary_Res_folder
OUTPUT_DIR = INPUT_DIR

# ============================================================
# CCS LABEL
# ============================================================
CCS_LABEL = "with_CCS" if "Blue" in PI_CO2_CfD_folder else "wo_CCS"

# ============================================================
# EXCEL FILES
# ============================================================
path_support = INPUT_DIR / "Res_CfD_Support_Hydrogen.xlsx"
path_cost = INPUT_DIR / "Res_Hydrogen_Marginal_Cost.xlsx"

path_sub_cost = INPUT_DIR / "Res_Hydrogen_Subsidised_Cost.xlsx"

path_emissions = INPUT_DIR / "Res_CO2_Emissions.xlsx"
path_opcost = INPUT_DIR / "Res_Operational_Cost.xlsx"
path_opex_support = INPUT_DIR / "Res_Opex_Support_Hydrogen.xlsx"
path_npv = INPUT_DIR / "Res_NPV.xlsx"
path_h2split = INPUT_DIR / "Res_P2G_G2G.xlsx"
path_npv_wo_cfd = INPUT_DIR / "Res_NPV_without_CfD_H2.xlsx"
path_total_cfd_cost = INPUT_DIR / "Res_Total_CfD_cost.xlsx"
path_mac = INPUT_DIR / "Res_Marginal_Abatement_Cost.xlsx"
path_mach = INPUT_DIR / "Res_Marginal_Abatement_Cost_Hydrogen.xlsx"
path_mach_sub = INPUT_DIR / "Res_Sub_Marginal_Abatement_Cost_Hydrogen.xlsx"
path_total_h2 = INPUT_DIR / "Res_Total_H2_Production.xlsx"


# ============================================================
# READ DATA
# ============================================================
def read_sheets(path):
    return (
        pd.read_excel(path, sheet_name="High_Price"),
        pd.read_excel(path, sheet_name="Low_Price"),
    )

df1_high, df1_low = read_sheets(path_support)
df2_high, df2_low = read_sheets(path_cost)

df_sub_cost_high, df_sub_cost_low = read_sheets(path_sub_cost)

df_em_high, df_em_low = read_sheets(path_emissions)
df_opcost_high, df_opcost_low = read_sheets(path_opcost)
df_opex_sup_high, df_opex_sup_low = read_sheets(path_opex_support)
df_npv_high, df_npv_low = read_sheets(path_npv)
df_h2_high, df_h2_low = read_sheets(path_h2split)
df_npv_wo_cfd_high, df_npv_wo_cfd_low = read_sheets(path_npv_wo_cfd)
df_total_cfd_cost_high, df_total_cfd_cost_low = read_sheets(path_total_cfd_cost)
df_mac_high, df_mac_low = read_sheets(path_mac)
df_mach_high, df_mach_low = read_sheets(path_mach)
df_mach_sub_high, df_mach_sub_low = read_sheets(path_mach_sub)
df_total_h2_high, df_total_h2_low = read_sheets(path_total_h2)


# ============================================================
# SCENARIOS
# ============================================================
SCENARIO_SHORT = {
    "High RES–High H2": "Hi_H2",
    "High RES–Low H2": "Lw_H2"
}

SCENARIO_FOLDER = {
    "High RES–High H2": "Scenario_High_H2",
    "High RES–Low H2": "Scenario_Low_H2",
}

PRICE_LABEL_SHORT = {
    "High_Price": "Hi_Price",
    "Low_Price": "Lw_Price"
}

scenarios = ["High RES–High H2", "High RES–Low H2"]

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def clean_numeric_df(df, keep_na_cols=None):
    df = df.copy()
    if keep_na_cols is None:
        keep_na_cols = []

    for col in df.columns:
        if col not in ["CO2 Price", "CfD Price"]:
            if col in keep_na_cols:
                df[col] = df[col].apply(
                    lambda x: x if x == "NA" else pd.to_numeric(x, errors="coerce")
                )
            else:
                df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

def get_heatmap_outfolder(base_heatmap_dir, scenario, price_label):
    scen_folder = SCENARIO_FOLDER.get(
        scenario, scenario.replace(" ", "_").replace("–", "-")
    )
    out_dir = base_heatmap_dir / scen_folder / price_label
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir

# ============================================================
# LIGHT / PASTEL COLORMAPS
# ============================================================


LIGHT_RED = LinearSegmentedColormap.from_list(
    "LightRed", ["#fde0dc", "#fcbba1", "#f76666"]
)

LIGHT_PURPLE = LinearSegmentedColormap.from_list(
    "LightPurple", ["#f3e6ff", "#d9b3ff", "#c28fff"]
)

LIGHT_GREEN = LinearSegmentedColormap.from_list(
    "LightGreen", ["#f7fcf5", "#c7e9c0", "#74c476"]
)

LIGHT_GREY = LinearSegmentedColormap.from_list(
    "LightGrey", ["#ffffff", "#e5e5e5", "#bdbdbd"]
)

LIGHT_ORANGE = LinearSegmentedColormap.from_list(
    "LightOrange", ["#fff5eb", "#fdd0a2", "#fdae6b"]
)

LIGHT_CYAN = LinearSegmentedColormap.from_list(
    "LightCyan", ["#f7fcfd", "#d0e7f2", "#9ecae1"]
)

LIGHT_OLIVE = LinearSegmentedColormap.from_list(
    "LightOlive", ["#fffff0", "#d9f0a3", "#addd8e"]
)

LIGHT_BLUE = LinearSegmentedColormap.from_list(
    "CyanGreyBlue",
    ["#d1f2eb", "#e8f8f5", "#f2f2f2", "#ddeaf7", "#9ecae1"]
)


LIGHT_LIME = LinearSegmentedColormap.from_list(
    "LightLime",
    ["#f0f9e8", "#d9f0d3", "#f2f2f2", "#bae4b3", "#7fc97f"]
)


LIGHT_BROWN = LinearSegmentedColormap.from_list(
    "LightBrown",
    ["#fdf5e6", "#f3e6c8", "#f2f2f2", "#e0cfa9", "#c9a66b"]
)

LIGHT_SLATE = LinearSegmentedColormap.from_list(
    "LightSlate",
    ["#f5f5f5", "#e0ded8", "#f2f2f2", "#cfcac2", "#b5afa5"]
)

LIGHT_ROSEWOOD = LinearSegmentedColormap.from_list(
    "LightRosewood",
    ["#faf0f0", "#f2dada", "#f2f2f2", "#e0bcbc", "#c99898"]
)

LIGHT_TAUPE = LinearSegmentedColormap.from_list(
    "LightTaupe",
    ["#f7f7f2", "#e5e4dc", "#f2f2f2", "#d2cec3", "#b8b2a7"]
)

LIGHT_TURQUOISE = LinearSegmentedColormap.from_list(
    "LightTurquoise",
    ["#e8f9f7", "#c7ede8", "#f2f2f2", "#9ddfd6", "#5bc0be"]
)

# ============================================================
# HEATMAP FUNCTION
# ============================================================
def plot_heatmap(df, value_col, out_folder, fig_name,
                 fmt=".1f", cmap=LIGHT_BLUE, cbar_label=None, round_int=False):

    sns.set_theme(style="white")
    df = df.replace("NA", np.nan)
    df = clean_numeric_df(df)

    heat_map = df.pivot(index="CO2 Price", columns="CfD Price", values=value_col)

    if round_int:
        heat_map = heat_map.round(0)
        fmt = ".0f"

    fig, ax = plt.subplots(figsize=(10, 7))
    hm = sns.heatmap(
        heat_map,
        annot=True,
        fmt=fmt,
        cmap=cmap,
        linewidths=0.5,
        linecolor="grey",
        cbar_kws={"shrink": 0.9, "pad": 0.02},
        ax=ax
    )

    for y in range(heat_map.shape[0]):
        for x in range(heat_map.shape[1]):
            if pd.isna(heat_map.iloc[y, x]):
                ax.text(
                    x + 0.5, y + 0.5, "NA",
                    ha="center", va="center",
                    fontsize=FONT_SIZES["na_annotation"],
                    color="black"
                )

    if cbar_label:
        cbar = hm.collections[0].colorbar
        cbar.set_label(cbar_label, fontsize=FONT_SIZES["cbar_label"])
        cbar.ax.tick_params(labelsize=FONT_SIZES["cbar_ticks"])

    for text in hm.texts:
        text.set_color("black")
        text.set_fontsize(FONT_SIZES["annotation"])

    ax.set_xlabel("CfD Price [£/MWh]", fontsize=FONT_SIZES["axis_label"])
    ax.set_ylabel("CO2 Price [£/tCO$_2$]", fontsize=FONT_SIZES["axis_label"])
    ax.tick_params(axis='both', labelsize=FONT_SIZES["axis_ticks"])

    plt.tight_layout()
    plt.savefig(out_folder / f"{fig_name}.png", dpi=300, bbox_inches="tight")
    plt.savefig(out_folder / f"{fig_name}.pdf", bbox_inches="tight")
    plt.close()

    print(f"Saved: {fig_name}")

# ============================================================
# SCORE FUNCTION
# ============================================================
def prepare_and_rank(df_support, df_cost, scenario, weight_support=0.5, weight_cost=0.5):
    df = pd.merge(df_support, df_cost,
                  on=["CO2 Price", "CfD Price"],
                  suffixes=('_support', '_margcost'))
    df = df.rename(columns={scenario + "_support": "support",
                            scenario + "_margcost": "marginal_cost"})
    df["support"] = pd.to_numeric(df["support"], errors="coerce")
    df["marginal_cost"] = pd.to_numeric(df["marginal_cost"], errors="coerce")

    def minmax_score(series, invert=False):
        mn, mx = series.min(), series.max()
        if mx == mn:
            return pd.Series(1.0, index=series.index)
        s = (series - mn) / (mx - mn)
        return 1 - s if invert else s

    df["support_score"] = minmax_score(df["support"], invert=True)
    df["cost_score"] = minmax_score(df["marginal_cost"], invert=True)
    df["combined_score"] = weight_support * df["support_score"] + weight_cost * df["cost_score"]
    return df.sort_values("combined_score", ascending=False).reset_index(drop=True)

# ============================================================
# MAIN EXECUTION
# ============================================================
results = {}
heatmap_folder = OUTPUT_DIR / "Heatmaps"
heatmap_folder.mkdir(exist_ok=True)

for label, sup_df, cost_df in [("High_Price", df1_high, df2_high),
                               ("Low_Price", df1_low, df2_low)]:

    price_short = PRICE_LABEL_SHORT[label]
    results[label] = {}

    for scen in scenarios:
        ranked = prepare_and_rank(sup_df, cost_df, scenario=scen)
        results[label][scen] = ranked
        out_folder = get_heatmap_outfolder(heatmap_folder, scen, price_short)
        sc_short = SCENARIO_SHORT[scen]

        plot_heatmap(ranked, "support", out_folder,
                     f"Fig_CfD_support_hyd_{sc_short}_{price_short}_{CCS_LABEL}",
                     cmap=LIGHT_BROWN, cbar_label="Support [million £]")

        plot_heatmap(ranked, "marginal_cost", out_folder,
                     f"Fig_marg_H2_cost_{sc_short}_{price_short}_{CCS_LABEL}",
                     cmap=LIGHT_ORANGE, cbar_label="Marginal Cost [£/MWh]", round_int=True)

        # >>> NEW: Subsidised H2 cost (same styling as marginal cost)
        plot_heatmap(df_sub_cost_high if label=="High_Price" else df_sub_cost_low,
                     scen, out_folder,
                     f"Fig_Sub_H2_cost_{sc_short}_{price_short}_{CCS_LABEL}",
                     cmap=LIGHT_ORANGE, cbar_label="Subsidised Cost [£/MWh]", round_int=True)

        plot_heatmap(ranked, "combined_score", out_folder,
                     f"Fig_score_{sc_short}_{price_short}_{CCS_LABEL}",
                     fmt=".2f", cmap=plt.cm.RdYlGn_r, cbar_label="Combined Score")

        plot_heatmap(df_em_high if label=="High_Price" else df_em_low,
                     scen, out_folder,
                     f"Fig_emissions_{sc_short}_{price_short}_{CCS_LABEL}",
                     fmt=".0f", cmap=LIGHT_TAUPE, cbar_label="CO2 Emissions [tCO2]")

        plot_heatmap(df_opcost_high if label=="High_Price" else df_opcost_low,
                     scen, out_folder,
                     f"Fig_opcost_{sc_short}_{price_short}_{CCS_LABEL}",
                     cmap=LIGHT_RED, cbar_label="Operational Cost [million £]")

        plot_heatmap(df_opex_sup_high if label=="High_Price" else df_opex_sup_low,
                     scen, out_folder,
                     f"Fig_opex_support_hyd_{sc_short}_{price_short}_{CCS_LABEL}",
                     cmap=LIGHT_CYAN, cbar_label="Opex Support [million £]")

        plot_heatmap(df_npv_high if label=="High_Price" else df_npv_low,
                     scen, out_folder,
                     f"Fig_NPV_{sc_short}_{price_short}_{CCS_LABEL}",
                     cmap=LIGHT_PURPLE, cbar_label="NPV [billion £]", round_int=True)

        df_h2 = df_h2_high if label=="High_Price" else df_h2_low
        df_h2["green_ratio"] = df_h2[f"{scen} - P2G"] / (
            df_h2[f"{scen} - P2G"] + df_h2[f"{scen} - G2G"]
        )

        plot_heatmap(df_h2, "green_ratio", out_folder,
                     f"Fig_green_H2_ratio_{sc_short}_{price_short}_{CCS_LABEL}",
                     fmt=".2f", cmap=LIGHT_OLIVE, cbar_label="Green H2 Ratio")

        plot_heatmap(df_npv_wo_cfd_high if label=="High_Price" else df_npv_wo_cfd_low,
                     scen, out_folder,
                     f"Fig_NPV_wo_CfD_H2_{sc_short}_{price_short}_{CCS_LABEL}",
                     cmap=LIGHT_GREEN, cbar_label="NPV w/o CfD [billion £]", round_int=True)

        plot_heatmap(df_total_cfd_cost_high if label=="High_Price" else df_total_cfd_cost_low,
                     scen, out_folder,
                     f"Fig_Total_CfD_cost_{sc_short}_{price_short}_{CCS_LABEL}",
                      cmap=LIGHT_ROSEWOOD, cbar_label="Total CfD Cost [billion £]")


        plot_heatmap(df_mac_high if label=="High_Price" else df_mac_low,
                     scen, out_folder,
                     f"Fig_MAC_{sc_short}_{price_short}_{CCS_LABEL}",
                     cmap=LIGHT_BLUE, cbar_label="Marginal Abatement Cost [£/tCO2]", round_int=True)

        plot_heatmap(df_mach_high if label=="High_Price" else df_mach_low,
                     scen, out_folder,
                     f"Fig_MACH_{sc_short}_{price_short}_{CCS_LABEL}",
                     cmap=LIGHT_BLUE, cbar_label="MAC Hydrogen [£/tCO2]", round_int=True)

        plot_heatmap(df_mach_sub_high if label=="High_Price" else df_mach_sub_low,
                     scen, out_folder,
                     f"Fig_MACH_Sub_{sc_short}_{price_short}_{CCS_LABEL}",
                     cmap=LIGHT_BLUE, cbar_label="MAC Hydrogen (Sub) [£/tCO2]", round_int=True)

        plot_heatmap(df_total_h2_high if label=="High_Price" else df_total_h2_low,
                     scen, out_folder,
                     f"Fig_Total_H2_Production_{sc_short}_{price_short}_{CCS_LABEL}",
                     cmap=LIGHT_TURQUOISE, cbar_label="Total H$_2$ Production [GWh]")


# ============================================================
# SAVE SUMMARY WORKBOOK
# ============================================================
summary_path = OUTPUT_DIR / "policy_combo_ranked_summary.xlsx"
with pd.ExcelWriter(summary_path, engine="openpyxl") as writer:
    for price_label in results:
        for scen in results[price_label]:
            name = f"{price_label}_{scen[:20].replace('–','-').replace(' ','_')}"
            results[price_label][scen].to_excel(writer, sheet_name=name[:31], index=False)

print("\nSaved ranked summary to:", summary_path)
