#!/usr/bin/env python3
"""
audit_run.py — Post-run analysis for a ChemVille simulation.

Usage:
  python reverie/audit_run.py --sim halfday_sim_02
  python reverie/audit_run.py --sim halfday_sim_02 --llm-summary
  python reverie/audit_run.py --list

Outputs a markdown audit report covering:
  - Activity timeline per agent (compressed)
  - Tool calls & chemistry results (SMILES, compounds, papers)
  - Agent-to-agent conversation counts
  - Optional LLM-generated narrative summary per agent
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

STORAGE_ROOT = Path(__file__).parent.parent / "environment/frontend_server/storage"


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def find_storage_dir(sim_code: str) -> Path:
    d = STORAGE_ROOT / sim_code
    if not d.exists():
        sys.exit(f"ERROR: Storage directory not found: {d}")
    return d


def load_movement_files(storage_dir: Path) -> list[tuple[int, dict]]:
    mv_dir = storage_dir / "movement"
    if not mv_dir.exists():
        sys.exit(f"ERROR: No movement/ directory in {storage_dir}")
    steps = sorted(int(f.stem) for f in mv_dir.glob("*.json"))
    result = []
    for step in steps:
        with open(mv_dir / f"{step}.json") as f:
            result.append((step, json.load(f)))
    return result


def load_scenario(storage_dir: Path) -> dict:
    p = storage_dir / "scenario.json"
    if p.exists():
        with open(p) as f:
            return json.load(f)
    return {}


def load_meta(storage_dir: Path) -> dict:
    p = storage_dir / "reverie" / "meta.json"
    if p.exists():
        with open(p) as f:
            return json.load(f)
    return {}


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def build_timelines(steps_data: list[tuple[int, dict]]) -> dict[str, list[tuple[str, str, str]]]:
    """
    Compressed activity timeline per agent.
    Returns {agent: [(sim_time, description, address), ...]}
    Only records when description changes.
    """
    timelines: dict[str, list] = defaultdict(list)
    last_desc: dict[str, str] = {}

    for step, data in steps_data:
        sim_time = data.get("meta", {}).get("curr_time", f"step {step}")
        for agent, v in data["persona"].items():
            desc = v.get("description") or ""
            if desc != last_desc.get(agent):
                # Split "action @ address"
                if "@" in desc:
                    action, addr = desc.split("@", 1)
                    action = action.strip()
                    addr = addr.strip()
                else:
                    action = desc.strip()
                    addr = ""
                timelines[agent].append((sim_time, action, addr))
                last_desc[agent] = desc

    return dict(timelines)


def extract_tool_calls(steps_data: list[tuple[int, dict]]) -> list[dict]:
    """
    Return list of all non-null tool_call records across the run.
    Each: {step, sim_time, agent, name, args, result}
    """
    results = []
    for step, data in steps_data:
        sim_time = data.get("meta", {}).get("curr_time", f"step {step}")
        for agent, v in data["persona"].items():
            tc = v.get("tool_call")
            if tc and isinstance(tc, dict) and tc.get("result"):
                results.append({
                    "step": step,
                    "sim_time": sim_time,
                    "agent": agent,
                    "name": tc.get("name", ""),
                    "args": tc.get("args", ""),
                    "result": tc.get("result", ""),
                })
    return results


def extract_smiles(text: str) -> list[str]:
    """
    Extract SMILES-like strings from text using a simple heuristic:
    token contains ring atoms + bonds and is not a word.
    """
    # Match tokens that look like SMILES (contain brackets, =, #, or ring closures with digits)
    smiles_pattern = re.compile(
        r'\b([A-Za-z][A-Za-z0-9@+\-\[\]()=#:/\\%\.]{6,})\b'
    )
    candidates = smiles_pattern.findall(text)
    # Filter: must contain at least one chemistry-specific character
    chem_chars = set('=#[]@+\\/')
    smiles = [c for c in candidates if any(ch in c for ch in chem_chars)]
    return list(dict.fromkeys(smiles))  # deduplicate preserving order


def extract_conversations(steps_data: list[tuple[int, dict]]) -> dict[str, dict[str, int]]:
    """
    Count conversation turns per (agent, partner) pair.
    Returns {agent: {partner: turn_count}}
    """
    interactions: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    seen_chats: set = set()  # avoid double-counting same chat in adjacent steps

    for step, data in steps_data:
        for agent, v in data["persona"].items():
            chat = v.get("chat")
            if not chat or not isinstance(chat, list):
                continue
            # Fingerprint the chat to avoid re-counting across repeated steps
            fingerprint = (agent, len(chat), chat[0][0] if chat else "")
            if fingerprint in seen_chats:
                continue
            seen_chats.add(fingerprint)

            speakers = set(turn[0] for turn in chat if isinstance(turn, list) and len(turn) >= 1)
            partners = speakers - {agent}
            for partner in partners:
                # Count turns spoken by each side
                agent_turns = sum(1 for t in chat if isinstance(t, list) and t[0] == agent)
                interactions[agent][partner] += agent_turns

    return {k: dict(v) for k, v in interactions.items()}


# ---------------------------------------------------------------------------
# Report rendering
# ---------------------------------------------------------------------------

def render_report(
    sim_code: str,
    scenario: dict,
    meta: dict,
    steps_data: list,
    timelines: dict,
    tool_calls: list,
    interactions: dict,
) -> str:
    lines = []
    total_steps = len(steps_data)
    start_time = steps_data[0][1]["meta"]["curr_time"] if steps_data else "?"
    end_time = steps_data[-1][1]["meta"]["curr_time"] if steps_data else "?"
    agents = list(timelines.keys())

    lines.append(f"# ChemVille Simulation Audit: `{sim_code}`")
    lines.append("")
    lines.append(f"**Scenario:** {scenario.get('scenario_name', 'N/A')}")
    lines.append(f"**Research goal:** {scenario.get('research_goal', 'N/A')}")
    lines.append(f"**Time range:** {start_time} → {end_time}  ({total_steps} steps × 10 s/step = {total_steps * 10 // 60} min simulated)")
    lines.append(f"**Agents:** {', '.join(agents)}")
    lines.append("")

    # --- Tool calls ---
    lines.append("---")
    lines.append("## Tool Calls")
    if not tool_calls:
        lines.append("_No tool calls recorded in this run._  ")
        lines.append("_(Tool call activation fix was applied after this run started — future runs will populate this section.)_")
    else:
        by_agent: dict[str, list] = defaultdict(list)
        for tc in tool_calls:
            by_agent[tc["agent"]].append(tc)

        all_smiles = []
        for agent, calls in by_agent.items():
            lines.append(f"\n### {agent} ({len(calls)} calls)")
            for tc in calls:
                lines.append(f"- **{tc['sim_time']}** — `{tc['name']}({tc['args']})`")
                result_short = tc["result"][:300].replace("\n", " ")
                lines.append(f"  > {result_short}{'…' if len(tc['result']) > 300 else ''}")
                smiles = extract_smiles(tc["result"])
                if smiles:
                    lines.append(f"  > SMILES found: `{'`, `'.join(smiles)}`")
                    all_smiles.extend(smiles)

        if all_smiles:
            lines.append("\n### All SMILES encountered")
            for s in dict.fromkeys(all_smiles):
                lines.append(f"- `{s}`")

    # --- Conversations ---
    lines.append("")
    lines.append("---")
    lines.append("## Agent Interactions")

    if not interactions:
        lines.append("_No conversations recorded._")
    else:
        # Build a summary table
        lines.append("")
        lines.append("| Agent | Talked with | Your turns |")
        lines.append("|-------|-------------|------------|")
        for agent in sorted(interactions.keys()):
            for partner, turns in sorted(interactions[agent].items(), key=lambda x: -x[1]):
                lines.append(f"| {agent} | {partner} | {turns} |")

        # Total unique contacts per agent
        lines.append("")
        lines.append("**Unique conversation partners per agent:**")
        for agent in sorted(agents):
            partners = interactions.get(agent, {})
            total_turns = sum(partners.values())
            if partners:
                partner_list = ", ".join(sorted(partners.keys()))
                lines.append(f"- **{agent}**: {len(partners)} partner(s) ({total_turns} turns) — {partner_list}")
            else:
                lines.append(f"- **{agent}**: no conversations recorded")

    # --- Activity timelines ---
    lines.append("")
    lines.append("---")
    lines.append("## Activity Timelines")
    lines.append("_Each entry = description changed. Time shown is sim time at change._")

    for agent in agents:
        timeline = timelines.get(agent, [])
        lines.append(f"\n### {agent}")
        if not timeline:
            lines.append("_No activity recorded._")
            continue
        for sim_time, action, addr in timeline:
            time_short = sim_time.split(", ")[-1] if ", " in sim_time else sim_time
            addr_str = f" @ `{addr}`" if addr else ""
            lines.append(f"- **{time_short}** — {action}{addr_str}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# LLM narrative summary
# ---------------------------------------------------------------------------

def generate_llm_summary(
    scenario: dict,
    timelines: dict,
    tool_calls: list,
    interactions: dict,
) -> str:
    try:
        from openai import OpenAI
        # Pull API key from the backend_server utils (same key used by the simulation)
        _be_path = Path(__file__).parent / "backend_server"
        sys.path.insert(0, str(_be_path))
        from utils import openai_api_key  # noqa
        client = OpenAI(api_key=openai_api_key)
    except Exception as e:
        return f"_Could not initialize OpenAI client: {e}_"

    research_goal = scenario.get("research_goal", "")

    # Compress timelines to brief bullet points for the prompt
    agent_summaries = []
    for agent, timeline in timelines.items():
        bullets = []
        for sim_time, action, addr in timeline:
            time_short = sim_time.split(", ")[-1] if ", " in sim_time else sim_time
            bullets.append(f"  {time_short}: {action[:120]}")
        partner_list = list((interactions.get(agent) or {}).keys())
        agent_summaries.append(
            f"**{agent}**\n" + "\n".join(bullets[:40]) +
            (f"\n  [Talked with: {', '.join(partner_list)}]" if partner_list else "")
        )

    tool_summary = ""
    if tool_calls:
        tool_summary = "\n\nTool calls made:\n" + "\n".join(
            f"- {tc['agent']} @ {tc['sim_time']}: {tc['name']}({tc['args']}) → {tc['result'][:200]}"
            for tc in tool_calls[:30]
        )

    prompt = f"""You are analysing a generative-agent simulation of a chemistry research group.
Research goal: {research_goal}

Below is each agent's compressed activity log for this simulation run.
{tool_summary}

Agent activity logs:
{''.join(chr(10)*2 + s for s in agent_summaries)}

Write a concise narrative report (1–3 paragraphs per agent) covering:
1. What did each agent actually do and work on?
2. What scientific progress (if any) was made toward the research goal?
3. Which agents collaborated and on what?
4. Were any SMILES or compounds found/proposed? If so, list them.
5. What were the key open questions or next steps at end of the run?

Be concrete and specific — cite exact actions, partners, and any chemistry details from the logs."""

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.3,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"_LLM summary failed: {e}_"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Audit a ChemVille simulation run.")
    parser.add_argument("--sim", help="Simulation code (directory name under storage/)")
    parser.add_argument("--list", action="store_true", help="List available simulation runs")
    parser.add_argument("--llm-summary", action="store_true",
                        help="Append an LLM-generated narrative summary (uses gpt-4o-mini)")
    parser.add_argument("--out", help="Write report to this file instead of stdout")
    args = parser.parse_args()

    if args.list:
        runs = sorted(d.name for d in STORAGE_ROOT.iterdir()
                      if d.is_dir() and not d.name.startswith("base_"))
        print("Available simulation runs:")
        for r in runs:
            n_steps = len(list((STORAGE_ROOT / r / "movement").glob("*.json"))) if (STORAGE_ROOT / r / "movement").exists() else 0
            print(f"  {r:<50} ({n_steps} steps)")
        return

    if not args.sim:
        parser.error("Provide --sim <run_name> or --list")

    storage_dir = find_storage_dir(args.sim)
    scenario = load_scenario(storage_dir)
    meta = load_meta(storage_dir)

    print(f"Loading movement files from {storage_dir}/movement/ ...", file=sys.stderr)
    steps_data = load_movement_files(storage_dir)
    print(f"Loaded {len(steps_data)} steps.", file=sys.stderr)

    timelines = build_timelines(steps_data)
    tool_calls = extract_tool_calls(steps_data)
    interactions = extract_conversations(steps_data)

    report = render_report(args.sim, scenario, meta, steps_data, timelines, tool_calls, interactions)

    if args.llm_summary:
        print("Generating LLM narrative summary...", file=sys.stderr)
        summary = generate_llm_summary(scenario, timelines, tool_calls, interactions)
        report += "\n\n---\n## LLM Narrative Summary\n\n" + summary

    if args.out:
        with open(args.out, "w") as f:
            f.write(report)
        print(f"Report written to {args.out}", file=sys.stderr)
    else:
        print(report)


if __name__ == "__main__":
    main()
