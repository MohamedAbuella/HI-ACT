# -*- coding: utf-8 -*-
"""
Created on Thu Dec 11 21:32:08 2025

@author: Mhdella
"""

# save as analyze_policy_combos.py and run with: python analyze_policy_combos.py
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

# ============================================================
# DEFINE ROOT PATHS BASED ON SCRIPT LOCATION
# ============================================================


### Folder that contains both input files AND where output should be saved:
    

# PI_CO2_CfD_folder = 'CfD_GreyH2_Sub_H2green_Cooperative'
# PI_CO2_CfD_folder = 'CfD_BlueH2_Sub_H2green_Cooperative'

PI_CO2_CfD_folder = "CfD_BlueH2_Cooperative"
# PI_CO2_CfD_folder = "CfD_GreyH2_Cooperative"


Summary_Res_folder = "Summary_Results_0_250_100_500"
# Summary_Res_folder = "Summary_Results_0_40_400"


# The folder where THIS script is located (GB_Policy/)
ROOT = Path(__file__).resolve().parent

INPUT_DIR = ROOT / "Output" / PI_CO2_CfD_folder / Summary_Res_folder

# Save outputs to the same folder
OUTPUT_DIR = INPUT_DIR

# Input Excel files
path_support = INPUT_DIR / "Res_CfD_Support_Hydrogen.xlsx"
path_cost    = INPUT_DIR / "Res_Hydrogen_Marginal_Cost.xlsx"


# ============================================================
# READ INPUT DATA
# ============================================================

df1_high = pd.read_excel(path_support, sheet_name="High_Price")
df1_low  = pd.read_excel(path_support, sheet_name="Low_Price")
df2_high = pd.read_excel(path_cost, sheet_name="High_Price")
df2_low  = pd.read_excel(path_cost, sheet_name="Low_Price")

# ============================================================
# PREPARATION & RANKING FUNCTION
# ============================================================

def prepare_and_rank(df_support, df_cost, scenario, weight_support=0.5, weight_cost=0.5):

    df = pd.merge(df_support, df_cost,
                  on=["CO2 Price", "CfD Price"],
                  suffixes=('_support', '_margcost'))

    df = df.rename(columns={
        scenario + "_support": "support",
        scenario + "_margcost": "marginal_cost"
    })

    df["support"] = pd.to_numeric(df["support"], errors="coerce")
    df["marginal_cost"] = pd.to_numeric(df["marginal_cost"], errors="coerce")

    def minmax_score(series, invert=False):
        mn, mx = series.min(), series.max()
        if mx == mn:
            return pd.Series(1.0, index=series.index)
        s = (series - mn) / (mx - mn)
        return 1 - s if invert else s

    # Negative support = better → invert
    df["support_score"] = minmax_score(df["support"], invert=True)
    df["cost_score"]    = minmax_score(df["marginal_cost"], invert=True)

    df["combined_score"] = weight_support * df["support_score"] + \
                           weight_cost * df["cost_score"]

    return df.sort_values("combined_score", ascending=False).reset_index(drop=True)


SCENARIO_SHORT = {
    "High RES–High H2": "Hi_H2",
    "High RES–Low H2":  "Lw_H2"
}

SCENARIO_FOLDER = {
    "High RES–High H2": "Scenario_High_H2",
    "High RES–Low H2":  "Scenario_Low_H2",
}



# ============================================================
# HEATMAP GENERATION
# ============================================================

def make_heatmaps(df, scenario, price_label, out_folder):

    sns.set_theme(style="white")
    
    scenario_short = SCENARIO_SHORT.get(scenario, scenario.replace(" ", "_"))

    support_map = df.pivot(index="CO2 Price", columns="CfD Price", values="support")
    cost_map    = df.pivot(index="CO2 Price", columns="CfD Price", values="marginal_cost")
    score_map   = df.pivot(index="CO2 Price", columns="CfD Price", values="combined_score")

    cmap = "RdYlGn_r"

    def plot_single(data, title, filename):
        plt.figure(figsize=(10, 7))
        sns.heatmap(data, annot=True, fmt=".1f", cmap=cmap)
        plt.title(title, fontsize=14)
        plt.xlabel("CfD Price")
        plt.ylabel("CO2 Price")
        plt.tight_layout()
        plt.savefig(out_folder / filename, dpi=300)
        plt.close()

    plot_single(support_map,
                f"CfD-Based Support [million £] for Hydrogen – {scenario} – {price_label}",
                f"Fig_CfD_support_hyd_{scenario_short}_{price_label}.png")

    plot_single(cost_map,
                f"Marginal Cost of Hydrogen [£/MWh] – {scenario} – {price_label}",
                f"Fig_marg_H2_cost_{scenario_short}_{price_label}.png")

    plot_single(score_map,
                f"Combined Score – {scenario} – {price_label}",
                f"Fig_score_{scenario_short}_{price_label}.png")

    print(f"Heatmaps saved for {scenario} / {price_label}")
    



def get_heatmap_outfolder(base_heatmap_dir, scenario, price_label):
    """
    Returns: Heatmaps/Scenario_X/High_Price or Low_Price
    """
    scen_folder = SCENARIO_FOLDER.get(
        scenario,
        scenario.replace(" ", "_").replace("–", "-")
    )

    out_dir = base_heatmap_dir / scen_folder / price_label
    out_dir.mkdir(parents=True, exist_ok=True)

    return out_dir



# ============================================================
# MAIN RUN
# ============================================================

scenarios = ["High RES–High H2", "High RES–Low H2"]


# Output paths
summary_path = OUTPUT_DIR / "policy_combo_ranked_summary.xlsx"
heatmap_folder = OUTPUT_DIR / "Heatmaps"
heatmap_folder.mkdir(exist_ok=True)

results = {}

for label, sup_df, cost_df in [
    ("High_Price", df1_high, df2_high),
    ("Low_Price",  df1_low,  df2_low),
]:
    results[label] = {}
    for scen in scenarios:

        ranked = prepare_and_rank(sup_df, cost_df, scenario=scen)
        results[label][scen] = ranked

        # PASS THE ORIGINAL SCENARIO STRING
        make_heatmaps(
            ranked,
            scenario=scen,   # <-- use original string here
            price_label=label,
            out_folder=get_heatmap_outfolder(
                heatmap_folder,
                scenario=scen,
                price_label=label
            ))

# ============================================================
# SAVE SUMMARY WORKBOOK
# ============================================================

with pd.ExcelWriter(summary_path, engine="openpyxl") as writer:
    for price_label in results:
        for scen in results[price_label]:
            name = f"{price_label}_{scen[:20].replace('–','-').replace(' ','_')}"
            results[price_label][scen].to_excel(writer, sheet_name=name[:31], index=False)

print("\nSaved ranked summary to:", summary_path)

# ============================================================
# PRINT TOP 10
# ============================================================

for price_label in results:
    for scen in results[price_label]:
        print("\n" + "="*60)
        print(f"{price_label} - {scen} (top 10 combos)")
        cols = ["CO2 Price", "CfD Price", "support", "marginal_cost",
                "support_score", "cost_score", "combined_score"]
        print(results[price_label][scen][cols].head(10).to_string(index=False))



# ============================================================
# ADDITIONAL INPUT FOR EMISSIONS HEATMAPS
# ============================================================

path_emissions = INPUT_DIR / "Res_CO2_Emissions.xlsx"

df_em_high = pd.read_excel(path_emissions, sheet_name="High_Price")
df_em_low  = pd.read_excel(path_emissions, sheet_name="Low_Price")

# ============================================================
# HEATMAP FUNCTION FOR EMISSIONS
# ============================================================

def make_emission_heatmaps(df, scenario, price_label, out_folder):
    """
    Create heatmaps for CO2 emissions: lower emissions = green, higher = red.
    """
    sns.set_theme(style="white")
    
    em_map = df.pivot(index="CO2 Price", columns="CfD Price", values=scenario)
    
    plt.figure(figsize=(10, 7))
    sns.heatmap(em_map, annot=True, fmt=".0f", cmap="RdYlGn_r")  # reversed so low=green, high=red
    plt.title(f"CO2 Emissions [tCO2]  – {scenario} – {price_label}", fontsize=14)
    plt.xlabel("CfD Price")
    plt.ylabel("CO2 Price")
    plt.tight_layout()
    filename = f"Fig_emissions_{SCENARIO_SHORT.get(scenario, scenario)}_{price_label}.png"       
    plt.savefig(out_folder / filename, dpi=300)
    plt.close()
    
    print(f"Emission heatmap saved for {scenario} / {price_label}")



# ============================================================
# GENERATE EMISSION HEATMAPS
# ============================================================

for label, em_df in [("High_Price", df_em_high), ("Low_Price", df_em_low)]:
    for scen in scenarios:
        make_emission_heatmaps(
            em_df,
            scenario=scen,
            price_label=label,
            out_folder=get_heatmap_outfolder(
            heatmap_folder,
            scenario=scen,
            price_label=label))
                
        

# ============================================================
# ADDITIONAL INPUT FOR OPERATIONAL COST HEATMAPS
# ============================================================

path_opcost = INPUT_DIR / "Res_Operational_Cost.xlsx"

df_opcost_high = pd.read_excel(path_opcost, sheet_name="High_Price")
df_opcost_low  = pd.read_excel(path_opcost, sheet_name="Low_Price")

# ============================================================
# HEATMAP FUNCTION FOR OPERATIONAL COST
# ============================================================

def make_opcost_heatmaps(df, scenario, price_label, out_folder):
    """
    Create heatmaps for operational cost: lower cost = yellow, higher = red.
    """
    sns.set_theme(style="white")
    
    op_map = df.pivot(index="CO2 Price", columns="CfD Price", values=scenario)
    
    plt.figure(figsize=(10, 7))
    sns.heatmap(op_map, annot=True, fmt=".2f", cmap="YlOrRd")  # yellow->red gradient
    plt.title(f"Operational Cost [million £] – {scenario} – {price_label}", fontsize=14)
    plt.xlabel("CfD Price")
    plt.ylabel("CO2 Price")
    plt.tight_layout()
    filename = f"Fig_opcost_{SCENARIO_SHORT.get(scenario, scenario)}_{price_label}.png"    
    plt.savefig(out_folder / filename, dpi=300)
    plt.close()
    
    print(f"Operational cost heatmap saved for {scenario} / {price_label}")


# ============================================================
# GENERATE OPERATIONAL COST HEATMAPS
# ============================================================

for label, op_df in [("High_Price", df_opcost_high), ("Low_Price", df_opcost_low)]:
    for scen in scenarios:
        make_opcost_heatmaps(
            op_df,
            scenario=scen,
            price_label=label,
            out_folder=get_heatmap_outfolder(
            heatmap_folder,
            scenario=scen,
            price_label=label))




# ============================================================
# ADDITIONAL INPUT FOR OPEX-BASED SUPPORT HEATMAPS
# ============================================================


path_opex_support = INPUT_DIR / "Res_Opex_Support_Hydrogen.xlsx"

df_opex_sup_high = pd.read_excel(path_opex_support, sheet_name="High_Price")
df_opex_sup_low  = pd.read_excel(path_opex_support, sheet_name="Low_Price")


def make_opex_support_heatmaps(df, scenario, price_label, out_folder):
    """
    Create heatmaps for Opex-based CfD support: low = yellow, high = red.
    """
    sns.set_theme(style="white")

    op_sup_map = df.pivot(index="CO2 Price", columns="CfD Price", values=scenario)

    plt.figure(figsize=(10, 7))
    sns.heatmap(op_sup_map, annot=True, fmt=".2f", cmap="YlOrRd")
    plt.title(f"Opex-Based Support [million £] for Hydrogen – {scenario} – {price_label}", fontsize=14)
    plt.xlabel("CfD Price")
    plt.ylabel("CO2 Price")
    plt.tight_layout()

    filename = f"Fig_opex_support_hyd_{SCENARIO_SHORT.get(scenario, scenario)}_{price_label}.png"
    plt.savefig(out_folder / filename, dpi=300)
    plt.close()

    print(f"Opex support heatmap saved for {scenario} / {price_label}")




# ============================================================ 
# GENERATE OPEX SUPPORT HEATMAPS
# ============================================================

for label, op_sup_df in [("High_Price", df_opex_sup_high), ("Low_Price", df_opex_sup_low)]:
    for scen in scenarios:
        make_opex_support_heatmaps(
            op_sup_df,
            scenario=scen,
            price_label=label,
            out_folder=get_heatmap_outfolder(
                heatmap_folder,
                scenario=scen,
                price_label=label))


# ============================================================
# ADDITIONAL INPUT FOR NPV HEATMAPS
# ============================================================


path_npv = INPUT_DIR / "Res_NPV.xlsx"

df_npv_high = pd.read_excel(path_npv, sheet_name="High_Price")
df_npv_low  = pd.read_excel(path_npv, sheet_name="Low_Price")


# ============================================================
# HEATMAP FUNCTION – NPV
# ============================================================

def make_npv_heatmaps(df, scenario, price_label, out_folder):
    """
    Create heatmaps for Net Present Value: low = yellow, high = red.
    """
    sns.set_theme(style="white")

    npv_map = df.pivot(index="CO2 Price", columns="CfD Price", values=scenario)

    plt.figure(figsize=(10, 7))
    sns.heatmap(npv_map, annot=True, fmt=".1f", cmap="YlOrRd")
    plt.title(f"NPV [billion £] – {scenario} – {price_label}", fontsize=14)
    plt.xlabel("CfD Price")
    plt.ylabel("CO2 Price")
    plt.tight_layout()

    filename = f"Fig_NPV_{SCENARIO_SHORT.get(scenario, scenario)}_{price_label}.png"
    plt.savefig(out_folder / filename, dpi=300)
    plt.close()

    print(f"NPV heatmap saved for {scenario} / {price_label}")


# ============================================================
# GENERATE NPV HEATMAPS
# ============================================================

for label, npv_df in [("High_Price", df_npv_high), ("Low_Price", df_npv_low)]:
    for scen in scenarios:
        make_npv_heatmaps(
            npv_df,
            scenario=scen,
            price_label=label,
            out_folder=get_heatmap_outfolder(
            heatmap_folder,
            scenario=scen,
            price_label=label))




# ============================================================
# ADDITIONAL INPUT FOR GREEN HYDROGEN RATIO HEATMAPS
# ============================================================

path_h2split = INPUT_DIR / "Res_P2G_G2G.xlsx"

df_h2_high = pd.read_excel(path_h2split, sheet_name="High_Price")
df_h2_low  = pd.read_excel(path_h2split, sheet_name="Low_Price")

# ============================================================
# HEATMAP FUNCTION FOR GREEN HYDROGEN RATIO
# ============================================================

def make_green_ratio_heatmaps(df, scenario, price_label, out_folder, folder_name):
    """
    Create heatmaps for the ratio of green hydrogen to total hydrogen.
    folder_name is 'BlueH2' or 'GreyH2' used in the title/filename.
    """
    sns.set_theme(style="white")
    
    # Columns for this scenario
    p2g_col = f"{scenario} - P2G"
    g2g_col = f"{scenario} - G2G"
    
    # Calculate green hydrogen ratio
    df_ratio = df.copy()
    df_ratio["green_ratio"] = df_ratio[p2g_col] / (df_ratio[p2g_col] + df_ratio[g2g_col])
    
    ratio_map = df_ratio.pivot(index="CO2 Price", columns="CfD Price", values="green_ratio")
    
    plt.figure(figsize=(10, 7))
    sns.heatmap(ratio_map, annot=True, fmt=".2f", cmap="YlGn")  # green = high ratio
    plt.title(f"Green H2 Ratio [Green/Total]  –  {folder_name} – {scenario} – {price_label}", fontsize=14)
    plt.xlabel("CfD Price")
    plt.ylabel("CO2 Price")
    plt.tight_layout()
    
    filename = f"Fig_green_H2_ratio_{SCENARIO_SHORT.get(scenario, scenario)}_{folder_name}_{price_label}.png"
    plt.savefig(out_folder / filename, dpi=300)
    plt.close()
    
    print(f"Green H2 ratio heatmap saved for {scenario} / {price_label} ({folder_name})")

# ============================================================
# DETERMINE HYDROGEN TYPE (Blue or Grey) BASED ON INPUT FOLDER
# ============================================================

if "Blue" in PI_CO2_CfD_folder:
    folder_name = "BlueH2"
else:
    folder_name = "GreyH2"

# ============================================================
# GENERATE GREEN HYDROGEN RATIO HEATMAPS
# ============================================================

for label, h2_df in [("High_Price", df_h2_high), ("Low_Price", df_h2_low)]:
    for scen in scenarios:
        make_green_ratio_heatmaps(
            h2_df,
            scenario=scen,
            price_label=label,
            out_folder=get_heatmap_outfolder(
            heatmap_folder,
            scenario=scen,
            price_label=label),
            folder_name=folder_name
        )


# ============================================================
# ADDITIONAL INPUT FOR NPV WITHOUT CfD HEATMAPS
# ============================================================

path_npv_wo_cfd = INPUT_DIR / "Res_NPV_without_CfD_H2.xlsx"

df_npv_wo_cfd_high = pd.read_excel(path_npv_wo_cfd, sheet_name="High_Price")
df_npv_wo_cfd_low  = pd.read_excel(path_npv_wo_cfd, sheet_name="Low_Price")


# ============================================================
# HEATMAP FUNCTION – NPV WITHOUT CfD
# ============================================================

def make_npv_wo_cfd_heatmaps(df, scenario, price_label, out_folder):
    """
    Create heatmaps for Net Present Value WITHOUT CfD.
    """
    sns.set_theme(style="white")

    npv_map = df.pivot(index="CO2 Price", columns="CfD Price", values=scenario)

    plt.figure(figsize=(10, 7))
    sns.heatmap(npv_map, annot=True, fmt=".1f", cmap="YlOrRd")
    plt.title(f"NPV without CfD_H2 [billion £] – {scenario} – {price_label}", fontsize=14)
    plt.xlabel("CfD Price")
    plt.ylabel("CO2 Price")
    plt.tight_layout()

    filename = f"Fig_NPV_wo_CfD_H2_{SCENARIO_SHORT.get(scenario, scenario)}_{price_label}.png"
    plt.savefig(out_folder / filename, dpi=300)
    plt.close()

    print(f"NPV without CfD heatmap saved for {scenario} / {price_label}")


# ============================================================
# GENERATE NPV WITHOUT CfD HEATMAPS
# ============================================================

for label, npv_df in [
    ("High_Price", df_npv_wo_cfd_high),
    ("Low_Price",  df_npv_wo_cfd_low),
]:
    for scen in scenarios:
        make_npv_wo_cfd_heatmaps(
            npv_df,
            scenario=scen,
            price_label=label,
            out_folder=get_heatmap_outfolder(
            heatmap_folder,
            scenario=scen,
            price_label=label))


# ============================================================
# ADDITIONAL INPUT FOR TOTAL CfD COST HEATMAPS
# ============================================================

path_total_cfd_cost = INPUT_DIR / "Res_Total_CfD_cost.xlsx"

df_total_cfd_cost_high = pd.read_excel(path_total_cfd_cost, sheet_name="High_Price")
df_total_cfd_cost_low  = pd.read_excel(path_total_cfd_cost, sheet_name="Low_Price")


# ============================================================
# HEATMAP FUNCTION – TOTAL CfD COST
# ============================================================

def make_total_cfd_cost_heatmaps(df, scenario, price_label, out_folder):
    
    """
    Create heatmaps for Total CfD cost.
    Higher cost = worse (red), lower cost = better (yellow).
    """
    sns.set_theme(style="white")

    cost_map = df.pivot(index="CO2 Price", columns="CfD Price", values=scenario)

    plt.figure(figsize=(10, 7))
    sns.heatmap(cost_map, annot=True, fmt=".1f", cmap="YlOrRd")
    plt.title(f"Total CfD Cost [billion £] – {scenario} – {price_label}", fontsize=14)
    plt.xlabel("CfD Price")
    plt.ylabel("CO2 Price")
    plt.tight_layout()

    filename = f"Fig_Total_CfD_cost_{SCENARIO_SHORT.get(scenario, scenario)}_{price_label}.png"
    plt.savefig(out_folder / filename, dpi=300)
    plt.close()

    print(f"Total CfD cost heatmap saved for {scenario} / {price_label}")


# ============================================================
# GENERATE TOTAL CfD COST HEATMAPS
# ============================================================

for label, cfd_df in [
    ("High_Price", df_total_cfd_cost_high),
    ("Low_Price",  df_total_cfd_cost_low),
]:
    for scen in scenarios:
        make_total_cfd_cost_heatmaps(
            cfd_df,
            scenario=scen,
            price_label=label,
            out_folder=get_heatmap_outfolder(
        heatmap_folder,
        scenario=scen,
        price_label=label))
        
        
        
        
# Input Excel file for MAC
path_mac = INPUT_DIR / "Res_Marginal_Abatement_Cost.xlsx"

df_mac_high = pd.read_excel(path_mac, sheet_name="High_Price")
df_mac_low  = pd.read_excel(path_mac, sheet_name="Low_Price")


def make_mac_heatmaps(df, scenario, price_label, out_folder):
    """
    Create heatmaps for Marginal Abatement Cost [£/tCO2].
    Lower cost = green, higher cost = red.
    """
    sns.set_theme(style="white")
    
    mac_map = df.pivot(index="CO2 Price", columns="CfD Price", values=scenario)
    
    plt.figure(figsize=(10, 7))
    sns.heatmap(mac_map, annot=True, fmt=".1f", cmap="RdYlGn_r")  # reversed so low=green, high=red
    plt.title(f"Marginal Abatement Cost [£/tCO2] – {scenario} – {price_label}", fontsize=14)
    plt.xlabel("CfD Price")
    plt.ylabel("CO2 Price")
    plt.tight_layout()
    
    filename = f"Fig_MAC_{SCENARIO_SHORT.get(scenario, scenario)}_{price_label}.png"
    plt.savefig(out_folder / filename, dpi=300)
    plt.close()
    
    print(f"MAC heatmap saved for {scenario} / {price_label}")


for label, mac_df in [("High_Price", df_mac_high), ("Low_Price", df_mac_low)]:
    for scen in scenarios:
        make_mac_heatmaps(
            mac_df,
            scenario=scen,
            price_label=label,
            out_folder=get_heatmap_outfolder(
                heatmap_folder,
                scenario=scen,
                price_label=label
            )
        )
