# POSG_SmartGrid
Securing Smart Grid using Game theory

## Overview
This repository implements a partially observable stochastic game (POSG) model for attacker/defender interactions in a smart grid context.

## `app.py`
`app.py` is a Streamlit-based interface for the POSG simulator. It provides:

- a live dashboard for attacker and defender scores
- stage visualization for Recon, Compromise, Weaponize, and Execute
- network signal selection and threat-level display
- a simple payoff matrix view
- attacker/defender action selection and step execution

The UI uses `POSGEnvironment` from `posg_engine.py` and maps high-level stage labels to simplified attacker/defender actions.

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```
