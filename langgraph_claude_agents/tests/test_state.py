from langgraph_claude_agents.state import IssueState


def test_issue_state_has_all_eight_fields():
    fields = IssueState.__required_keys__ | IssueState.__optional_keys__
    assert "issue_number" in fields
    assert "issue_title" in fields
    assert "issue_body" in fields
    assert "behaviors" in fields
    assert "current_behavior_index" in fields
    assert "acceptance_criteria" in fields
    assert "error" in fields
    assert "status" in fields
    assert len(fields) == 8
