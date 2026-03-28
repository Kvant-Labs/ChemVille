#!/bin/bash
# Run a 48-hour (17280 step) headless ChemVille simulation.
# Execute from reverie/backend_server/:
#   bash run_48h.sh

HIST=./environment/frontend_server/static_dirs/assets/chemville/agent_history_init_n18.csv

../../venv/bin/python3 automatic_execution.py \
  --origin base_chemville_all_19 \
  --target chemville_48h_run_01 \
  --steps 17280 \
  --ui None \
  --load_history "$HIST"
