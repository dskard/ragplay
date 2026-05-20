# LangGraph Claude Agents

A Python program that implements a GitHub issue end-to-end using LangGraph for orchestration and the Claude Agent SDK for autonomous execution within each node.

## Language

**Graph**:
The LangGraph `StateGraph` that defines all nodes, edges, and routing logic for the issue implementation workflow.
_Avoid_: Pipeline, workflow, chain

**Node**:
A single async Python function in the graph that sends one prompt to the Claude Agent SDK and updates state with the result.
_Avoid_: Step, stage, handler

**State**:
The `TypedDict` instance that carries data between nodes across the entire graph execution.
_Avoid_: Context, payload, data

**Behavior**:
One discrete, testable unit of functionality derived from the issue body, implemented via one TDD red/green/commit/review cycle.
_Avoid_: Feature, task, story, requirement

**TDD cycle**:
The red/green/commit/review sequence executed once per behavior: write failing test, make it pass, commit, run roborev.
_Avoid_: TDD loop, test loop, iteration

**Checkpoint**:
A SqliteSaver snapshot of graph state after each node completes, enabling resume after crash using the same `--issue` number.
_Avoid_: Snapshot, save point

**Thread**:
A LangGraph execution identity keyed by `issue-{number}`, used to look up the correct checkpoint for a given issue.
_Avoid_: Run, session, execution ID

**Teardown node**:
The terminal node that always executes, whether the graph succeeded or failed, to ensure cleanup runs.
_Avoid_: Finally block, cleanup step, exit node

## Relationships

- A **Graph** contains exactly seven **Nodes**: setup, plan_behaviors, tdd_behavior, verify_ac, full_test, branch_review, teardown
- A **State** is shared across all **Nodes** in a single **Thread**
- A **Thread** maps to exactly one GitHub issue and one **Checkpoint** database entry
- Each **Behavior** is implemented via exactly one **TDD cycle**
- The **Teardown node** receives control from any **Node** that sets `error` in **State**

## Example dialogue

> **Dev:** "Should the tdd_behavior node loop internally or does the graph loop back to it?"
> **Domain expert:** "The graph loops — a back-edge returns to the tdd_behavior node until `current_behavior_index` reaches the end of `behaviors`. The node itself handles exactly one behavior per invocation."

## Flagged ambiguities

- "loop" was used to describe both the graph back-edge and the Claude Agent SDK's internal tool-use loop — resolved: "loop" in this context always means the LangGraph back-edge; Claude's internal execution is called its "agent loop" and is not modeled in the graph.
