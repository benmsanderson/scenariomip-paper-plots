"""Build notebooks/0505_extensions_plotting.ipynb from cell source strings.

Run with the portable venv (ScenarioMIP_final/.venv); only depends on
nbformat. Re-run after editing this file to regenerate the notebook.

    .venv/bin/python scripts/build_plotting_notebook.py
"""

from pathlib import Path

import nbformat as nbf

REPO_ROOT = Path(__file__).parent.parent
OUT_PATH = REPO_ROOT / "notebooks" / "0505_extensions_plotting.ipynb"


CELLS: list[tuple[str, str]] = [
    (
        "markdown",
        """\
# ScenarioMIP — extension plots

Produces every figure for the ScenarioMIP description paper from:

* **CSV emissions** in `data/` — gross positive, AFOLU, energy & industry,
  plus CDR sub-components.
* **FaIR ensemble outputs** at `data/fair-outputs/fair_run.nc` — produced
  by `scripts/run_fair_simulations.py`. If the file is missing, the
  load-data cell below invokes the script automatically (~5 min for the
  full AR6 ensemble).

Figures rendered:

1. CO₂ flux extensions (annual + cumulative, with CDR breakdown).
2. Pre-run CO₂ and GHG emissions summaries.
3. Temperature & emissions (GHG with uncertainty band + temperature 2000–2150).
4. Multi-panel diagnostics (8 panels: emissions, forcing, concentration, temperature).
5. Temperature ECDFs at 2100, 2300, and peak warming.
""",
    ),
    (
        "markdown",
        "## Imports",
    ),
    (
        "code",
        """\
import subprocess
import sys
from pathlib import Path

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
""",
    ),
    (
        "markdown",
        "## Load data",
    ),
    (
        "code",
        """\
REPO_ROOT = Path.cwd().parent
DATA_DIR = REPO_ROOT / "data"
PLOTS_DIR = REPO_ROOT / "plots"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

raw_output = pd.read_csv(DATA_DIR / "continuous_emissions_timeseries_1750_2500.csv")
raw_output = raw_output.set_index(["model", "scenario", "region", "workflow", "variable", "unit"])
raw_output.columns = raw_output.columns.astype(float)

cdr_components = pd.read_csv(DATA_DIR / "cdr_components_future.csv")
cdr_components = cdr_components.set_index(["model", "scenario", "variable"])
cdr_components.columns = cdr_components.columns.astype(float)

# FaIR ensemble outputs — run the simulation if the NetCDF is missing.
fair_path = DATA_DIR / "fair-outputs" / "fair_run.nc"
if not fair_path.exists():
    print(f"{fair_path} not found -- running FaIR simulation (this takes a few minutes)...")
    subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "run_fair_simulations.py")],
        check=True,
    )
fair = xr.open_dataset(fair_path)

print(f"raw_output:     {raw_output.shape}, years {raw_output.columns.min():.0f}-{raw_output.columns.max():.0f}")
print(f"cdr_components: {cdr_components.shape}, years {cdr_components.columns.min():.0f}-{cdr_components.columns.max():.0f}")
print(f"fair:           {dict(fair.sizes)}")
""",
    ),
    (
        "markdown",
        "## Scenario metadata and colors",
    ),
    (
        "code",
        """\
# CO2-flux figure constants (reserves are Gt CO2 cumulative ceilings).
BASELINE_YEAR = 2100
CDR_LIMIT = -1460
PROVED_FOSSIL_RESERVES = 2032 + 2400
PROBABLE_FOSSIL_RESERVES = 8036 + 2400

# Long IAM-scenario names in the raw_output CSV mapped to short codes.
scenario_model_match = {
    "VL": ["SSP1 - Very Low Emissions", "REMIND-MAgPIE 3.5-4.11", "tab:blue"],
    "LN": ["SSP2 - Low Overshoot_a", "AIM 3.0", "tab:cyan"],
    "L":  ["SSP2 - Low Emissions", "MESSAGEix-GLOBIOM-GAINS 2.1-M-R12", "tab:green"],
    "ML": ["SSP2 - Medium-Low Emissions", "COFFEE 1.6", "tab:pink"],
    "M":  ["SSP2 - Medium Emissions", "IMAGE 3.4", "tab:purple"],
    "H":  ["SSP3 - High Emissions", "GCAM 8s", "tab:red"],
    "HL": ["SSP5 - Medium-Low Emissions_a", "WITCH 6.0", "tab:brown"],
}
scenario_to_code = {info[0]: code for code, info in scenario_model_match.items()}

# Component colors for the CO2-flux figure.
COLORS = {
    "Gross_Positive":      "#8B4513",
    "BECCS":               "#BEDB3C",
    "DACCS":               "#DF23D9",
    "Ocean":               "#4D3EBD",
    "Enhanced_Weathering": "#A6A6A6",
    "AFOLU":               "#51E390",
}

# Per-scenario line colors (used in all FaIR-output plots).
snames = ["VL", "LN", "L", "ML", "M", "H", "HL"]
scenario_colors = {
    "HL": "#E744F6",
    "H":  "#a41212",
    "M":  "#fc7b03",
    "ML": "#dec820",
    "L":  "#20A359",
    "LN": "#22e5db",
    "VL": "#16188F",
}
""",
    ),
    (
        "markdown",
        "## CO₂ flux figure — plot helpers",
    ),
    (
        "code",
        """\
def _series_by_scenario_variable(df, scenario, variable, years):
    \"\"\"Sum rows matching (scenario, variable) and return a 1D ndarray over `years`.\"\"\"
    mask = (
        (df.index.get_level_values("scenario") == scenario)
        & (df.index.get_level_values("variable") == variable)
    )
    sub = df.loc[mask, years]
    if sub.empty:
        return np.zeros(len(years))
    return sub.sum(axis=0).values


def _cdr_future_padded(scenario, variable, all_years, future_years):
    \"\"\"CDR sub-component: zero over the historical period, future values after.\"\"\"
    mask = (
        (cdr_components.index.get_level_values("scenario") == scenario)
        & (cdr_components.index.get_level_values("variable") == variable)
    )
    vals = cdr_components.loc[mask, future_years].sum(axis=0).values
    return np.concatenate([np.zeros(len(all_years) - len(future_years)), vals])


def _get_scenario_data(scenario, all_years, future_years):
    \"\"\"Assemble all series needed to plot one scenario, in Gt CO2 / yr.\"\"\"
    return {
        "gross_pos": _series_by_scenario_variable(raw_output, scenario, "Emissions|CO2|Gross Positive Emissions", all_years) / 1000,
        "fossil":    _series_by_scenario_variable(raw_output, scenario, "Emissions|CO2|Energy and Industrial Processes", all_years) / 1000,
        "afolu":     _series_by_scenario_variable(raw_output, scenario, "Emissions|CO2|AFOLU", all_years) / 1000,
        "beccs":     _cdr_future_padded(scenario, "Emissions|CO2|BECCS",               all_years, future_years) / 1000,
        "daccs":     _cdr_future_padded(scenario, "Emissions|CO2|Direct Air Capture",  all_years, future_years) / 1000,
        "ocean":     _cdr_future_padded(scenario, "Emissions|CO2|Ocean",               all_years, future_years) / 1000,
        "ew":        _cdr_future_padded(scenario, "Emissions|CO2|Enhanced Weathering", all_years, future_years) / 1000,
    }


def _plot_annual(ax, data, years):
    afolu_pos = np.clip(data["afolu"], 0, None)
    afolu_neg = np.clip(data["afolu"], None, 0)

    y1_pos = data["gross_pos"]
    y2_pos = y1_pos + afolu_pos
    y1_neg = data["beccs"]
    y2_neg = y1_neg + data["daccs"]
    y3_neg = y2_neg + data["ocean"]
    y4_neg = y3_neg + data["ew"]
    y5_neg = y4_neg + afolu_neg

    ax.fill_between(years, 0,       y1_pos, alpha=0.7, color=COLORS["Gross_Positive"],      label="Gross FF&I")
    ax.fill_between(years, y1_pos,  y2_pos, alpha=0.7, color=COLORS["AFOLU"],               label="AFOLU")
    ax.fill_between(years, 0,       y1_neg, alpha=0.7, color=COLORS["BECCS"],               label="BECCS")
    ax.fill_between(years, y1_neg,  y2_neg, alpha=0.7, color=COLORS["DACCS"],               label="DACCS")
    ax.fill_between(years, y2_neg,  y3_neg, alpha=0.7, color=COLORS["Ocean"],               label="Ocean CDR")
    ax.fill_between(years, y3_neg,  y4_neg, alpha=0.7, color=COLORS["Enhanced_Weathering"], label="Enhanced Weathering")
    ax.fill_between(years, y4_neg,  y5_neg, alpha=0.7, color=COLORS["AFOLU"])

    ax.plot(years, data["fossil"] + data["afolu"], "k-", linewidth=2, alpha=0.8, label="Net Emissions")


def _plot_cumulative(ax, data, years):
    afolu_pos = np.clip(data["afolu"], 0, None)
    afolu_neg = np.clip(data["afolu"], None, 0)

    gp_cum    = np.cumsum(data["gross_pos"])
    afolu_cum = np.cumsum(afolu_pos + afolu_neg)
    beccs_cum = np.cumsum(data["beccs"])
    daccs_cum = np.cumsum(data["daccs"])
    ocean_cum = np.cumsum(data["ocean"])
    ew_cum    = np.cumsum(data["ew"])

    y1_pos = gp_cum
    y2_pos = y1_pos + afolu_cum
    y1_neg = beccs_cum
    y2_neg = y1_neg + daccs_cum
    y3_neg = y2_neg + ocean_cum
    y4_neg = y3_neg + ew_cum

    ax.fill_between(years, 0,      y1_pos, alpha=0.7, color=COLORS["Gross_Positive"])
    ax.fill_between(years, y1_pos, y2_pos, alpha=0.7, color=COLORS["AFOLU"])
    ax.fill_between(years, 0,      y1_neg, alpha=0.7, color=COLORS["BECCS"])
    ax.fill_between(years, y1_neg, y2_neg, alpha=0.7, color=COLORS["DACCS"])
    ax.fill_between(years, y2_neg, y3_neg, alpha=0.7, color=COLORS["Ocean"])
    ax.fill_between(years, y3_neg, y4_neg, alpha=0.7, color=COLORS["Enhanced_Weathering"])

    fossil_cum = np.cumsum(data["fossil"])
    ax.plot(years, fossil_cum + afolu_cum, "k-", linewidth=2, alpha=0.8, label="Net Emissions")


def _format_axes(ax_annual, ax_cumul, scenario, row_index, all_years):
    for ax, suffix in [(ax_annual, "Annual Gross Fluxes"), (ax_cumul, "Cumulative Gross Fluxes")]:
        ax.set_title(f"{scenario_to_code[scenario]} {suffix}", fontsize=12, fontweight="bold")
        ax.set_xlabel("Year", fontsize=11)
        ax.set_ylabel(
            "CO₂ Flux (Gt CO₂/yr)" if ax is ax_annual else "Cumulative CO₂ (Gt CO₂)",
            fontsize=11,
        )
        ax.tick_params(axis="both", which="major", labelsize=10)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(all_years[0], all_years[-1])
        ax.axvline(x=BASELINE_YEAR, color="red", linestyle="--", alpha=0.5, linewidth=1)
        ax.axhline(y=0, color="black", linestyle="-", alpha=0.3, linewidth=2)

        if ax is ax_cumul:
            ax.axhline(y=CDR_LIMIT,                color="green", linestyle="-",  alpha=0.3, linewidth=3, label="Cumulative CDR limit")
            ax.axhline(y=PROVED_FOSSIL_RESERVES,   color="red",   linestyle="-",  alpha=0.3, linewidth=3, label="Proved Fossil Reserves")
            ax.axhline(y=PROBABLE_FOSSIL_RESERVES, color="red",   linestyle="--", alpha=0.3, linewidth=3, label="Proved + Probable Fossil Reserves")
        if row_index == 0:
            ax.legend(loc="upper right", fontsize=9)


def plot_comprehensive_co2_analysis_with_history():
    all_years = sorted(c for c in raw_output.columns if isinstance(c, (int, float)))
    future_years = sorted(c for c in cdr_components.columns if isinstance(c, (int, float)))

    scenarios = sorted(
        set(raw_output.index.get_level_values("scenario"))
        & set(cdr_components.index.get_level_values("scenario"))
    )
    n = len(scenarios)
    print(f"Plotting {n} scenarios across {len(all_years)} years")

    fig, axes = plt.subplots(n, 2, figsize=(10, 3 * n))
    if n == 1:
        axes = axes.reshape(1, -1)

    years_arr = np.array(all_years)
    for i, scenario in enumerate(scenarios):
        data = _get_scenario_data(scenario, all_years, future_years)
        _plot_annual(axes[i, 0], data, years_arr)
        _plot_cumulative(axes[i, 1], data, years_arr)
        _format_axes(axes[i, 0], axes[i, 1], scenario, i, all_years)

    plt.tight_layout()
    return fig
""",
    ),
    (
        "markdown",
        "## Figure 1 — CO₂ flux extensions",
    ),
    (
        "code",
        """\
fig = plot_comprehensive_co2_analysis_with_history()
out_path = PLOTS_DIR / "co2_extensions_with_history.png"
fig.savefig(out_path, dpi=150, bbox_inches="tight")
print(f"Saved {out_path}")
plt.show()
""",
    ),
    (
        "markdown",
        """\
## FaIR-output figures — shared accessors

Convenience helpers so the FaIR plots read like the original notebook.
""",
    ),
    (
        "code",
        """\
timepoints = fair["emissions"].timepoints.values
timebounds = fair["temperature"].timebounds.values
scenarios = fair["temperature"].scenario.values

emissions = fair["emissions"]                  # (timepoints, scenario, specie)
co2e = fair["co2e"]                            # (timepoints, scenario)  -- tonnes CO2e / yr
temperature = fair["temperature"]              # (timebounds, scenario, config)  -- layer 0
co2_concentration = fair["co2_concentration"]  # (timebounds, scenario, config)
forcing_sum = fair["forcing_sum"]              # (timebounds, scenario, config)

# Anomaly relative to 1850-1900 mean.
T_BASELINE = temperature.sel(timebounds=np.arange(1850, 1902)).mean(dim="timebounds")
temperature_anom = temperature - T_BASELINE
""",
    ),
    (
        "markdown",
        "## Figure 2 — CO₂ emissions (annual + cumulative)",
    ),
    (
        "code",
        """\
fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(14, 5))
for scenario in scenarios:
    co2_total = emissions.sel(scenario=scenario, specie="CO2 FFI") + emissions.sel(scenario=scenario, specie="CO2 AFOLU")
    ax[0].plot(timepoints, co2_total, label=scenario, color=scenario_colors[scenario])
    ax[1].plot(timepoints, co2_total.cumsum(), label=scenario, color=scenario_colors[scenario])
ax[0].set_ylabel("CO$_2$ emissions, GtCO$_2$ yr$^{-1}$")
ax[1].set_ylabel("Cumulative CO$_2$ emissions, GtCO$_2$")
for a in ax:
    a.axhline(ls=":", color="k", lw=0.5)
    a.legend()
    a.grid()
fig.savefig(PLOTS_DIR / "co2_emissions.png")
plt.show()
""",
    ),
    (
        "markdown",
        "## Figure 3 — CO₂ and total GHG emissions (CO₂e)",
    ),
    (
        "code",
        """\
fig, ax = plt.subplots(1, 2, figsize=(14, 5))
for scenario in scenarios:
    co2_total = emissions.sel(scenario=scenario, specie="CO2 FFI") + emissions.sel(scenario=scenario, specie="CO2 AFOLU")
    ax[0].plot(timepoints, co2_total, label=scenario, color=scenario_colors[scenario])
    ax[1].plot(timepoints, co2e.sel(scenario=scenario) / 1e6, label=scenario, color=scenario_colors[scenario])

ax[0].set_ylabel("CO$_2$ emissions, GtCO$_2$ yr$^{-1}$")
ax[0].set_xlim(2015, 2300)
ax[0].set_ylim(-40, 100)
ax[0].legend()

ax[1].set_ylabel("GHG emissions, GtCO$_2$eq yr$^{-1}$")
ax[1].set_xlim(2015, 2300)
ax[1].set_ylim(-50, 100)

for a in ax:
    a.axhline(ls=":", color="k", lw=0.5)
    a.grid()
fig.savefig(PLOTS_DIR / "ghg_emissions.png")
plt.show()
""",
    ),
    (
        "markdown",
        """\
## Figure 4 — Temperature & emissions (2000–2150)

Two panels: GHG emissions (CO₂e) with an uncertainty band derived from
the scenario spread, and warming relative to 1850–1900 (33rd–66th
percentile across the ensemble).
""",
    ),
    (
        "code",
        """\
fig, ax = plt.subplots(1, 2, figsize=(12, 5))

# Uncertainty band scaled by the high-vs-low scenario gap.
unc = np.tanh((co2e.sel(scenario=scenarios[0]) - co2e.sel(scenario=scenarios[-2])) / 1e6 / 10) * 8

for scenario in scenarios:
    ax[0].fill_between(
        timebounds[:351],
        co2e.sel(scenario=scenario)[:351] / 1e6 - unc[:351],
        co2e.sel(scenario=scenario)[:351] / 1e6 + unc[:351],
        color=scenario_colors[scenario], lw=0, alpha=0.3,
    )
    ax[0].fill_between(
        timepoints[350:],
        co2e.sel(scenario=scenario)[350:] / 1e6 - unc[350:],
        co2e.sel(scenario=scenario)[350:] / 1e6 + unc[350:],
        color=scenario_colors[scenario], hatch="XXX", lw=0, alpha=0.1,
    )
    ax[0].plot(timepoints[:275], co2e.sel(scenario=scenario)[:275] / 1e6, color="k")

ax[0].text(2030, -39, "IAM generated \\nscenarios \\n(2025-2100)")
ax[0].text(2105, -39, "Priority extension\\nperiod \\n(2101-2150)")
ax[0].set_ylabel("GHG emissions, GtCO$_2$eq yr$^{-1}$")
ax[0].axhline(ls=":", color="k", lw=0.5)
ax[0].set_xlim(2000, 2150)
ax[0].set_ylim(-50, 100)
ax[0].grid()
ax[0].set_title("(a)")

for scenario in scenarios:
    ta = temperature_anom.sel(scenario=scenario)
    ax[1].fill_between(
        timebounds,
        ta.quantile(0.33, dim="config"),
        ta.quantile(0.66, dim="config"),
        color=scenario_colors[scenario], lw=0, alpha=0.3, label=scenario,
    )
# Historical (black band) from the last scenario in the loop -- temperature is the
# same for all scenarios over the historical period.
hist = temperature_anom.sel(scenario=scenarios[-1])
ax[1].fill_between(
    timebounds[:274],
    hist[:274].quantile(0.33, dim="config"),
    hist[:274].quantile(0.66, dim="config"),
    color="k", alpha=0.5,
)
ax[1].axhline(0, ls=":", color="k", lw=0.5)
ax[1].set_ylabel("Temperature above 1850-1900, K")
ax[1].set_ylim(0, 5)
ax[1].set_xlim(2000, 2150)
ax[1].grid()
ax[1].legend()
ax[1].set_title("(b)")

fig.savefig(PLOTS_DIR / "temperature_emis.png", dpi=600, bbox_inches="tight")
fig.savefig(PLOTS_DIR / "temperature_emis.pdf", format="pdf", bbox_inches="tight")
plt.show()
""",
    ),
    (
        "markdown",
        """\
## Figure 5 — Multi-panel diagnostics

Eight panels: CO₂ emissions (annual & cumulative), CH₄, sulfur, GHG
totals, effective radiative forcing, CO₂ concentration, and temperature.
Black overlay marks the historical period (1750–2022).
""",
    ),
    (
        "code",
        """\
fig, ax = plt.subplots(nrows=4, ncols=2, figsize=(14, 16))
ax = ax.flatten()
hist_slice = slice(0, 273)

# Panel 0: annual CO2
for scenario in scenarios:
    co2_total = emissions.sel(scenario=scenario, specie="CO2 FFI") + emissions.sel(scenario=scenario, specie="CO2 AFOLU")
    ax[0].plot(timepoints, co2_total, label=scenario, color=scenario_colors[scenario])
ax[0].plot(timepoints[hist_slice], co2_total[hist_slice], color="k")
ax[0].set_ylabel("CO$_2$ emissions, GtCO$_2$ yr$^{-1}$")
ax[0].legend()

# Panel 1: cumulative CO2
for scenario in scenarios:
    co2_total = emissions.sel(scenario=scenario, specie="CO2 FFI") + emissions.sel(scenario=scenario, specie="CO2 AFOLU")
    ax[1].plot(timepoints, co2_total.cumsum(), color=scenario_colors[scenario])
ax[1].plot(timepoints[hist_slice], co2_total.cumsum()[hist_slice], color="k")
ax[1].set_ylabel("Cumulative CO$_2$ emissions, GtCO$_2$")

# Panel 2: CH4
for scenario in scenarios:
    ax[2].plot(timepoints, emissions.sel(scenario=scenario, specie="CH4"), color=scenario_colors[scenario])
ax[2].plot(timepoints[hist_slice], emissions.sel(scenario=scenarios[-1], specie="CH4")[hist_slice], color="k")
ax[2].set_ylabel("CH$_4$ emissions, MtCH$_4$ yr$^{-1}$")

# Panel 3: SO2
for scenario in scenarios:
    ax[3].plot(timepoints, emissions.sel(scenario=scenario, specie="Sulfur"), color=scenario_colors[scenario])
ax[3].plot(timepoints[hist_slice], emissions.sel(scenario=scenarios[-1], specie="Sulfur")[hist_slice], color="k")
ax[3].set_ylabel("SO$_2$ emissions, MtS yr$^{-1}$")

# Panel 4: GHG (CO2e)
for scenario in scenarios:
    ax[4].plot(timepoints, co2e.sel(scenario=scenario) / 1e6, color=scenario_colors[scenario])
ax[4].plot(timepoints[hist_slice], co2e.sel(scenario=scenarios[-1])[hist_slice] / 1e6, color="k")
ax[4].set_ylabel("GHG emissions, GtCO$_2$eq yr$^{-1}$")

# Panel 5: effective radiative forcing
for scenario in scenarios:
    fs = forcing_sum.sel(scenario=scenario)
    ax[5].fill_between(
        timebounds, fs.quantile(0.05, dim="config"), fs.quantile(0.95, dim="config"),
        color=scenario_colors[scenario], lw=0, alpha=0.1,
    )
    ax[5].plot(
        timebounds[274:], fs.median(dim="config")[274:],
        path_effects=[pe.Stroke(linewidth=4, foreground="w", alpha=0.8), pe.Normal()],
        color=scenario_colors[scenario],
    )
    ax[5].plot(timebounds, fs.median(dim="config"), color=scenario_colors[scenario])
ax[5].plot(timebounds[hist_slice], fs.median(dim="config")[hist_slice], color="k")
ax[5].set_ylabel("Effective radiative forcing, W m$^{-2}$")

# Panel 6: CO2 concentration
for scenario in scenarios:
    co2c = co2_concentration.sel(scenario=scenario)
    ax[6].fill_between(
        timebounds, co2c.quantile(0.05, dim="config"), co2c.quantile(0.95, dim="config"),
        color=scenario_colors[scenario], lw=0, alpha=0.1,
    )
    ax[6].plot(
        timebounds[274:], co2c.median(dim="config")[274:],
        path_effects=[pe.Stroke(linewidth=5, foreground="w", alpha=0.8), pe.Normal()],
        color=scenario_colors[scenario],
    )
    ax[6].plot(timebounds, co2c.median(dim="config"), color=scenario_colors[scenario])
ax[6].plot(timebounds[hist_slice], co2c.median(dim="config")[hist_slice], color="k")
ax[6].axhline(0, ls=":", color="k", lw=0.5)
ax[6].set_ylabel("Atmospheric CO$_2$ concentration, ppm")
ax[6].set_ylim(0, 1500)

# Panel 7: temperature anomaly (vs 1850-1900)
for scenario in scenarios:
    ta = temperature_anom.sel(scenario=scenario)
    ax[7].fill_between(
        timebounds, ta.quantile(0.05, dim="config"), ta.quantile(0.95, dim="config"),
        color=scenario_colors[scenario], lw=0, alpha=0.1,
    )
    ax[7].plot(
        timebounds[274:], ta.median(dim="config")[274:],
        path_effects=[pe.Stroke(linewidth=4, foreground="w", alpha=0.8), pe.Normal()],
        color=scenario_colors[scenario],
    )
    ax[7].plot(timebounds, ta.median(dim="config"), label=scenario, color=scenario_colors[scenario])
ax[7].plot(timebounds[hist_slice], ta.median(dim="config")[hist_slice], color="k")
ax[7].axhline(0, ls=":", color="k", lw=0.5)
ax[7].set_ylabel("Temperature above 1850-1900, K")
ax[7].set_ylim(-1, 8)
ax[7].legend()

for a in ax:
    a.axhline(ls=":", color="k", lw=0.5)
    a.grid()

fig.savefig(PLOTS_DIR / "extensions.png", dpi=600, bbox_inches="tight")
fig.savefig(PLOTS_DIR / "extensions.pdf", format="pdf", bbox_inches="tight")
plt.show()
""",
    ),
    (
        "markdown",
        """\
## Figure 6 — Temperature ECDFs

Cumulative probability across the ensemble at 2100, 2300, and peak
warming (relative to year 1850).
""",
    ),
    (
        "code",
        """\
fig, ax = plt.subplots(3, 1, figsize=(12, 8))
ax = ax.flatten()

T_2100 = temperature.sel(timebounds=2100) - temperature.sel(timebounds=1850)
T_2300 = temperature.sel(timebounds=2300) - temperature.sel(timebounds=1850)
T_peak = temperature.max(dim="timebounds") - temperature.sel(timebounds=1850)

panels = [
    (T_2100, "Temperature anomaly in 2100 relative to 1850, K"),
    (T_2300, "Temperature anomaly in 2300 relative to 1850, K"),
    (T_peak, "Maximum temperature anomaly relative to 1850, K"),
]

for a, (T, title) in zip(ax, panels):
    for scenario in scenarios:
        a.ecdf(T.sel(scenario=scenario), color=scenario_colors[scenario], label=scenario)
    a.set_title(title)
    a.set_xlabel("K")
    a.set_ylabel("Cumulative probability")
    a.set_yticks([0.1, 0.25, 0.33, 0.5, 0.66, 0.75, 0.9])
    a.set_xticks(np.array([-0.5, 0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]) * 2)
    a.set_xlim([-1, 10])
    a.legend(loc="upper right")
    a.grid()

plt.tight_layout()
plt.show()
""",
    ),
]


def main() -> None:
    nb = nbf.v4.new_notebook()
    nb.metadata = {
        "kernelspec": {"display_name": "ScenarioMIP", "language": "python", "name": "scenariomip"},
        "language_info": {"name": "python"},
    }
    cells = []
    for kind, source in CELLS:
        if kind == "markdown":
            cells.append(nbf.v4.new_markdown_cell(source))
        elif kind == "code":
            cells.append(nbf.v4.new_code_cell(source))
        else:
            raise ValueError(kind)
    nb.cells = cells
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w") as f:
        nbf.write(nb, f)
    print(f"Wrote {OUT_PATH} ({len(cells)} cells)")


if __name__ == "__main__":
    main()
