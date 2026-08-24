from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable


def _when(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _step_index(spec: dict[str, Any]) -> dict[str, int]:
    return {step["name"]: index for index, step in enumerate(spec["steps"])}


def reconcile(spec: dict[str, Any], events: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Rebuild the controller plan from the event stream.

    This starter implementation intentionally contains several incident bugs.
    The benchmark asks the agent to repair it while preserving the public CLI.
    """
    steps = spec["steps"]
    step_index = _step_index(spec)
    as_of = _when(spec["as_of"])
    leases = {item["target"]: item for item in spec.get("leases", [])}

    states: dict[tuple[str, str], dict[str, Any]] = {}
    for step in steps:
        for target in step["targets"]:
            states[(step["name"], target)] = {
                "step": step["name"],
                "target": target,
                "status": "pending",
                "attempt": 0,
            }

    # BUG: event arrival order is not authoritative, but the incident code
    # applies events exactly as delivered.
    for event in events:
        key = (event["step"], event["target"])
        state = states.get(key)
        if state is None:
            continue
        if _when(event["occurred_at"]) > as_of:
            continue
        if event["kind"] == "deploy_started":
            state["attempt"] = event["attempt"]
            state["status"] = "running"
        elif event["kind"] == "health_passed":
            state["status"] = "healthy"
        elif event["kind"] == "health_failed":
            state["status"] = "failed"
        elif event["kind"] == "rollback_started":
            state["status"] = "rolling_back"
        elif event["kind"] == "rollback_completed":
            state["status"] = "rolled_back"

    def dependencies_ready(step: dict[str, Any]) -> bool:
        return all(
            states[(dependency, target)]["status"] == "healthy"
            for dependency in step.get("depends_on", [])
            for target in next(s for s in steps if s["name"] == dependency)["targets"]
        )

    actions: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []

    for step in steps:
        targets = step["targets"]
        if not dependencies_ready(step):
            for target in targets:
                state = states[(step["name"], target)]
                if state["status"] not in {"healthy", "running", "rolling_back"}:
                    blocked.append(
                        {"step": step["name"], "target": target, "reason": "dependency_not_complete"}
                    )
            continue

        active = sum(
            states[(step["name"], target)]["status"] == "running" for target in targets
        )
        slots = max(0, step["max_parallel"] - active)
        lease = leases.get(targets[0]) if targets else None

        for target in sorted(targets):
            state = states[(step["name"], target)]
            if state["status"] == "healthy":
                continue
            if state["status"] == "running":
                blocked.append({"step": step["name"], "target": target, "reason": "awaiting_health"})
                continue
            if state["status"] == "rolling_back":
                blocked.append(
                    {"step": step["name"], "target": target, "reason": "awaiting_rollback"}
                )
                continue
            if lease is None or _when(lease["expires_at"]) <= as_of:
                blocked.append(
                    {"step": step["name"], "target": target, "reason": "lease_unavailable"}
                )
                continue
            if slots == 0:
                blocked.append(
                    {"step": step["name"], "target": target, "reason": "parallel_limit"}
                )
                continue

            action = "retry_deploy" if state["status"] == "rolled_back" else "start_deploy"
            actions.append(
                {
                    "action": action,
                    "attempt": state["attempt"] + 1,
                    "lease_epoch": lease["epoch"],
                    "step": step["name"],
                    "target": target,
                }
            )
            slots -= 1

    ordered_states = [
        states[(step["name"], target)]
        for step in steps
        for target in sorted(step["targets"])
    ]
    return {
        "actions": actions,
        "as_of": spec["as_of"],
        "blocked": blocked,
        "rollout_id": spec["rollout_id"],
        "state": ordered_states,
    }
