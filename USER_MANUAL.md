# ChemVille User Manual

A practical guide to configuring, running, observing, and evaluating ChemVille simulations.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Configuring a Run](#2-configuring-a-run)
3. [Starting a Run](#3-starting-a-run)
4. [Monitoring Live](#4-monitoring-live)
5. [Replaying a Completed Run](#5-replaying-a-completed-run)
6. [Exporting to MP4](#6-exporting-to-mp4)
7. [Evaluating Results](#7-evaluating-results)
8. [Reference: Step Count Calculator](#8-reference-step-count-calculator)
9. [Reference: File Locations](#9-reference-file-locations)

---

## 1. Prerequisites

### Python environment
All commands assume you are using the project's virtual environment. Activate it once per terminal session:

```bash
cd /path/to/ChemVille
source venv/bin/activate
```

Or prefix every `python3` call with `venv/bin/python3`.

### API key
Your OpenAI API key must be present in **two files** (never committed to git):

| File | Field |
|------|-------|
| `reverie/backend_server/utils.py` | `openai_api_key = "sk-..."` |
| `openai_config.json` (repo root) | `"model-key"` and `"embeddings-key"` |

### Cost cap
Set your spend limit in `openai_config.json`:
```json
"cost-upperbound": 15.0
```
The simulation will abort if this limit is reached. Adjust before long runs.

---

## 2. Configuring a Run

### 2.1 Choose your agent team

The **base simulation folder** is:
```
environment/frontend_server/storage/base_chemville_all_19/
```

The active agent list is defined in `reverie/meta.json` inside that folder:

```json
{
  "persona_names": [
    "Samira Reininger",
    "Erick Gruetzberger",
    "Rongzhen Yang",
    "Lilly Florentino",
    "Alex Tyman",
    "Yuri Zuckermann",
    "Lionel Wittinger"
  ]
}
```

To change who participates:
- **Remove** a name from `persona_names` to exclude them from the run (their folder stays intact).
- **Add** a name (must have a corresponding `personas/{Name}/` folder with `bootstrap_memory/scratch.json`) to include them.
- Minimum recommended: the 7 core agents above (professors + postdocs + PhDs).

> Note: If you add agents from the full roster (Laura Stevens, Tyler Zhao, etc.), make sure their `scratch.json` exists first — ask Claude to generate it before running.

### 2.2 Set the research goal

Edit `environment/frontend_server/storage/base_chemville_all_19/scenario.json`:

```json
{
  "research_goal": "Give the SMILES output of an antibiotic scaffold targeting S. aureus. It should be active, non-toxic and novel (i.e. not reported in literature).",
  "scenario_name": "antibiotic_discovery_run_01"
}
```

- `research_goal` is injected into every agent's daily planning prompt. Change it to switch research scenarios.
- `scenario_name` is a label for your own records — it does not affect agent behavior.

### 2.3 Set the simulation duration

Duration is controlled by the `--steps` argument at run time. Each step = 10 simulated seconds.

| Duration | Steps |
|----------|-------|
| 20 steps (validation test) | `20` |
| 1 simulated day | `8640` |
| 2 simulated days | `17280` |
| 1 simulated week | `60480` |

See [Section 8](#8-reference-step-count-calculator) for a full reference.

### 2.4 Set the simulation start date

Edit `environment/frontend_server/storage/base_chemville_all_19/reverie/meta.json`:

```json
{
  "start_date": "September 1, 2025",
  "curr_time": "September 1, 2025, 00:00:00"
}
```

---

## 3. Starting a Run

All backend commands must be run from `reverie/backend_server/`:

```bash
cd reverie/backend_server
```

### 3.1 Headless run (no browser, fastest)

Use this for overnight runs or when you only want the data:

```bash
venv/bin/python3 automatic_execution.py \
  --origin base_chemville_all_19 \
  --target chemville_run_01 \
  --steps 17280 \
  --ui None \
  --load_history ./environment/frontend_server/static_dirs/assets/chemville/agent_history_init_n18.csv
```

- `--origin`: the base folder to fork from (always `base_chemville_all_19` for a fresh run)
- `--target`: name prefix for the output run (output folders will be `chemville_run_01-s-0-0-200`, etc.)
- `--steps`: total steps to run
- `--ui None`: no browser opened
- `--load_history`: seeds agent memories on the first step only

The simulation **auto-saves every 200 steps** and is **fully resumable** — if it crashes, just rerun with `--origin` pointing to the last saved checkpoint folder.

### 3.2 Live run (browser observation)

See [Section 4](#4-monitoring-live) — requires the frontend server to also be running.

### 3.3 Resuming a crashed or paused run

Find the last saved checkpoint folder:
```bash
ls environment/frontend_server/storage/ | grep chemville_run_01
# e.g. chemville_run_01-s-3-600-800
```

Resume from it (no `--load_history` needed — memories are already in the saved state):
```bash
venv/bin/python3 automatic_execution.py \
  --origin chemville_run_01-s-3-600-800 \
  --target chemville_run_01 \
  --steps 17280 \
  --ui None
```

---

## 4. Monitoring Live

### Step 1 — Start the frontend server

Open a **separate terminal**:

```bash
cd environment/frontend_server
../../venv/bin/python3 manage.py runserver 8000
```

Leave this running.

### Step 2 — Start the backend with UI enabled

In another terminal, from `reverie/backend_server/`:

```bash
venv/bin/python3 automatic_execution.py \
  --origin base_chemville_all_19 \
  --target chemville_run_01 \
  --steps 17280 \
  --ui True \
  --load_history ./environment/frontend_server/static_dirs/assets/chemville/agent_history_init_n18.csv
```

### Step 3 — Open the simulator

Navigate to: **http://localhost:8000/simulator_home**

You will see all agents moving on the ChemVille map in real time. Each agent shows:
- An emoji above their head indicating their current activity
- A description of what they are doing and where (visible on click or hover)

> Note: In live mode all agents share the same default sprite. Per-character sprites appear only in replay mode.

---

## 5. Replaying a Completed Run

### Start the frontend server (if not already running)

```bash
cd environment/frontend_server
../../venv/bin/python3 manage.py runserver 8000
```

### Open the replay

Navigate to: **http://localhost:8000/replay/\<sim_name\>/0**

Replace `<sim_name>` with the final checkpoint folder name, e.g.:

```
http://localhost:8000/replay/chemville_run_01-s-8-1600-1800/0
```

To find the final checkpoint:
```bash
ls environment/frontend_server/storage/ | grep chemville_run_01 | sort | tail -1
```

In replay mode:
- Each agent appears with their **assigned character sprite**
- You can **scrub through time** using the playback controls
- Agent descriptions and chat logs are visible

---

## 6. Exporting to MP4

> **Status: Planned (Phase 1.9).** Not yet implemented. This section describes the intended workflow once `reverie/export_video.py` is built.

### Planned workflow

```bash
# From repo root
python3 reverie/export_video.py \
  --sim_name chemville_run_01-s-8-1600-1800 \
  --fps 10 \
  --output exports/chemville_run_01.mp4
```

This will:
1. Start a headless browser pointed at the replay page
2. Screenshot each step
3. Encode the screenshots into an MP4 using ffmpeg

### In the meantime

Use a screen recorder (QuickTime on macOS: `Cmd+Shift+5`) while the replay plays in your browser.

---

## 7. Evaluating Results

> **Status: Planned (Phase 3).** Not yet implemented. This section describes the intended workflow once `reverie/backend_server/evaluation/evaluate_run.py` is built.

### What the evaluation does

- Loads a completed simulation
- Interviews each agent with a standard set of research questions
- Produces a structured JSON report per agent
- Optionally compares two runs side by side

### Planned command

```bash
python evaluate_run.py \
  --sim_code chemville_run_01-s-8-1600-1800 \
  --output_path reports/
```

### Standard interview questions

Each agent will be asked:
1. What have you been working on in the lab this week?
2. What experiments or analyses did you complete?
3. What were your most interesting findings or challenges?
4. How does your work relate to the lab's research goal?
5. What are your next steps?
6. Who did you collaborate with, and what did you learn from them?

### Reading agent state now (without evaluation runner)

While Phase 3 is not built, you can inspect agent state directly:

**Daily plans and reflections:**
```bash
cat environment/frontend_server/storage/<sim_name>/personas/<Name>/bootstrap_memory/associative_memory/nodes.json | python3 -m json.tool
```

**Movement and activity log:**
```bash
cat environment/frontend_server/storage/<sim_name>/movement/<step>.json | python3 -m json.tool
```

**What an agent is currently doing:**
Each step's movement file contains for every agent:
- `description`: e.g. `"analyzing candidate scaffolds (pharmacophore annotation) @ chemville:Lab1:Theory:desk"`
- `pronunciatio`: emoji representing the activity
- `chat`: conversation transcript if the agent was talking to someone

---

## 8. Reference: Step Count Calculator

| Simulated time | Steps | Real time (approx.) |
|----------------|-------|---------------------|
| 1 hour | 360 | ~3 min |
| 6 hours | 2160 | ~18 min |
| 1 day | 8640 | ~72 min |
| 2 days | 17280 | ~2.5 hours |
| 3 days | 25920 | ~3.5 hours |
| 1 week | 60480 | ~8.5 hours |

Real-time estimates assume ~0.5s per LLM step on gpt-4o-mini with 7 agents. Actual time depends on API latency.

### Cost estimate (gpt-4o-mini, 7 agents)

| Duration | Estimated cost |
|----------|----------------|
| 20 steps (test) | ~$0.01 |
| 1 day | ~$2–4 |
| 2 days | ~$4–8 |
| 1 week | ~$14–25 |

---

## 9. Reference: File Locations

| File | Purpose |
|------|---------|
| `openai_config.json` | API key, model, cost cap — **never commit** |
| `reverie/backend_server/utils.py` | API key + path config — **never commit** |
| `environment/frontend_server/storage/base_chemville_all_19/` | Bootstrap data for all runs (source of truth) |
| `environment/frontend_server/storage/base_chemville_all_19/reverie/meta.json` | Agent list, start date |
| `environment/frontend_server/storage/base_chemville_all_19/scenario.json` | Research goal |
| `environment/frontend_server/storage/base_chemville_all_19/personas/<Name>/bootstrap_memory/scratch.json` | Character bio, current state, lifestyle |
| `environment/frontend_server/static_dirs/assets/chemville/agent_history_init_n18.csv` | Day-1 whisper memories |
| `environment/frontend_server/storage/<sim_name>/movement/` | Per-step activity log (replay data) |
| `reverie/backend_server/cost-logs/` | LLM cost logs per run |
| `CHEMVILLE_PLAN.md` | Full development plan with status markers |
