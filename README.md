
# Thesis Title

This repository contains the code developed as part of the MSc thesis in [Electronic Systems](https://www.en.aau.dk/education/master/electronic-systems) at Aalborg University:

**Title:** "Title"

**Author:** Christian Kjærsgaard Nielsen

## Overview

```text
├── napkin/           # Exploratory calculations
├── framework/        # Multihop simulation framework
├── configuration.yml # Simulation settings for LoRa and network
├── pyproject.toml    # Project configurations
└── uv.lock           # Locked dependencies
```

## Requirements
- Python 3.14+
- [uv](https://docs.astral.sh/uv/) package manager

## Setup

Clone the repository and install dependencies:
```bash
git clone https://github.com/CKjaer/district-heating-multihop-sim.git
cd district-heating-multihop-sim
uv sync
```
Activate the virtual environment in macOS/Linux:
```bash
source .venv/bin/activate
```
Or in Windows
```bash
source .venv\Scripts\activate
```

Run simulation scripts using `uv`
```bash
uv run python simulations/<simulation>.py
```
View plots and collected statistics in the `/results` folder

## Contact

For questions regarding the code or the thesis, please contact:

<christiankjaernielsen@gmail.com>

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgements
This repo was inspired by [DRAMCO/LoRa-multihop-sim](https://github.com/DRAMCO/)
