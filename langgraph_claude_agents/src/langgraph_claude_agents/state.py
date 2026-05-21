from typing import NotRequired, TypedDict


class IssueState(TypedDict):
    issue_number: int
    issue_title: str
    issue_body: str
    behaviors: list[str]
    current_behavior_index: int
    acceptance_criteria: list[str]
    error: str
    status: str
    model: NotRequired[str | None]
