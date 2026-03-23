# ChemVille Development Plan

A research simulation built on [Generative Agents](https://arxiv.org/abs/2304.03442), adapted for a chemistry university setting. Agents are professors, postdocs, PhD students, and staff who pursue real research goals, use chemistry databases, and can be interviewed about their work.

**LLM:** `gpt-4o-mini` for all calls + `text-embedding-3-small` for embeddings (OpenAI only).

---

## Status Legend
- `[ ]` Not started
- `[~]` In progress
- `[x]` Done
- `[?]` Needs input from user before proceeding

---

## Phase 1 — Run ChemVille with 19 agents and chemistry prompts

### 1.1 Fix spawn points
**File:** `environment/frontend_server/static_dirs/assets/chemville/matrix/special_blocks/spawning_location_blocks.csv`

The map is missing spawn tiles for several characters. Add the following entries (requires painting new tiles in Tiled first, or reusing nearby tile IDs):

- `[ ]` Dorm1:A — for Rongzhen Yang (no spawn exists at all for this arena)
- `[ ]` Dorm1:C sp-B — for Lionel Wittinger (only sp-A exists; Yuri, Lionel, Laura share this room)
- `[ ]` Dorm1:C sp-C — for Laura Stevens
- `[ ]` Dorm2:B sp-C — for Henry Scott (Tara and Naima occupy sp-A and sp-B)
- `[ ]` Dorm2:B sp-D — for Sophia Cortez
- `[ ]` Dorm2:B sp-E — for Clyde Hoffmann
- `[ ]` Cafeteria spawn — for Sarah Robin (she works there, no dorm)
- `[ ]` Office or Classroom spawn — for Marco Mäder (janitor, no dorm)

> Options: (A) Open `environment/frontend_server/static_dirs/assets/chemville/visuals/chemville.tmx` in Tiled, paint new Spawning Block tiles in those rooms, re-export the matrix CSVs. (B) Quick fix: assign Sarah and Marco `living_area` values pointing to an existing valid spawn (e.g. Cafeteria:cafe for Sarah) — the fallback routing will handle it without crashing.

---

### 1.2 Bootstrap all 19 persona directories
**New folder:** `environment/frontend_server/storage/base_chemville_all_19/`

Directory structure mirrors `base_chemville_isabella_maria_klaus/`. Required files per persona:
- `bootstrap_memory/scratch.json`
- `bootstrap_memory/spatial_memory.json` (copy from Isabella — full campus knowledge)
- `bootstrap_memory/associative_memory/nodes.json` (empty `{}`)
- `bootstrap_memory/associative_memory/embeddings.json` (empty `{}`)
- `bootstrap_memory/associative_memory/kw_strength.json` (copy template)

Plus root files:
- `reverie/meta.json` — lists all active persona names, start date, map name
- `environment/0.json` — initial (x, y) tile coordinates per persona

**Characters defined so far** (from `assets/ChemVille_Character_List.xlsx`):

| Name | Role | Age | Innate Traits | Living Area |
|------|------|-----|---------------|-------------|
| Samira Reininger | Theoretical Professor | 40 | Curious, Creative, Intelligent, Visionary, Quantum-romantic | Dorm4:A |
| Erick Gruetzberger | Experimental Professor | 52 | Skilled, Inquisitive, Ambitious, Relentless, Pragmatic | Dorm4:B |
| Rongzhen Yang | Postdoc 1 | 26 | Knowledgeable, Stressed, Competent, Solution-oriented | Dorm1:A |
| Lilly Florentino | Postdoc 2 | 28 | Interdisciplinary, Creative, Pragmatic, Competitive | Dorm1:B |
| Alex Tyman | Postdoc 3 | 31 | Wise, Friendly, Mentor, Bold strategist, Dry humor | Dorm3:B |
| Yuri Zuckermann | PhD 1 | 22 | Bold, Analytical, Outgoing, Perfection seeker, Optimistic | Dorm1:C |
| Lionel Wittinger | PhD 2 | 24 | Soft-spoken, Strategic, Sceptical, Practical thinker, Poetic | Dorm1:C |
| Laura Stevens | PhD 3 | 23 | Problem-solver, Logic-driven, Ambitious, Optimistic | Dorm1:C |
| Amelia Hayes | PhD 4 | 22 | Visionary, Eco-driven, Hands-on, Lab rat, Storyteller | Dorm3:C |
| Tyler Zhao | PhD 5 | 26 | Laid back, Out-of-the-box-thinker, Stress resistant, Jazz-lover | Dorm3:C |
| Tara Olson | Student 1 | 19 | Analytical, Creative, Detail oriented, Problem solver | Dorm2:B |
| Naima Jamila | Student 2 | 18 | Ambitious, Curious, Eager, Learning by doing | Dorm2:B |
| Henry Scott | Student 3 | 20 | Focused, Mindful, Constant learner, Library rat | Dorm2:B |
| Sophia Cortez | Student 4 | 19 | Organized, Detective-like, Team player, Classical music-enjoyer | Dorm2:B |
| Sarah Robin | Cafeteria Staff | 43 | Communicative, Loving, Wise, Caring, Funny | Cafeteria |
| Marco Mäder | Janitor Staff | 64 | Grumpy, Technical, Genius, Misunderstood, Sports expert | Campus |
| Clyde Hoffmann | Surfer Student | 24 | Relaxed, Hedonistic, Occasional high-performer, Beach lover | Dorm2:B |
| Joel Dubois | Rector | 55 | Strategic, Diplomatic, Avoidant, Well-meaning, Science-interested | Dorm4:C |

**Still needed from user before generating scratch.json files:**

- `[x]` **Research scenario** — "Give the SMILES output of an antibiotic scaffold targeting S.aureus. It should be active, non-toxic and novel (i.e. not reported in literature)."
- `[x]` **Subset for first run** — Core team of 7: Samira Reininger, Erick Gruetzberger, Rongzhen Yang, Lilly Florentino, Alex Tyman, Yuri Zuckermann, Lionel Wittinger
- `[~]` **Per-character bios / current state / lifestyle / relationships** — collecting group by group (see details below)

> **Process:** We will go role-group by role-group (professors → postdocs → PhDs → students → staff), presenting what's defined and asking for missing details before writing any file.

#### Professors ✓
**Samira Reininger**
- *Bio:* Trained in quantum chemistry at ETH Zürich. Runs a computational group focused on cheminformatics and ML for science. Eager to curate datasets and train ML models to predict chemical properties. Careful about benchmarking, insists on choosing the right models.
- *Currently:* Curating a training dataset of antibiotic SMILES with activity labels from ChEMBL, preparing to train a graph neural network for activity prediction.
- *Lifestyle:* Wake 7:00am, bed 11:30pm, lunch at cafeteria ~12:30, dinner at cafeteria or skips ~7pm, late-night reading/coding habit.
- *Relationship:* Formally collaborates with Erick as two independent PIs with the same overarching goal. Can seek each other's input when needed. Postdocs interact more informally.

**Erick Gruetzberger**
- *Bio:* Spent 15 years in industry at Novartis before returning to academia. Reputation for rigorously reproducible synthesis protocols. Always looks out for chemical rigour and practical relevance in his own and others' work.
- *Currently:* Reviewing the synthesis feasibility of a list of candidate scaffolds his group proposed, flagging ones with impractical reaction steps.
- *Lifestyle:* Wake 6:30am, bed 10:30pm, lunch at cafeteria ~12:00, dinner at cafeteria/home ~6:30pm, early morning strict schedule.
- *Relationship:* Formally collaborates with Samira. Postdocs interact more informally during coffee chats.

#### Postdocs ✓
**Rongzhen Yang** (Samira's group, blue)
- *Bio:* Focused on antibiotic activity prediction ML models. Makes use of existing models wherever possible and has strong knowledge of the literature in his area.
- *Currently:* Validating a random forest model trained on MIC data from ChEMBL against a held-out test set, trying to push classification accuracy above 80% before Samira reviews it. Also searching for existing ML models in the literature to benchmark against.
- *Lifestyle:* Wake 7:30am, bed 11:00pm, lunch at cafeteria ~12:30.
- *Relationships:* Direct report to Samira (weekly 1:1, rigorous train/test split reviews). Collaborates closely with Lilly — her toxicity flags filter his activity predictions, exchange results often. Cross-group coffee chats with Alex to discuss whether model predictions make chemical sense.

**Lilly Florentino** (Samira's group, red)
- *Bio:* Focused on counterscreening for cellular toxicity. Interdisciplinary, makes use of existing models and has strong literature knowledge in toxicity prediction.
- *Currently:* Assembling a counterscreening pipeline — has identified three public toxicity endpoints (hERG, cytotoxicity, others) and is sourcing the right datasets to validate the workflow.
- *Lifestyle:* Wake 8:00am, bed midnight, lunch at cafeteria ~1:00pm.
- *Relationships:* Direct report to Samira (trusted to work independently, everything benchmarked before passing to Erick's group). Collaborates closely with Rongzhen. Pragmatic working relationship with Alex — his pharmacophore annotations tell her which structural features to watch for toxicity red flags.

**Alex Tyman** (Erick's group, yellow)
- *Bio:* Skilled medicinal chemist. Can take structures from others and identify the active pharmacophore, scaffold, and functional groups — and speculate on their role. Deep practical knowledge of SAR.
- *Currently:* Analyzing a shortlist of 12 candidate scaffolds from Erick's group, annotating each with its likely pharmacophore, known liabilities, and synthetic accessibility score, preparing a one-page summary for the team.
- *Lifestyle:* Wake 7:00am, bed 11:00pm, lunch at cafeteria ~12:00.
- *Relationships:* Direct report to Erick (daily reviews, experienced enough to push back diplomatically on accessibility disagreements). Passes scaffold ideas to Rongzhen for activity scoring. Provides structural feature annotations to Lilly. Informal coffee chats with both Samira postdocs.

#### PhDs ✓
**Yuri Zuckermann** (Samira's group)
- *Bio:* Early-stage PhD student in Samira's computational group. Bold and optimistic, prone to excitement over preliminary results.
- *Currently:* Running his first independent ML experiment — a naive Bayes classifier on antibiotic activity — and excitedly comparing it to Rongzhen's random forest, convinced his approach will perform better.
- *Lifestyle:* Wake 8:00am, bed midnight, lunch at cafeteria ~1:00pm. Energetic, works in bursts.
- *Relationships:* Supervised by Samira. Works alongside Rongzhen. Roommates and friendly rivals with Lionel — debates computational vs. experimental approaches over dinner; Yuri vents to Lionel when Samira pushes back on his benchmarks.

**Lionel Wittinger** (Erick's group)
- *Bio:* Mid-stage PhD student in Erick's experimental group. Methodical and sceptical, cross-checks everything against primary literature.
- *Currently:* Carefully reviewing Alex's pharmacophore annotations for 3 of the 12 candidate scaffolds, cross-checking against the primary literature to verify the SAR reasoning before adding his own structural notes.
- *Lifestyle:* Wake 8:30am, bed 11:30pm, lunch at cafeteria ~12:30pm. Methodical, steady pace.
- *Relationships:* Supervised by Erick. Works alongside Alex. Roommates and friendly rivals with Yuri — sceptical of Yuri's computational enthusiasm, vents to Yuri when Erick finds fault with his retrosynthesis.

#### PhDs `[?]` — needed after postdocs
Yuri Zuckermann, Lionel Wittinger — bios, current states, lifestyles, relationships

**Action items:**
- `[x]` Collect user input for all `[?]` items (core 7 agents)
- `[x]` Generate `scratch.json` for all 7 core personas
- `[x]` Copy `spatial_memory.json` from Isabella to all 7 personas
- `[x]` Create associative memory files for all 7 personas
- `[x]` Write `reverie/meta.json` with 7 persona names, start date Sep 1 2025
- `[x]` Run path tester to collect (x, y) coordinates for `environment/0.json` (derived directly from maze CSVs)

---

### 1.3 Seed agent history (whisper CSV)
**File:** `environment/frontend_server/static_dirs/assets/chemville/agent_history_init_n18.csv`

Currently exists but has only a header row. Add 4–6 whisper sentences per agent that seed their relationships, research context, and group dynamics. These become their day-1 memories.

- `[x]` Collect relationship map from user
- `[x]` Write whisper rows for all 7 core agents (no research goal in whispers — goal lives in system prompt only, per Step 1.6)

---

### 1.4 Fix hardcoded cafeteria fallback
**File:** `reverie/backend_server/persona/cognitive_modules/execute.py` (lines 82 and 94)

Currently: any failed address lookup silently routes agents to `chemville:Cafeteria:cafe`, causing clustering.
Fix: fall back to `persona.scratch.living_area` instead.

- `[x]` Replace hardcoded `"chemville:Cafeteria:cafe"` fallback with `persona.scratch.living_area` (falls back to first known address if living_area also missing)

---

### 1.5 Chemistry-appropriate prompts
Replace generic social simulation few-shot examples with chemistry research examples in 4 files:

**File:** `reverie/backend_server/persona/prompt_template/v2/daily_planning_v6.py`
- `[x]` Replaced "watch TV / have lunch" examples with: lab experiments, group meeting, writing results, reading papers. Research goal injected as optional line when `scenario_config.RESEARCH_GOAL` is set.

**File:** `reverie/backend_server/persona/prompt_template/v2/task_decomp_v3.py`
- `[x]` Replaced schoolteacher example with synthesis experiment subtasks (prepare reagents → reflux → monitor by TLC → work up → record in notebook → clean up → label samples)

**File:** `reverie/backend_server/persona/prompt_template/v1/action_location_sector_v1.py`
- `[x]` Replaced "Hobbs Cafe / Johnson Park" examples with ChemVille agents (Rongzhen → Lab1 for ML training; Samira → Cafeteria for lunch)

**File:** `reverie/backend_server/persona/prompt_template/v1/action_location_arena_vMar11.py`
- `[x]` Replaced Jane Anderson / Tom Watson examples with ChemVille agents (Rongzhen → Lab1:Theory for computation; Alex → Cafeteria:cafe for lunch)

---

### 1.6 Scenario configuration system
**New file:** `reverie/backend_server/scenario_config.py`
**Modified file:** `reverie/backend_server/reverie.py`

A JSON config that sets the simulation's research goal and active agent list, injected into each agent's daily planning prompt:

```json
{
  "research_goal": "discover a novel antibiotic scaffold targeting bacterial cell wall synthesis",
  "scenario_name": "antibiotic_discovery_run_01",
  "active_persona_names": ["Samira Reininger", "Erick Gruetzberger", ...],
  "sim_duration_days": 2
}
```

- `[x]` Research goal confirmed: "Give the SMILES output of an antibiotic scaffold targeting S. aureus. It should be active, non-toxic and novel (i.e. not reported in literature)."
- `[x]` Created `scenario_config.py` — module-level `RESEARCH_GOAL` loaded from `scenario.json` in sim folder
- `[x]` Created `storage/base_chemville_all_19/scenario.json` with research goal
- `[x]` Modified `reverie.py` to call `scenario_config.load(sim_folder)` at init
- `[x]` Modified `daily_planning_v6.py` to import `scenario_config` and pass `RESEARCH_GOAL` into prompt

---

### 1.7 Fix character sprites
**Note:** `characters_chemville/atlas.json` is not referenced anywhere in the frontend — it was a red herring. The actual system works as follows:
- **Live sim** (`home/main_script.html`): uses a single external misa atlas for all personas — no per-character assets needed.
- **Demo/replay** (`demo/main_script.html`): loads `assets/characters/{Name_Underscore}.png` per persona + the shared `assets/characters/atlas.json` (already correct).

Fix: copy existing sprites to ChemVille persona names.

- `[x]` Copied sprite sheets and profile PNGs for all 7 core personas:
  - Samira_Reininger ← Mei_Lin
  - Erick_Gruetzberger ← Arthur_Burton
  - Rongzhen_Yang ← Eddy_Lin
  - Lilly_Florentino ← Hailey_Johnson
  - Alex_Tyman ← Giorgio_Rossi
  - Yuri_Zuckermann ← Ryan_Park
  - Lionel_Wittinger ← Wolfgang_Schulz
- `[ ]` (Later) Replace with unique character sprites when art is available

---

### 1.8 Validate and run
- `[x]` Test with a small subset (2–3 agents) in headless mode to confirm startup without errors
- `[ ]` Run path tester for all rooms to confirm agents can navigate the full map
- `[ ]` Run full 19-agent simulation, verify activity profiles make sense (agents go to labs, not just cafeteria)
- `[ ]` Confirm video playback works via `http://localhost:8000/replay/<sim-name>/0`

### 1.9 MP4 export (optional, post first run)
**New file:** `reverie/export_video.py`

Headless replay → MP4 pipeline using Playwright (headless Chrome) + ffmpeg:
1. Serve the demo replay locally
2. Use Playwright to screenshot each step of `/replay/<sim_name>/0`
3. Pipe screenshots to ffmpeg to produce a timestamped MP4

- `[ ]` Implement `export_video.py` with Playwright screenshot loop + ffmpeg encode
- `[ ]` Add `--fps` and `--output` arguments
- `[ ]` Test with a short run (20 steps → ~20 frames)

**Recommended run command:**
```bash
./run_backend_automatic.sh \
  -o base_chemville_all_19 \
  -t chemville_run_01 \
  -s 17280 \
  --ui None \
  --load_history ./environment/frontend_server/static_dirs/assets/chemville/agent_history_init_n18.csv
```
> 17,280 steps = 2 simulated days at 10 seconds/step. Estimated cost: ~$3–6 with gpt-4o-mini and 12–15 active agents.

---

## Phase 2 — Lab Devices (Tool Calls)

*Prerequisite: Phase 1 validated and running stably.*

### 2.1 Chemistry tool functions
**New file:** `reverie/backend_server/tools/chemistry_tools.py`
**New file:** `reverie/backend_server/tools/tool_registry.py`

Four tools, each with 5-second timeout and graceful error handling:

| Tool | API | Purpose |
|------|-----|---------|
| `search_pubchem(compound_name)` | PubChem PUG REST (free) | Chemical properties, structure, synonyms |
| `search_chembl(target_name)` | ChEMBL REST (free) | Drug targets, bioactivity data |
| `search_literature(query)` | Semantic Scholar Graph API (free, no key) | Recent papers, abstracts |
| `search_web(query)` | Brave Search or SerpAPI | General web search |

- `[ ]` Implement `chemistry_tools.py` with all four functions
- `[ ]` Create `tool_registry.py` mapping string names to callables

---

### 2.2 Extend task decomposition for tool calls
**File:** `reverie/backend_server/persona/prompt_template/v2/task_decomp_v3.py`

Add optional `tool_call: {tool_name, arguments}` field to the `Subtask` Pydantic model. Backward compatible — null if unused. Add a "available lab tools" block to the prompt for research-role agents.

- `[ ]` Add `ToolCall` and `Optional[ToolCall]` to the `Subtask` model
- `[ ]` Add tool-use instructions and example to `create_prompt()`

---

### 2.3 Execute tools in the cognitive loop
**File:** `reverie/backend_server/persona/cognitive_modules/plan.py`

After task decomp, dispatch any tool calls in the schedule. Inject results directly into the agent's associative memory as high-poignancy events — they become retrievable memories that influence future planning and conversation, with no new infrastructure needed.

- `[ ]` Add `execute_tool_calls_in_schedule()` after task decomp
- `[ ]` Inject tool results into associative memory via `persona.a_mem.add_event()`

---

### 2.4 Shared lab notebook
**New file:** `reverie/backend_server/lab_notebook.py`

A persistent JSON side-file that all agents can read from and write to. Models a shared Electronic Lab Notebook (ELN). Last 3 entries are injected into each agent's daily planning context — Agent A writes results, Agent B reads them next morning.

- `[ ]` Implement `LabNotebook` class with `add_entry()`, `get_recent_entries()`, `search_entries()`
- `[ ]` Instantiate in `reverie.py` and pass to planning context
- `[ ]` Trigger notebook writes for "documenting results" / "writing in lab notebook" subtasks

---

### 2.5 Tool access control in scenario config
**File:** `reverie/backend_server/scenario_config.py`

Add to the scenario config:
```json
{
  "enabled_tools": ["search_pubchem", "search_literature"],
  "tool_call_budget_per_agent_per_day": 10
}
```
Enforce budget in `execute_tool_calls_in_schedule()` to prevent runaway API usage.

- `[ ]` Add `enabled_tools` and `tool_call_budget_per_agent_per_day` to scenario config
- `[ ]` Enforce budget per agent per simulated day

---

## Phase 3 — Evaluation

*Prerequisite: At least one complete simulation run.*

### 3.1 Agent interview method
**File:** `reverie/backend_server/persona/persona.py`

Wrap the existing `open_convo_session("analysis")` into a structured interview loop.

- `[ ]` Add `conduct_research_interview(questions: list) -> dict` method to `Persona`

---

### 3.2 Evaluation runner script
**New file:** `reverie/backend_server/evaluation/evaluate_run.py`

Standalone script: loads a completed simulation, interviews all agents, writes structured report.

```bash
python evaluate_run.py --sim_code chemville_run_01 --output_path reports/
```

Standard interview questions:
1. What have you been working on in the lab this week?
2. What experiments or analyses did you complete?
3. What were your most interesting findings or challenges?
4. How does your work relate to the lab's research goal?
5. What are your next steps?
6. Who did you collaborate with, and what did you learn?

Output per agent: `{question: answer, ...}` JSON + a 3-sentence research contribution summary.

- `[ ]` Implement `evaluate_run.py`
- `[?]` Review standard interview questions with user — add or change any?

---

### 3.3 Cross-run comparison
**File:** `reverie/backend_server/evaluation/evaluate_run.py` (extended)

When two run codes are provided:
- Embedding cosine similarity between research summaries across runs
- Lab notebook divergence (what did each run discover differently?)
- Activity profile per agent: % time in Lab vs. Classroom vs. Cafeteria (from existing `movement/` JSON files — no new simulation instrumentation needed)

```bash
python evaluate_run.py --sim_code run_01 run_02 --output_path reports/compare/
```

- `[ ]` Add multi-run comparison mode to `evaluate_run.py`

---

## Map Reference

**ChemVille sectors and arenas** (already in the deployed map):

| Sector | Contains |
|--------|----------|
| Lab1 | Theory, Experiment rooms |
| Lab2 | Theory, Experiment rooms |
| Lab3 | Theory, Experiment rooms |
| Classroom | Main classroom |
| Seminarroom | Seminar room |
| Dorm1 | Rooms A, B, C, D |
| Dorm2 | Rooms B, C |
| Dorm3 | Rooms A, B, C |
| Dorm4 | Rooms A, B, C |
| Office1 | Office space |
| Office2 | Office space |
| Office3 | Office space |
| Cafeteria | Cafe area |

**Tiled source files** (for map edits): `assets/Tilesets/Tiled/chemville.tmx`
**Deployed map** (authoritative): `environment/frontend_server/static_dirs/assets/chemville/visuals/chemville.tmx`

---

## Quick Reference: Key Files

| File | Purpose |
|------|---------|
| `reverie/backend_server/reverie.py` | Main simulation loop |
| `reverie/backend_server/automatic_execution.py` | Run launcher with error recovery |
| `reverie/backend_server/persona/persona.py` | Agent cognitive loop |
| `reverie/backend_server/persona/cognitive_modules/execute.py` | Pathfinding (has hardcoded fallback — see 1.4) |
| `reverie/backend_server/persona/cognitive_modules/plan.py` | Daily planning + task decomp |
| `reverie/backend_server/persona/prompt_template/gpt_structure.py` | LLM call router |
| `reverie/backend_server/persona/prompt_template/v2/daily_planning_v6.py` | Daily plan prompt |
| `reverie/backend_server/persona/prompt_template/v2/task_decomp_v3.py` | Task decomp prompt |
| `environment/frontend_server/storage/base_chemville_all_19/` | Simulation bootstrap data (to be created) |
| `environment/frontend_server/static_dirs/assets/chemville/matrix/special_blocks/` | Named map locations and spawn points |
| `assets/ChemVille_Character_List.xlsx` | Character roster (source of truth) |
| `assets/Tilesets/Tiled/chemville.tmx` | Tiled source map |

---

## Current Blockers (before first run)

1. **Spawn points missing** (Step 1.1) — Rongzhen, Lionel, Laura, Henry, Sophia, Clyde, Sarah, Marco have no valid start tiles
2. **User input required** (Step 1.2) — research scenario, character bios, current states, lifestyles, relationships not yet defined
3. ~~**atlas.json empty** (Step 1.7)~~ — fixed (sprites copied to correct paths)
4. ~~**Prompts still social** (Step 1.5)~~ — fixed
