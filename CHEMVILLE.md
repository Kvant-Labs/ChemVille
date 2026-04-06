# ChemVille

A generative-agent chemistry research simulation built on [Generative Agents](https://arxiv.org/abs/2304.03442). Seven agents (2 professors, 3 postdocs, 2 PhD students) pursue a shared research goal — currently: **"Give the SMILES output of an antibiotic scaffold targeting S. aureus. It should be active, non-toxic, and novel."**

**LLM:** `gpt-4o-mini` for all reasoning + `text-embedding-3-small` for embeddings (OpenAI only, no multi-model routing).

---

## Setup

```bash
# 1. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Create OpenAI config
cat > reverie/backend_server/openai_config.json << 'EOF'
{"model": "gpt-4o-mini", "api_key": "sk-..."}
EOF

# 3. Install playwright for video export (optional)
playwright install chromium
```

---

## Running a Simulation

All run commands must be executed from `reverie/backend_server/`:

```bash
cd reverie/backend_server
```

### Quick smoke test (200 steps ≈ first 30 sim-minutes)
```bash
python automatic_execution.py \
  --origin base_chemville_all_19 \
  --target my_test_run \
  --steps 200 \
  --ui None
```

### Full 2-day run (17280 steps, unattended)
```bash
python automatic_execution.py \
  --origin base_chemville_all_19 \
  --target chemville_2day_run \
  --steps 17280 \
  --ui None
```

### Resuming a stopped run
Find the last complete segment folder (e.g. `chemville_2day_run-s-56-10998-11198`), then:
```bash
python automatic_execution.py \
  --origin chemville_2day_run-s-56-10998-11198 \
  --target chemville_2day_run-resume-01 \
  --steps <remaining_steps> \
  --ui None
```

### Live UI mode (requires frontend server in another terminal)
```bash
# Terminal 1:
cd environment/frontend_server
python manage.py runserver 8000
# Then open: http://localhost:8000/simulator_home

# Terminal 2:
cd reverie/backend_server
python automatic_execution.py \
  --origin base_chemville_all_19 \
  --target my_live_run \
  --steps 1000 \
  --ui True
```

### Step count reference
| Duration | Steps |
|----------|-------|
| 1 hour sim | 360 |
| 1 day (7am–midnight, 17h) | 6120 |
| 1 full day (24h) | 8640 |
| 2 full days | 17280 |

---

## Monitoring a Run

Segments are saved every 200 steps to:
```
environment/frontend_server/storage/<run_name>-s-<idx>-<from>-<to>/
```

Check what step the run is at:
```bash
ls environment/frontend_server/storage/ | grep <run_name> | sort -t'-' -k5 -n | tail -3
```

Check if still running:
```bash
pgrep -fl "automatic_execution"
```

---

## Replaying a Run

With the frontend server running:
```
http://localhost:8000/replay/<segment_name>/0/
```

Example: `http://localhost:8000/replay/chemville_2day_run-s-57-11198-11398/0/`

---

## Auditing a Completed Run

The last segment contains all movement files from step 0 onward (each segment forks from the previous).

```bash
# Basic audit
python reverie/audit_run.py --sim chemville_2day_run-s-57-11198-11398

# With LLM narrative summary (calls gpt-4o-mini, ~$0.01)
python reverie/audit_run.py --sim chemville_2day_run-s-57-11198-11398 --llm-summary

# Save to file
python reverie/audit_run.py --sim chemville_2day_run-s-57-11198-11398 --llm-summary --out exports/audit.md
```

The audit reports: tool calls (with SMILES), agent conversations, compressed activity timelines, and an optional GPT-4o-mini narrative summary.

---

## Exporting to MP4

Requires: frontend server running + ffmpeg + playwright.

```bash
# From repo root:
python reverie/export_video.py \
  --sim_name chemville_2day_run-s-57-11198-11398 \
  --output exports/chemville_2day.mp4 \
  --fps 24
```

**Note:** Captures one frame per step via headless Playwright. At ~0.5s/frame, 11287 steps ≈ 1.5 hours capture time. For a quick preview, use `--start_step 2000` to skip early steps or export a subset segment.

---

## Changing the Research Goal

Edit `environment/frontend_server/storage/base_chemville_all_19/scenario.json`:
```json
{
  "research_goal": "Your new goal here — be specific and mention SMILES if you want output in that format.",
  "scenario_name": "my_scenario_01"
}
```

The research goal is injected into daily planning prompts AND task decomposition prompts for all eligible agents.

---

## Character Roster

### Active agents (7 core personas)

| Name | Role | Living Area | Focus |
|------|------|-------------|-------|
| Samira Reininger | Professor (Computational) | Dorm4:A | ML/cheminformatics, dataset curation, model benchmarking |
| Erick Gruetzberger | Professor (Experimental) | Dorm4:B | Synthesis routes, medicinal chemistry, lab coordination |
| Rongzhen Yang | Postdoc 1 | Dorm1:B | ML activity prediction (random forest, GNN) |
| Lilly Florentino | Postdoc 2 | Dorm1:B | Toxicity counterscreening (hERG, cytotoxicity) |
| Alex Tyman | Postdoc 3 | Dorm3:B | Pharmacophore annotation, scaffold shortlisting |
| Yuri Zuckermann | PhD 1 | Dorm1:C | Naive Bayes / ML models, competes with Lionel |
| Lionel Wittinger | PhD 2 | Dorm1:C | SAR literature review, cross-checks pharmacophore claims |

### Full 19-character roster (inactive — require additional bootstrap setup)

| Name | Role | Living Area |
|------|------|-------------|
| Laura Stevens | PhD 3 | Dorm1:C |
| Amelia Hayes | PhD 4 | Dorm2:B |
| Tyler Zhao | PhD 5 | Dorm2:C |
| Tara Olson | Student 1 | Dorm2:C |
| Naima Jamila | Student 2 | Dorm2:C |
| Henry Scott | Student 3 | Dorm2:B |
| Sophia Cortez | Student 4 | Dorm2:B |
| Sarah Robin | Cafeteria Worker | Cafeteria |
| Marco Mäder | Janitor | Office/Classroom |
| Clyde Hoffmann | Lazy Student | Dorm2:B |
| Joel Dubois | Principal | Office3 |
| (unnamed) | — | — |

---

## Lab Tools (Chemistry APIs)

Tool calls are automatic when agents work at computers, lab equipment, whiteboards, or desks. Three tools are available:

| Tool | API | Returns |
|------|-----|---------|
| `search_pubchem(compound)` | PubChem PUG REST | SMILES, formula, MW, InChIKey |
| `search_chembl(target)` | ChEMBL REST | Target name, organism, ChEMBL ID |
| `search_literature(query)` | Semantic Scholar | Paper titles, abstracts |

**Budget:** 10 calls per agent per simulated day (configurable in scenario.json: `"tool_call_budget_per_agent_per_day": 10`).

When a tool fires and returns SMILES, the agent's `currently` field is updated with the SMILES so it surfaces in subsequent conversations.

---

## Architecture Notes

### Tool call pipeline
```
Daily planning → Research goal injected
Task decomp → MANDATORY tool_call for chemistry subtasks (enforced by keyword auto-filler)
plan.py → queues pending_tool_call when agent is at a tool-capable game object
reverie.py → executes on tile arrival, stores result in a_mem + scratch.currently
Frontend → tool_call result appears in movement JSON, pronunciatio shows SMILES snippet
```

### Location system
- `persona.scratch.living_area` = `"chemville:Sector:Arena"` — where agent sleeps
- Sector selection: LLM → validated against accessible sectors → dorm guard rejects dormitory sectors for non-sleep tasks
- Arena selection: LLM → validated against accessible arenas in chosen sector
- Spawn tiles: defined in `matrix/special_blocks/spawning_location_blocks.csv`

### Sprite sheet
- `Character_Assets/tileset_characters.png`: 19 cols × 18 rows of 16×32px frames
- Frame formula: `col * 19 + dir * 4 + anim_frame` for walking; `col * 19 + 18` for sleeping
- `PERSONA_COL` in `main_script.html` maps each agent name → sprite column

### Map files
- **Source:** `environment/frontend_server/static_dirs/assets/chemville/visuals/chemville.tmx` (Tiled editor)
- **Export:** `chemville_16april.json` — loaded by Phaser.js frontend
- **Backend maze:** `matrix/maze/*.csv` — 144×96 grid used by Python pathfinding
- **Special blocks:** `matrix/special_blocks/*.csv` — maps tile IDs to world addresses

---

## Known Issues & Pending Fixes

### Code (done in last session)
- [x] Sleeping animation: frame 18 (rightmost column), regex `/sleeping|asleep|in bed/i`
- [x] Arena validation: fallback prevents KeyError crash
- [x] Tool registry: `search_chembl` added to all game objects
- [x] `pending_tool_calls` persisted in scratch.save/load
- [x] `last_tool_call_result` reset after writing to movement file
- [x] Mid-corridor stops: `act_path_set = True` when same arena
- [x] Tool call prompt: mandatory with auto-enforcer for chemistry keywords
- [x] SMILES propagation: `currently` updated after tool fires, pronunciatio shows snippet
- [x] Conversation prompt: agents instructed to cite SMILES from memories
- [x] Dorm routing guard: non-sleep tasks can't be assigned to dormitory sectors
- [x] Rongzhen Yang `living_area` changed from Dorm1:A (no spawn) to Dorm1:B

### Map (requires Tiled — manual)

> **How to install:** `brew install --cask tiled` or download from mapeditor.org  
> **Map file to open:** `environment/frontend_server/static_dirs/assets/chemville/visuals/chemville.tmx`  
> **After every Tiled edit:** re-export as `visuals/chemville_16april.json`, then run `python3 tools/regenerate_maze_csvs.py` from the repo root.

#### TODO 1 — Fix map dimensions (140×100 → 144×96)
The current Tiled map is 140×100 tiles but the backend maze CSVs expect 144×96.
1. In Tiled: `Map → Resize Map…` → set Width=144, Height=96, Offset X=0 Y=0
2. Check nothing is cut off at the bottom (southernmost rooms are at Y≈88, within 96)
3. Re-export JSON + run `regenerate_maze_csvs.py`

#### TODO 2 — Fix misplaced carpet tiles
The "Carpets in Dormatory" layer is correctly placed. The visual glitch is likely in another layer.
1. In Tiled, toggle layers on/off (eye icon) to isolate the problem layer
2. Check the **Rooms** and **Furniture** layers for dorm carpet tiles appearing outside dorm buildings
3. Select the offending layer, use Eraser tool (`E`) to remove misplaced tiles
4. Re-export JSON + run `regenerate_maze_csvs.py`

#### TODO 3 — Add Dorm1:A spawn tile (optional)
Rongzhen Yang was moved from Dorm1:A → Dorm1:B as a workaround (no spawn tile existed for Dorm1:A). To restore his intended room:
1. In Tiled, select the **Spawning Blocks** layer
2. Find Dorm1:A on the map (around X=88-110, Y=66-71; use Arena Blocks layer to see room labels)
3. Select the **blocks_3** tileset, pick an unused spawn tile, paint it in Dorm1:A center
4. Note the tile's local ID (shown in the status bar) — call it `N`
5. Add to `matrix/special_blocks/spawning_location_blocks.csv`: `N, chemville, Dorm1, A, sp-A`
6. In `storage/base_chemville_all_19/personas/Rongzhen Yang/bootstrap_memory/scratch.json` change `living_area` back to `"chemville:Dorm1:A"`
7. Re-export JSON + run `regenerate_maze_csvs.py`

#### TODO 4 — Missing spawns for inactive characters
These 8 characters need spawn tiles before they can be added to a run:
- Dorm1:C sp-B → Lionel Wittinger (only sp-A exists; Yuri uses it)
- Dorm1:C sp-C → Laura Stevens
- Dorm2:B sp-C → Henry Scott
- Dorm2:B sp-D → Sophia Cortez
- Dorm2:B sp-E → Clyde Hoffmann
- Cafeteria spawn → Sarah Robin (works there, no dorm)
- Office/Classroom spawn → Marco Mäder (janitor)
Same process as TODO 3: paint a new spawn tile in each room, add to `spawning_location_blocks.csv`.

### Not yet started
- [ ] Agent interview/evaluation system (Phase 3)
- [ ] Shared lab notebook across agents
- [ ] Full 19-agent run (12 characters still need bootstrap memory)

---

## Cost Estimates

Based on `openai-cost-logger` output from prior runs:
- 7 agents, 200 steps (smoke test): ~$0.15–0.25
- 7 agents, full day (8640 steps): ~$5–8
- 7 agents, 2-day run (17280 steps): ~$10–16
