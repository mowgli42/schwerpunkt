from __future__ import annotations

import json
from pathlib import Path

from schwerpunkt.models import FactWithConfidence, Observation, Signal


def _load_scenario_data(path: Path) -> dict:
    return json.loads(path.read_text())


def observation_from_fixture(path: Path) -> Observation:
    data = _load_scenario_data(path)
    signals = [Signal(**s) for s in data.get("signals", [])]
    return Observation(
        signals=signals,
        failed_sensors=data.get("failed_sensors", []),
        confidence=data.get("confidence", 1.0),
        pattern_id=data.get("pattern_id"),
    )


def initial_facts_from_fixture(path: Path) -> dict[str, FactWithConfidence]:
    data = _load_scenario_data(path)
    return {k: FactWithConfidence(**v) for k, v in data.get("initial_facts", {}).items()}


def load_scenario_observation(fixtures_dir: Path, scenario: str) -> tuple[dict[str, FactWithConfidence], Observation]:
    path = fixtures_dir / "scenarios" / f"{scenario}.json"
    return initial_facts_from_fixture(path), observation_from_fixture(path)
