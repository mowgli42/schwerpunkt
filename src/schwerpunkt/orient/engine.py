from __future__ import annotations

from schwerpunkt.models import (
    Contradiction,
    FactWithConfidence,
    HumanResolvedFact,
    Observation,
    OrientationResult,
    WorldModel,
)

NUMERIC_REVISION_TOLERANCE = 0.05


def _is_numeric(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def values_conflict(prior_value: object, new_value: object, tolerance: float = NUMERIC_REVISION_TOLERANCE) -> bool:
    """Return True when new observation contradicts prior fact (not a minimal belief revision)."""
    if prior_value == new_value:
        return False
    if _is_numeric(prior_value) and _is_numeric(new_value):
        prior_f = float(prior_value)
        new_f = float(new_value)
        if prior_f == 0:
            return abs(new_f) > tolerance
        return abs(new_f - prior_f) / abs(prior_f) > tolerance
    return True


def detect_contradictions(observation: Observation, model: WorldModel) -> list[Contradiction]:
    found: list[Contradiction] = []
    for signal in observation.signals:
        prior = model.known_facts.get(signal.key)
        if prior is None:
            continue
        if values_conflict(prior.value, signal.value):
            severity = "high" if prior.confidence > 0.8 else "low"
            found.append(
                Contradiction(
                    key=signal.key,
                    new_value=signal.value,
                    prior_value=prior.value,
                    severity=severity,
                    prior_confidence=prior.confidence,
                )
            )
    return found


def apply_human_resolutions(model: WorldModel) -> WorldModel:
    facts = dict(model.known_facts)
    contradictions = list(model.contradictions)
    for resolved in model.human_resolved_facts:
        facts[resolved.key] = FactWithConfidence(
            key=resolved.key, value=resolved.value, confidence=0.95
        )
        contradictions = [c for c in contradictions if c.key != resolved.key]
    return model.model_copy_update(known_facts=facts, contradictions=contradictions)


def orient_from_observation(
    observation: Observation,
    model: WorldModel,
    orientation_confidence_factor: float = 1.0,
) -> OrientationResult:
    model = apply_human_resolutions(model)
    contradictions = detect_contradictions(observation, model)
    active = contradictions + [c for c in model.contradictions if c.key not in {x.key for x in contradictions}]

    high_severity = [c for c in active if c.severity == "high"]
    if high_severity:
        return OrientationResult(
            updated_model=model.model_copy_update(contradictions=active),
            contradictions=active,
            requires_human_review=True,
            orientation_confidence=min(0.4, observation.confidence * 0.5),
        )

    facts = dict(model.known_facts)
    for signal in observation.signals:
        facts[signal.key] = FactWithConfidence(
            key=signal.key, value=signal.value, confidence=signal.confidence
        )

    updated = model.model_copy_update(known_facts=facts, contradictions=[])
    conf = observation.confidence * orientation_confidence_factor * 0.9
    return OrientationResult(
        updated_model=updated,
        contradictions=[],
        requires_human_review=False,
        orientation_confidence=conf,
    )


def merge_stub_orientation(model: WorldModel, stub_facts: dict[str, FactWithConfidence]) -> WorldModel:
    facts = dict(model.known_facts)
    facts.update(stub_facts)
    return model.model_copy_update(known_facts=facts, contradictions=[])
