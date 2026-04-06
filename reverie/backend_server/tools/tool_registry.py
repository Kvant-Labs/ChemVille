"""
tool_registry.py

Maps game_object names to the tools available at that object and enforces
per-agent per-day call budgets. Import this module wherever tool dispatch
is needed.
"""
from .chemistry_tools import search_pubchem, search_chembl, search_literature

# ---------------------------------------------------------------------------
# Tool function table
# ---------------------------------------------------------------------------
TOOL_FUNCTIONS = {
    "search_pubchem": search_pubchem,
    "search_chembl": search_chembl,
    "search_literature": search_literature,
}

# ---------------------------------------------------------------------------
# Game-object → available tools
# Keys must match the game_object values in game_object_maze.csv exactly.
# ---------------------------------------------------------------------------
GAME_OBJECT_TOOLS: dict[str, list[str]] = {
    "computer":       ["search_literature", "search_pubchem", "search_chembl"],
    "lab equipment":  ["search_pubchem", "search_chembl", "search_literature"],
    "lab equipment1": ["search_pubchem", "search_chembl", "search_literature"],
    "lab equipment2": ["search_pubchem", "search_chembl", "search_literature"],
    "lab equipment3": ["search_pubchem", "search_chembl", "search_literature"],
    "whiteboard":     ["search_literature"],
    "desk":           ["search_literature", "search_pubchem", "search_chembl"],
}

# ---------------------------------------------------------------------------
# Budget tracking: {persona_name: {sim_date_str: call_count}}
# Reset each simulated day automatically.
# ---------------------------------------------------------------------------
_budget: dict[str, dict[str, int]] = {}
DEFAULT_BUDGET = 10


def is_tool_capable(game_object: str) -> bool:
    """Return True if game_object has at least one tool available."""
    return game_object in GAME_OBJECT_TOOLS


def get_available_tools(game_object: str) -> list[str]:
    """Return list of tool names available at the given game object."""
    return GAME_OBJECT_TOOLS.get(game_object, [])


def call_tool(
    name: str,
    args: str,
    persona_name: str,
    sim_date_str: str = "",
    budget: int = DEFAULT_BUDGET,
    enabled_tools: list[str] | None = None,
) -> str | None:
    """Execute a named tool with the given args string.

    Returns the result string, or None if the tool is disabled, the budget
    is exhausted, or the tool name is unknown.
    """
    if enabled_tools is not None and name not in enabled_tools:
        return None

    if name not in TOOL_FUNCTIONS:
        return None

    # Budget enforcement
    day_key = sim_date_str or "default"
    agent_budget = _budget.setdefault(persona_name, {})
    count = agent_budget.get(day_key, 0)
    if count >= budget:
        print(f"(tool_registry): {persona_name} budget exhausted for {day_key} ({count}/{budget})")
        return None

    agent_budget[day_key] = count + 1
    print(f"(tool_registry): {persona_name} calling {name}({args!r}) [{count+1}/{budget}]")

    return TOOL_FUNCTIONS[name](args)
