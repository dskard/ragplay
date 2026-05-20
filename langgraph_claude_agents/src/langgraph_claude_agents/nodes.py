import json
import re
from typing import Any

from langgraph_claude_agents.agent import run_agent
from langgraph_claude_agents.state import IssueState


def _extract_json(text: str) -> Any:
    """Extract and parse the last JSON object or array from text that may contain surrounding content."""
    decoder = json.JSONDecoder()
    last_value = None
    found = False
    i = 0
    while i < len(text):
        if text[i] in ('{', '['):
            try:
                value, end = decoder.raw_decode(text, i)
                last_value = value
                found = True
                i = end
                continue
            except json.JSONDecodeError:
                pass
        i += 1
    if not found:
        raise json.JSONDecodeError("No JSON object or array found", text, 0)
    return last_value

_SETUP_PROMPT_TEMPLATE = """
Check that `gh` and `roborev` are available in PATH.
Then fetch issue #{issue_number} using `gh issue view {issue_number} --json title,body`.
Return ONLY a JSON object with keys "issue_title" and "issue_body".
If `gh` or `roborev` are not available, return a JSON object with key "error" describing what is missing.
"""


async def setup(state: IssueState) -> dict:
    prompt = _SETUP_PROMPT_TEMPLATE.format(issue_number=state["issue_number"])
    raw = await run_agent(prompt=prompt, allowed_tools=["Bash"], model=state.get("model"))
    try:
        data = _extract_json(raw)
    except json.JSONDecodeError:
        return {"error": f"setup agent returned non-JSON: {raw!r}"}
    if not isinstance(data, dict):
        return {"error": f"setup agent returned unexpected JSON type: {raw!r}"}
    if "error" in data:
        return {"error": data["error"]}
    try:
        return {
            "issue_title": data["issue_title"],
            "issue_body": data["issue_body"],
            "status": "setup_done",
        }
    except KeyError as exc:
        return {"error": f"setup agent response missing key: {exc}"}


_PLAN_BEHAVIORS_PROMPT_PREFIX = """
Given this GitHub issue body, return a JSON array of behavior strings for a TDD loop.
Order behaviors by dependency (foundational behaviors first).
Return ONLY the JSON array, nothing else.

Issue body:
"""

_AC_PATTERN = re.compile(
    r"## Acceptance Criteria\s*\n(.*?)(?=\n##|\Z)", re.DOTALL
)
_CHECKBOX_PATTERN = re.compile(r"-\s+\[\s\]\s+(.*)")


def _extract_acceptance_criteria(issue_body: str) -> list[str]:
    match = _AC_PATTERN.search(issue_body)
    if not match:
        return []
    return _CHECKBOX_PATTERN.findall(match.group(1))


async def plan_behaviors(state: IssueState) -> dict:
    prompt = _PLAN_BEHAVIORS_PROMPT_PREFIX + state["issue_body"]
    raw = await run_agent(prompt=prompt, allowed_tools=["Bash"], model=state.get("model"))
    try:
        behaviors = _extract_json(raw)
        if not isinstance(behaviors, list):
            raise ValueError("expected a JSON array")
    except (json.JSONDecodeError, ValueError) as exc:
        return {"error": f"plan_behaviors agent returned invalid JSON: {exc}"}
    return {
        "behaviors": behaviors,
        "current_behavior_index": 0,
        "acceptance_criteria": _extract_acceptance_criteria(state["issue_body"]),
    }


_TDD_BEHAVIOR_PROMPT_PREFIX = """
Implement this behavior using a TDD red/green/commit/review cycle:

Behavior: """

_TDD_BEHAVIOR_PROMPT_SUFFIX = """

Steps:
1. Write one failing test that verifies this behavior through the public interface.
   Run the full test suite and confirm only the new test fails.
2. Write the minimal implementation to make the test pass.
   Run the full test suite and confirm all tests pass.
3. Stage only the files created or modified for this behavior and commit with a
   Conventional Commits message (type(scope): subject, blank line, bullet body).
4. Run `roborev wait`. If the review fails, fix the findings, re-commit, and repeat
   until the review passes.

Return ONLY a JSON object:
- {"status": "success"} when all steps complete successfully
- {"error": "<description>"} if any step fails unrecoverably
"""


async def tdd_behavior(state: IssueState) -> dict:
    idx = state.get("current_behavior_index", 0)
    behaviors = state.get("behaviors", [])
    if idx >= len(behaviors):
        return {"error": f"tdd_behavior called with index {idx} but only {len(behaviors)} behaviors exist"}
    behavior = behaviors[idx]
    prompt = _TDD_BEHAVIOR_PROMPT_PREFIX + behavior + _TDD_BEHAVIOR_PROMPT_SUFFIX
    raw = await run_agent(prompt=prompt, allowed_tools=["Bash", "Read", "Write", "Edit"], model=state.get("model"))
    try:
        data = _extract_json(raw)
    except json.JSONDecodeError:
        return {"error": f"tdd_behavior agent returned non-JSON: {raw!r}"}
    if not isinstance(data, dict):
        return {"error": f"tdd_behavior agent returned unexpected JSON type: {raw!r}"}
    if "error" in data and data["error"]:
        return {"error": data["error"]}
    return {"current_behavior_index": idx + 1}


_VERIFY_AC_PROMPT_PREFIX = """
You are verifying that all acceptance criteria for a GitHub issue are covered by the codebase.

Acceptance criteria to check:
"""

_VERIFY_AC_PROMPT_SUFFIX = """
Search the codebase using Bash and Read tools to find evidence that each criterion is covered
(test files or implementation files that clearly address the described behavior).

Return ONLY a JSON object:
{"all_covered": true, "uncovered": []} when every criterion is covered.
{"all_covered": false, "uncovered": ["<criterion text>", ...]} listing only the uncovered ones.
"""


async def verify_ac(state: IssueState) -> dict:
    ac = state.get("acceptance_criteria", [])
    if not ac:
        return {}
    criteria_list = "\n".join(f"- {c}" for c in ac)
    prompt = _VERIFY_AC_PROMPT_PREFIX + criteria_list + _VERIFY_AC_PROMPT_SUFFIX
    raw = await run_agent(prompt=prompt, allowed_tools=["Bash", "Read"], model=state.get("model"))
    try:
        data = _extract_json(raw)
    except json.JSONDecodeError:
        return {"error": f"verify_ac agent returned non-JSON: {raw!r}"}
    if not isinstance(data, dict):
        return {"error": f"verify_ac agent returned unexpected JSON type: {raw!r}"}
    if data.get("all_covered"):
        return {}
    uncovered = data.get("uncovered", [])
    if not uncovered:
        return {}
    existing = state.get("behaviors", [])
    existing_set = set(existing)
    new_items = [u for u in uncovered if u not in existing_set]
    if not new_items:
        return {}
    new_index = len(existing)
    return {
        "behaviors": existing + new_items,
        "current_behavior_index": new_index,
    }


_FULL_TEST_PROMPT = """
Detect the test runner by checking these files in order:
1. CLAUDE.md - look for a test command hint
2. Justfile - look for a test recipe
3. Makefile - look for a test target
4. pyproject.toml (run: uv run pytest)
5. package.json (run: npm test)

Run the full test suite.

Return ONLY a JSON object:
- {"status": "success"} when all tests pass
- {"error": "<description>"} if any tests fail
"""


async def full_test(state: IssueState) -> dict:
    raw = await run_agent(prompt=_FULL_TEST_PROMPT, allowed_tools=["Bash", "Read"])
    try:
        data = _extract_json(raw)
    except json.JSONDecodeError:
        return {"error": f"full_test agent returned non-JSON: {raw!r}"}
    if not isinstance(data, dict):
        return {"error": f"full_test agent returned unexpected JSON type: {raw!r}"}
    if "error" in data and data["error"]:
        return {"error": data["error"]}
    return {}


_BRANCH_REVIEW_PROMPT = """
Run a roborev branch review using `roborev review-branch` and fix any
findings until the review passes.

Return ONLY a JSON object:
- {"status": "success"} when the review passes with no actionable findings
- {"error": "<description>"} if the review cannot be completed or findings
  cannot be resolved
"""


async def branch_review(state: IssueState) -> dict:
    raw = await run_agent(
        prompt=_BRANCH_REVIEW_PROMPT,
        allowed_tools=["Bash", "Read", "Write", "Edit"],
    )
    try:
        data = _extract_json(raw)
    except json.JSONDecodeError:
        return {"error": f"branch_review agent returned non-JSON: {raw!r}"}
    if not isinstance(data, dict):
        return {"error": f"branch_review agent returned unexpected JSON type: {raw!r}"}
    if "error" in data and data["error"]:
        return {"error": data["error"]}
    return {}


async def teardown(state: IssueState) -> dict:
    error = state.get("error", "")
    if error:
        return {"status": "error"}
    return {"status": "done"}
