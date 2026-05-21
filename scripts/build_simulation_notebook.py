"""Build notebooks/0504_extension_fair_simulations.ipynb from cell source strings.

Run with the portable venv (ScenarioMIP_final/.venv); only depends on
nbformat. Re-run after editing this file to regenerate the notebook.

    .venv/bin/python scripts/build_simulation_notebook.py
"""

from pathlib import Path

import nbformat as nbf

REPO_ROOT = Path(__file__).parent.parent
OUT_PATH = REPO_ROOT / "notebooks" / "0504_extension_fair_simulations.ipynb"


CELLS: list[tuple[str, str]] = [
    (
        "markdown",
        """\
# FaIR climate model simulations — extended scenarios

Runs the [FaIR v2.2](https://github.com/OMS-NetZero/FAIR) climate model
over 1750–2501 across seven ScenarioMIP-aligned scenarios (VL through HL)
and saves the ensemble outputs to NetCDF for downstream plotting in
`0505_extensions_plotting.ipynb`.

This notebook is **simulation only** — no plots are produced here.
The figures in the paper are rendered in 0505 from the saved outputs.

**Steps**
1. Define the time horizon, scenarios, and species.
2. Load the AR6-calibrated parameter ensemble (Zenodo).
3. Fill emissions + volcanic/solar forcing from CSV.
4. Compute total GHG emissions in CO₂-equivalent (AR6 GWP100).
5. Run FaIR.
6. Save outputs to `data/fair-outputs/fair_run.nc`.
""",
    ),
    (
        "markdown",
        "## Imports",
    ),
    (
        "code",
        """\
import os

import numpy as np
import pandas as pd
import pooch
import xarray as xr
from fair import FAIR
from fair.interface import initialise
from fair.io import read_properties
""",
    ),
    (
        "markdown",
        """\
## Configuration

Set `memory_limited = True` to run only 5 ensemble members (for quick
testing). The full AR6 ensemble (~1500 members) is fetched from Zenodo
on first run.
""",
    ),
    (
        "code",
        """\
memory_limited = False
""",
    ),
    (
        "markdown",
        "## Define scenarios, time horizon, and species",
    ),
    (
        "code",
        """\
snames = ["VL", "LN", "L", "ML", "M", "H", "HL"]

f = FAIR()
f.define_time(1750, 2501, 1)
f.define_scenarios(snames)

species, properties = read_properties("../data/fair-inputs/species_configs_properties_1.4.1.csv")
f.define_species(species, properties)
f.ch4_method = "Thornhill2021"
""",
    ),
    (
        "markdown",
        "## Load the calibrated parameter ensemble",
    ),
    (
        "code",
        """\
if not memory_limited:
    ZENODO_DOI = "10.5281/zenodo.7112539"
    FILE_NAME = "calibrated_constrained_parameters.csv"
    FILE_HASH = "md5:8a70a3fb05d0e0cf35e136de382582a5"

    data_pooch = pooch.create(
        path="../data/fair-inputs",
        base_url=f"doi:{ZENODO_DOI}",
        version="1.5.0",
        registry={FILE_NAME: FILE_HASH},
    )
    local_file_path = data_pooch.fetch(FILE_NAME)
    print(f"Config file: {local_file_path}")
""",
    ),
    (
        "code",
        """\
if memory_limited:
    df_configs = pd.read_csv("../data/fair-inputs/1.5.0/calibrated_constrained_parameters_short.csv", index_col=0)
else:
    df_configs = pd.read_csv("../data/fair-inputs/1.5.0/calibrated_constrained_parameters.csv", index_col=0)

f.define_configs(df_configs.index)
f.allocate()
print(f"Ensemble size: {len(df_configs)} configs")
""",
    ),
    (
        "markdown",
        "## Fill emissions and natural forcing",
    ),
    (
        "code",
        """\
f.fill_from_csv(
    forcing_file="../data/fair-inputs/volcanic_solar.csv",
    emissions_file="../data/fair-inputs/emissions_1750-2500.csv",
)

# Solar forcing is handled separately by FaIR (zeroed in the input file).
for s in f.scenarios:
    f.forcing.loc[dict(scenario=s, specie="Solar")] = 0
""",
    ),
    (
        "markdown",
        """\
## CO₂-equivalent emissions

Aggregate all GHG emissions to CO₂-equivalents using 100-year Global
Warming Potentials (AR6 GWP100, mass-adjusted).
""",
    ),
    (
        "code",
        """\
gwpmat = pd.read_csv("../data/fair-inputs/gwp_mass_adjusted_100y.csv", index_col=0)

co2eo = f.emissions.sel(specie="CO2 FFI")[:, :, 0].copy() * 0
for specie in f.emissions.specie.values:
    gwp = gwpmat["ar6_gwp_mass_adjusted"].get(specie, np.nan)
    if not np.isnan(gwp):
        co2eo = co2eo + f.emissions.sel(specie=specie)[:, :, 0] * gwp / 1e6
co2e = co2eo * 1e6  # tonnes CO2e per year
""",
    ),
    (
        "markdown",
        "## Run FaIR",
    ),
    (
        "code",
        """\
f.fill_species_configs("../data/fair-inputs/species_configs_properties_1.4.1.csv")
if memory_limited:
    f.override_defaults("../data/fair-inputs/1.5.0/calibrated_constrained_parameters_short.csv")
else:
    f.override_defaults("../data/fair-inputs/1.5.0/calibrated_constrained_parameters.csv")

initialise(f.concentration, f.species_configs["baseline_concentration"])
initialise(f.forcing, 0)
initialise(f.temperature, 0)
initialise(f.cumulative_emissions, 0)
initialise(f.airborne_emissions, 0)
initialise(f.ocean_heat_content_change, 0)

f.run()
""",
    ),
    (
        "markdown",
        """\
## Save outputs

Bundle the variables needed by `0505_extensions_plotting.ipynb` into a
single NetCDF file. Emissions are sliced at `config=0` (they are
config-invariant); climate variables retain the full ensemble.
""",
    ),
    (
        "code",
        """\
out = xr.Dataset(
    {
        "emissions": f.emissions.isel(config=0, drop=True),
        "co2e": co2e,
        "temperature": f.temperature.isel(layer=0, drop=True),
        "co2_concentration": f.concentration.sel(specie="CO2", drop=True),
        "forcing_sum": f.forcing_sum.rename("forcing_sum"),
    }
)

encoding = {v: {"dtype": "float32", "zlib": True, "complevel": 4} for v in out.data_vars}

out_dir = "../data/fair-outputs"
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "fair_run.nc")
out.to_netcdf(out_path, encoding=encoding)

print(f"Saved {out_path}")
print(out)
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
