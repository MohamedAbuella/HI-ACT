# -*- coding: utf-8 -*-
"""
Compute average MACH per CO2 and CfD corridors
Focus: High RES–High H2 only
Options: Exclude CO2=0 if needed
Includes: Mean, Std Dev, Range, Total Avg/Std/Range
"""

import pandas as pd
from pathlib import Path

# -----------------------------
# USER SETTINGS
# -----------------------------
INPUT_FILE = Path("Output/CfD_GreyH2_Cooperative/Summary_Results_0_250_100_500/Res_Marginal_Abatement_Cost_Hydrogen.xlsx")

SHEETS = ["High_Price", "Low_Price"]
COLUMN_H2 = "High RES–High H2"

# Define corridors (boundaries)
CO2_CORRIDORS = [(100, 200), (200, 300), (300, 400), (400, 500)]
CFD_CORRIDORS = [(0, 50), (50, 100), (100, 200), (200, 250)]

EXCLUDE_CO2_ZERO = True  # Set False to include CO2=0

# EXCLUDE_CO2_ZERO = False  # Set False to include CO2=0


# -----------------------------
# READ DATA
# -----------------------------
df_high = pd.read_excel(INPUT_FILE, sheet_name=SHEETS[0])
df_low = pd.read_excel(INPUT_FILE, sheet_name=SHEETS[1])

# Clean numeric columns
def clean_mach(df):
    df = df.copy()
    df[COLUMN_H2] = pd.to_numeric(df[COLUMN_H2], errors='coerce')
    df["CO2 Price"] = pd.to_numeric(df["CO2 Price"], errors='coerce')
    df["CfD Price"] = pd.to_numeric(df["CfD Price"], errors='coerce')
    return df

df_high = clean_mach(df_high)
df_low = clean_mach(df_low)

# Optionally remove CO2=0
if EXCLUDE_CO2_ZERO:
    df_high = df_high[df_high["CO2 Price"] != 0]
    df_low = df_low[df_low["CO2 Price"] != 0]

# -----------------------------
# FUNCTION TO COMPUTE STATISTICS FOR CORRIDORS
# -----------------------------
def corridor_stats(df, column, var="CO2"):
    """
    df: dataframe
    column: column to analyze (MACH)
    var: "CO2" or "CfD"
    returns: dict of stats {corridor: {"mean":, "std":, "range":}}
    """
    result = {}
    if var=="CO2":
        corridors = CO2_CORRIDORS
        price_col = "CO2 Price"
    else:
        corridors = CFD_CORRIDORS
        price_col = "CfD Price"

    for low, high in corridors:
        values = df[(df[price_col] >= low) & (df[price_col] <= high)][column].dropna()
        avg = values.mean() if not values.empty else None
        std = values.std() if not values.empty else None
        rng = values.max() - values.min() if not values.empty else None
        result[f"{low}-{high}"] = {"mean": avg, "std": std, "range": rng}
    return result

# -----------------------------
# COMPUTE STATS
# -----------------------------
co2_stats_high = corridor_stats(df_high, COLUMN_H2, var="CO2")
co2_stats_low = corridor_stats(df_low, COLUMN_H2, var="CO2")

cfd_stats_high = corridor_stats(df_high, COLUMN_H2, var="CfD")
cfd_stats_low = corridor_stats(df_low, COLUMN_H2, var="CfD")

# -----------------------------
# BUILD TABLES
# -----------------------------
def build_table(stats_low, stats_high):
    table = []
    for corridor in stats_high.keys():
        mean_low = stats_low[corridor]["mean"]
        mean_high = stats_high[corridor]["mean"]
        total_mean = (mean_low + mean_high)/2 if (mean_low is not None and mean_high is not None) else None

        std_low = stats_low[corridor]["std"]
        std_high = stats_high[corridor]["std"]
        total_std = (std_low + std_high)/2 if (std_low is not None and std_high is not None) else None

        range_low = stats_low[corridor]["range"]
        range_high = stats_high[corridor]["range"]
        total_range = (range_low + range_high)/2 if (range_low is not None and range_high is not None) else None

        table.append({
            "Corridor": corridor,
            "Avg MACH Low Price": mean_low,
            "Avg MACH High Price": mean_high,
            "Total Avg": total_mean,
            "Std Dev Low Price": std_low,
            "Std Dev High Price": std_high,
            "Total Std Dev": total_std,
            "Range Low Price": range_low,
            "Range High Price": range_high,
            "Total Range": total_range
        })
    return pd.DataFrame(table)

co2_table = build_table(co2_stats_low, co2_stats_high)
cfd_table = build_table(cfd_stats_low, cfd_stats_high)

# -----------------------------
# OUTPUT
# -----------------------------
print("=== CO2 Corridors MACH Stats ===")
print(co2_table.to_string(index=False))
print("\n=== CfD Corridors MACH Stats ===")
print(cfd_table.to_string(index=False))

# Save to Excel
OUTPUT_FILE = INPUT_FILE.parent / "MACH_Corridor_Averages_Stats.xlsx"
with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
    co2_table.to_excel(writer, sheet_name="CO2_Corridors", index=False)
    cfd_table.to_excel(writer, sheet_name="CfD_Corridors", index=False)

print("\nSaved enhanced corridor averages with Std Dev and Range to:", OUTPUT_FILE)
