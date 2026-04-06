from pydantic import BaseModel
import traceback
import datetime
from typing import Any, Optional

from ..common import openai_config, get_prompt_file_path
from ..gpt_structure import safe_generate_structured_response
from ..print_prompt import print_run_prompts
import scenario_config


# All active personas are eligible for tool use, including PIs.
TOOL_ELIGIBLE_PERSONAS = {
    "Samira Reininger", "Erick Gruetzberger",
    "Rongzhen Yang", "Lilly Florentino", "Alex Tyman",
    "Yuri Zuckermann", "Lionel Wittinger", "Laura Stevens",
    "Amelia Hayes", "Tyler Zhao",
    "Tara Olson", "Naima Jamila", "Henry Scott", "Sophia Cortez",
}

# Keywords that indicate a chemistry-related subtask requiring a tool call.
CHEMISTRY_KEYWORDS = {
    "compound", "scaffold", "molecule", "drug", "smiles", "structure",
    "synthesis", "antibiotic", "inhibitor", "ligand", "binding", "assay",
    "activity", "toxicity", "herg", "mic", "ic50", "aureus", "bacteria",
    "protein", "receptor", "enzyme", "target", "pharmacophore", "literature",
    "paper", "reading", "review", "data", "model", "dataset", "prediction",
    "screen", "candidate", "analog", "series", "scaffold",
}

_TOOL_PROMPT_TEMPLATE = """
MANDATORY TOOL USE — this group is working toward: {research_goal}

For EVERY subtask, you MUST include a tool_call unless the subtask is purely physical (walking, eating, sleeping, or talking face-to-face).

Available tools:
- search_pubchem(compound_name): returns canonical SMILES, molecular formula, MW — use for any compound, drug, scaffold, or molecule
- search_chembl(target_name): returns drug targets, bioactivity — use for proteins, receptors, enzymes, targets
- search_literature(query): returns paper abstracts — use for reading, reviewing, or literature tasks

MANDATORY RULES:
1. Subtask involves a compound, scaffold, molecule, or drug → tool_call: search_pubchem("<specific compound name>")
2. Subtask involves a protein, receptor, enzyme, or target → tool_call: search_chembl("<target name>")
3. Subtask involves literature, papers, reading, or reviewing data → tool_call: search_literature("<specific query>")
4. Purely physical or social subtask (walking, eating, chatting) → tool_call: null

SMILES REQUIREMENT: For search_pubchem calls, use a SPECIFIC compound name (e.g. "oxacillin", "vancomycin", "penicillin G", "daptomycin") not a vague category. The result will contain a SMILES string.

Example (chemistry): {{"task": "reviewing candidate scaffold structures for S. aureus activity", "duration": 15, "minutes_left": 45, "tool_call": {{"name": "search_pubchem", "args": "oxacillin"}}}}
Example (target): {{"task": "checking bioactivity data for PBP2a binding", "duration": 10, "minutes_left": 30, "tool_call": {{"name": "search_chembl", "args": "penicillin binding protein 2a"}}}}
Example (literature): {{"task": "reading recent papers on beta-lactam resistance mechanisms", "duration": 20, "minutes_left": 25, "tool_call": {{"name": "search_literature", "args": "beta-lactam resistance S. aureus novel scaffolds"}}}}
Example (social, no tool): {{"task": "walking to the cafeteria for lunch", "duration": 15, "minutes_left": 40, "tool_call": null}}
"""


def _make_tool_block(research_goal: str) -> str:
    return _TOOL_PROMPT_TEMPLATE.format(research_goal=research_goal or "produce a novel antibiotic SMILES scaffold")


def create_prompt(prompt_input: dict[str, Any]):
  identity_stable_set = prompt_input["identity_stable_set"]
  broad_schedule_summary = prompt_input["broad_schedule_summary"]
  persona_firstname = prompt_input["persona_firstname"]
  persona_fullname = prompt_input.get("persona_fullname", "")
  action = prompt_input["action"]
  action_duration = prompt_input["action_duration"]
  action_time_range = prompt_input["action_time_range"]

  tool_block = _make_tool_block(scenario_config.RESEARCH_GOAL) if persona_fullname in TOOL_ELIGIBLE_PERSONAS else ""

  prompt = f"""
Describe subtasks in 5 min increments.

--- Example ---
Name: Amelia Hayes
Age: 22
Backstory: Amelia Hayes is a PhD student in an experimental chemistry group working on antibiotic discovery. She is hands-on and loves being in the lab.
Personality: visionary, eco-driven, hands-on
Location: Amelia is in Lab1 that has the following areas: [Experiment, Theory].
Currently: Amelia is running a synthesis experiment to produce a candidate antibiotic scaffold.
Daily plan requirement: Amelia spends mornings running experiments in the lab, afternoons analysing results and reading papers.

Today is Monday September 1. From 08:00am ~ 09:00am, Amelia is planning on completing her morning routine, from 09:00am ~ 12:00pm, Amelia is planning on running a synthesis experiment, and from 12:00pm ~ 13:00pm, Amelia is planning on having lunch.
In 5 min increments, list the subtasks Amelia does when Amelia is running a synthesis experiment from 09:00am ~ 12:00pm (total duration in minutes: 180):
1) Amelia is preparing the reaction vessel and reagents. (duration in minutes: 20, minutes left: 160)
2) Amelia is setting up the reflux condenser. (duration in minutes: 15, minutes left: 145)
3) Amelia is heating the reaction mixture. (duration in minutes: 60, minutes left: 85)
4) Amelia is monitoring the reaction progress by TLC. (duration in minutes: 30, minutes left: 55)
5) Amelia is cooling the mixture and filtering the product. (duration in minutes: 25, minutes left: 30)
6) Amelia is recording observations in the lab notebook. (duration in minutes: 15, minutes left: 15)
7) Amelia is cleaning up the fume hood. (duration in minutes: 10, minutes left: 5)
8) Amelia is labelling samples for analysis. (duration in minutes: 5, minutes left: 0)
---
{identity_stable_set}
{broad_schedule_summary}
In 5 min increments, list the subtasks {persona_firstname} does when {persona_firstname} is {action} from {action_time_range} (total duration in minutes: {action_duration}). Use present progressive tense (e.g., "recording observations in the lab notebook").
{tool_block}"""
  return prompt


class ToolCall(BaseModel):
  name: str   # e.g. "search_pubchem"
  args: str   # e.g. "penicillin G"


class Subtask(BaseModel):
  task: str
  duration: int
  minutes_left: int
  tool_call: Optional[ToolCall] = None


class TaskDecomposition(BaseModel):
  subtasks: list[Subtask]


def run_gpt_prompt_task_decomp(persona, task, duration, test_input=None, verbose=False):
  def create_prompt_input(persona, task, duration, test_input=None, debug=False):
    """
    Today is Saturday June 25. From 00:00 ~ 06:00am, Maeve is
    planning on sleeping, 06:00 ~ 07:00am, Maeve is
    planning on waking up and doing her morning routine,
    and from 07:00am ~08:00am, Maeve is planning on having breakfast.
    """
    curr_f_org_index = persona.scratch.get_f_daily_schedule_hourly_org_index()
    all_indices = []
    # if curr_f_org_index > 0:
    #   all_indices += [curr_f_org_index-1]
    all_indices += [curr_f_org_index]
    if curr_f_org_index + 1 <= len(persona.scratch.f_daily_schedule_hourly_org):
      all_indices += [curr_f_org_index + 1]
    if curr_f_org_index + 2 <= len(persona.scratch.f_daily_schedule_hourly_org):
      all_indices += [curr_f_org_index + 2]

    curr_time_range = ""

    if debug:
      print("DEBUG")
      print(persona.scratch.f_daily_schedule_hourly_org)
      print(all_indices)

    summary_str = f"Today is {persona.scratch.curr_time.strftime('%B %d, %Y')}. "
    summary_str += "From "
    for index in all_indices:
      if debug:
        print("index", index)

      if index < len(persona.scratch.f_daily_schedule_hourly_org):
        start_min = 0
        for i in range(index):
          start_min += persona.scratch.f_daily_schedule_hourly_org[i][1]
        end_min = start_min + persona.scratch.f_daily_schedule_hourly_org[index][1]
        start_time = datetime.datetime.strptime(
          "00:00:00", "%H:%M:%S"
        ) + datetime.timedelta(minutes=start_min)
        end_time = datetime.datetime.strptime(
          "00:00:00", "%H:%M:%S"
        ) + datetime.timedelta(minutes=end_min)
        start_time_str = start_time.strftime("%H:%M%p")
        end_time_str = end_time.strftime("%H:%M%p")
        summary_str += f"{start_time_str} ~ {end_time_str}, {persona.name} is planning on {persona.scratch.f_daily_schedule_hourly_org[index][0]}, "
        if curr_f_org_index + 1 == index:
          curr_time_range = f"{start_time_str} ~ {end_time_str}"
    summary_str = summary_str[:-2] + "."

    prompt_input = {
      "identity_stable_set": persona.scratch.get_str_iss(),
      "broad_schedule_summary": summary_str,
      "persona_firstname": persona.scratch.get_str_firstname(),
      "persona_fullname": persona.scratch.name,
      "action": task,
      "action_duration": duration,
      "action_time_range": curr_time_range,
    }
    return prompt_input

  def __func_clean_up(
    gpt_response: TaskDecomposition, prompt="", debug=False
  ) -> list[list]:
    if debug:
      print(gpt_response)
      print("-==- -==- -==- ")
      print("(cleanup func): Enter function")

    final_task_list = []

    for count, subtask in enumerate(gpt_response.subtasks):
      task = subtask.task.strip().strip(".")

      # Get rid of "1)", "2)", etc. at start of string if it exists
      if task[1] == ")":
        task = task[2:].strip()
      # Get rid of "Isabella is " at start of string if it exists
      task = task.removeprefix(persona.scratch.get_str_firstname()).strip()
      task = task.removeprefix("is").strip()

      final_task_list += [[task, subtask.duration]]

      # Store any tool call in the persona's pending_tool_calls dict so that
      # plan.py can pick it up when this subtask becomes the active action.
      if not hasattr(persona.scratch, "pending_tool_calls"):
        persona.scratch.pending_tool_calls = {}

      if subtask.tool_call is not None:
        persona.scratch.pending_tool_calls[task] = {
          "name": subtask.tool_call.name,
          "args": subtask.tool_call.args,
        }
      elif persona.scratch.name in TOOL_ELIGIBLE_PERSONAS:
        # Auto-enforcer: if the LLM returned null for a chemistry-relevant task,
        # force a search_literature fallback so tool calls always fire for science work.
        task_words = set(task.lower().replace(",", " ").replace(".", " ").split())
        if task_words & CHEMISTRY_KEYWORDS:
          persona.scratch.pending_tool_calls[task] = {
            "name": "search_literature",
            "args": task[:80],
          }

    if debug:
      print("(cleanup func) Unpacked (final_task_list)): ", final_task_list)
      print("(cleanup func) Prompt:", prompt)

    total_expected_min = int(duration)

    if debug:
      print("(cleanup func) Expected Minutes:", total_expected_min)

    # TODO -- now, you need to make sure that this is the same as the sum of
    #         the current action sequence.
    curr_min_slot = [
      ["dummy", -1],
    ]  # (task_name, task_index)
    for count, split_task in enumerate(final_task_list):
      i_task = split_task[0]
      i_duration = split_task[1]

      i_duration -= i_duration % 5
      if i_duration > 0:
        for _j in range(i_duration):
          curr_min_slot += [[i_task, count]]
    curr_min_slot = curr_min_slot[1:]

    if len(curr_min_slot) > total_expected_min:
      last_task = curr_min_slot[60]
      for i in range(1, 6):
        curr_min_slot[-1 * i] = last_task
    elif len(curr_min_slot) < total_expected_min:
      last_task = curr_min_slot[-1]
      for i in range(total_expected_min - len(curr_min_slot)):
        curr_min_slot += [last_task]

    return_task_list = [
      ["dummy", -1],
    ]
    for task, _task_index in curr_min_slot:
      if task != return_task_list[-1][0]:
        return_task_list += [[task, 1]]
      else:
        return_task_list[-1][1] += 1
    final_task_list = return_task_list[1:]

    return final_task_list

  def __func_validate(gpt_response, prompt=""):
    try:
      __func_clean_up(gpt_response, prompt)
    except Exception as e:
      print("Validation failed: ", e)
      traceback.print_exc()
      return False
    return gpt_response

  def get_fail_safe():
    fs = [["idle", 5]]
    return fs

  gpt_param = {
    "engine": openai_config["model"],
    "max_tokens": 5000,
    "temperature": 0,
    "top_p": 1,
    "stream": False,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "stop": None,
  }
  prompt_file = get_prompt_file_path(__file__)
  prompt_input = create_prompt_input(persona, task, duration)
  prompt = create_prompt(prompt_input)
  fail_safe = get_fail_safe()

  output = safe_generate_structured_response(
    prompt,
    gpt_param,
    TaskDecomposition,
    5,
    fail_safe,
    __func_validate,
    __func_clean_up,
  )

  if verbose:
    print("DEBUG")
    print("PROMPT:")
    print(prompt)
    print("\nOUTPUT:")
    print(output)

  fin_output = []
  time_sum = 0
  for i_task, i_duration in output:
    time_sum += int(i_duration)

    # if time_sum < duration:
    if time_sum <= duration:
      fin_output += [[i_task, i_duration]]
    else:
      break

  ftime_sum = 0
  for _fi_task, fi_duration in fin_output:
    ftime_sum += fi_duration

  fin_output[-1][1] += duration - ftime_sum
  output = fin_output

  task_decomp = output
  ret = []
  for decomp_task, duration in task_decomp:
    ret += [[f"{task} ({decomp_task})", duration]]
  output = ret

  if verbose:
    print_run_prompts(prompt_file, persona, gpt_param, prompt_input, prompt, output)

  return output, [output, prompt, gpt_param, prompt_input, fail_safe]
