"""
scenario_config.py

Loads a scenario.json file from the active simulation folder and exposes
the research goal as a module-level string injected into the planning prompts.

Expected scenario.json format:
{
  "research_goal": "Give the SMILES output of an antibiotic scaffold...",
  "scenario_name": "antibiotic_discovery_run_01"
}
"""
import json
import os

RESEARCH_GOAL: str = ""
SCENARIO_NAME: str = ""


def load(sim_folder: str) -> None:
  """Load scenario.json from sim_folder if it exists. Safe to call even if
  the file is absent — falls back to empty strings (no goal injected)."""
  global RESEARCH_GOAL, SCENARIO_NAME
  path = os.path.join(sim_folder, "scenario.json")
  if os.path.exists(path):
    with open(path) as f:
      data = json.load(f)
    RESEARCH_GOAL = data.get("research_goal", "")
    SCENARIO_NAME = data.get("scenario_name", "")
    print(f"(scenario_config): Loaded scenario '{SCENARIO_NAME}'")
    print(f"(scenario_config): Research goal: {RESEARCH_GOAL}")
  else:
    RESEARCH_GOAL = ""
    SCENARIO_NAME = ""
