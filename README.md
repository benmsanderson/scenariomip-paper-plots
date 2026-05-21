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

## Notebooks

| Notebook | Description |
|---|---|
| [0504_extension_fair_simulations.ipynb](notebooks/0504_extension_fair_simulations.ipynb) | Runs FaIR v2.2 with extended emissions scenarios and produces temperature and concentration projections |
| [0505_extensions_plotting.ipynb](notebooks/0505_extensions_plotting.ipynb) | Reproduces the comprehensive CO₂ flux figure (annual + cumulative, gross positive, AFOLU, CDR breakdown) for the seven scenarios |

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
