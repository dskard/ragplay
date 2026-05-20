import json
import re

from langgraph_claude_agents.agent import run_agent
from langgraph_claude_agents.state import IssueState

_SETUP_PROMPT_TEMPLATE = """
Check that `gh` and `roborev` are available in PATH.
Then fetch issue #{issue_number} using `gh issue view {issue_number} --json title,body`.
Return ONLY a JSON object with keys "issue_title" and "issue_body".
If `gh` or `roborev` are not available, return a JSON object with key "error" describing what is missing.
"""


async def setup(state: IssueState) -> dict:
    prompt = _SETUP_PROMPT_TEMPLATE.format(issue_number=state["issue_number"])
    raw = await run_agent(prompt=prompt, allowed_tools=["Bash"])
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {"error": f"setup agent returned non-JSON: {raw!r}"}
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


_PLAN_BEHAVIORS_PROMPT_TEMPLATE = """
Given this GitHub issue body, return a JSON array of behavior strings for a TDD loop.
Order behaviors by dependency (foundational behaviors first).
Return ONLY the JSON array, nothing else.

Issue body:
{issue_body}
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
    prompt = _PLAN_BEHAVIORS_PROMPT_TEMPLATE.format(issue_body=state["issue_body"])
    raw = await run_agent(prompt=prompt, allowed_tools=["Bash"])
    try:
        behaviors = json.loads(raw)
        if not isinstance(behaviors, list):
            raise ValueError("expected a JSON array")
    except (json.JSONDecodeError, ValueError) as exc:
        return {"error": f"plan_behaviors agent returned invalid JSON: {exc}"}
    return {
        "behaviors": behaviors,
        "current_behavior_index": 0,
        "acceptance_criteria": _extract_acceptance_criteria(state["issue_body"]),
    }


async def tdd_behavior(state: IssueState) -> dict:
    return {"current_behavior_index": state.get("current_behavior_index", 0) + 1}


async def verify_ac(state: IssueState) -> dict:
    return {}


async def full_test(state: IssueState) -> dict:
    return {}


async def branch_review(state: IssueState) -> dict:
    return {}


async def teardown(state: IssueState) -> dict:
    return {"status": "done"}
