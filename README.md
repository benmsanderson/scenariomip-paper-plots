# ScenarioMIP Extension: FaIR Climate Simulations

This repository reproduces the plots for the published ScenarioMIP CMIP7 description paper:

Van Vuuren, D. P., O'Neill, B. C., Tebaldi, C., Sanderson, B. M., Chini, L. P., Friedlingstein, P., Hasegawa, T., Riahi, K., Govindasamy, B., Bauer, N., Eyring, V., Fall, C. M. N., Frieler, K., Gidden, M. J., Gohar, L. K., Högner, A., Jones, A. D., Kikstra, J., King, A., Knutti, R., Kriegler, E., Lawrence, P., Lennard, C., Lowe, J., Mathison, C., Mehmood, S., Nicholls, Z., Prado, L. F., Zhang, Q., Rose, S. K., Ruane, A. C., Sandstad, M., Schleussner, C.-F., Seferian, R., Sillmann, J., Smith, C., Sörensson, A. A., Panickal, S., Tachiiri, K., Vaughan, N., Vishwanathan, S. S., Yokohata, T., Zecchetto, M., and Ziehn, T.: The Scenario Model Intercomparison Project for CMIP7 (ScenarioMIP-CMIP7), Geosci. Model Dev., 19, 2627–2656, https://doi.org/10.5194/gmd-19-2627-2026, 2026.

The repo contains emissions scenario data and a Jupyter notebook that runs the [FaIR v2.2](https://github.com/OMS-NetZero/FAIR) climate model over extended timelines (1750-2501) across seven ScenarioMIP-aligned scenarios (VL through HL).

## Requirements

- Python 3.10+

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/benmsanderson/scenariomip-paper-plots.git
cd scenariomip-paper-plots
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Register the kernel with Jupyter

```bash
python -m ipykernel install --user --name scenariomip --display-name "ScenarioMIP"
```

### 5. Launch JupyterLab

```bash
jupyter lab
```

## Pipeline

| Stage | File | Description |
|---|---|---|
| Simulation | [scripts/run_fair_simulations.py](scripts/run_fair_simulations.py) | Runs FaIR v2.2 over 1750–2501 across the seven scenarios and saves the ensemble (emissions, CO₂e, temperature, CO₂ concentration, forcing) to `data/fair-outputs/fair_run.nc`. The full AR6 calibration is fetched from Zenodo on first run. |
| Plotting (module) | [scripts/plotting.py](scripts/plotting.py) | Single source of truth for figure code. Exposes `load_data()` and `fig_*` functions used by both the notebook and the CLI. |
| Plotting (CLI) | [scripts/make_plots.py](scripts/make_plots.py) | Renders every figure to `plots/` without Jupyter. Auto-invokes the simulation script if `fair_run.nc` is missing. |
| Plotting (notebook) | [notebooks/0505_extensions_plotting.ipynb](notebooks/0505_extensions_plotting.ipynb) | Interactive view of the same figures, for inspecting intermediates and tweaking styling. |

### Render all figures (no Jupyter)

```bash
.venv/bin/python scripts/make_plots.py
.venv/bin/python scripts/make_plots.py --out-dir /tmp/plots
```

### Run the FaIR simulation manually

```bash
.venv/bin/python scripts/run_fair_simulations.py            # skip if output exists
.venv/bin/python scripts/run_fair_simulations.py --force    # always re-run
.venv/bin/python scripts/run_fair_simulations.py --memory-limited  # 5-member test ensemble
```

The plotting notebook is regenerated from
[scripts/build_plotting_notebook.py](scripts/build_plotting_notebook.py).
For substantive plot changes, edit `scripts/plotting.py` (shared by both
the notebook and the CLI); the builder script is only for adding /
removing notebook cells.

## Data

See [data/README.md](data/README.md) for a description of the input files. All data files are version-controlled directly in this repository. FaIR calibration parameters are also fetched from Zenodo at runtime. The full dataset (including regional files) is archived on Zenodo.

## Scenarios

Seven scenarios are included, spanning a wide range of future emissions pathways:

| ID | Description |
|---|---|
| VL | Very low emissions |
| LN | Low-negative emissions |
| L | Low emissions |
| ML | Medium-low emissions |
| M | Medium emissions |
| H | High emissions |
| HL | High-legacy / very high emissions |
