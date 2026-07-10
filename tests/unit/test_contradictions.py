from schwerpunkt.models import FactWithConfidence, Observation, Signal, WorldModel
from schwerpunkt.orient.engine import detect_contradictions, orient_from_observation, values_conflict


def test_detect_contradiction():
    wm = WorldModel(known_facts={"case_status": FactWithConfidence(key="case_status", value="closed", confidence=0.92)})
    obs = Observation(signals=[Signal(key="case_status", value="open", confidence=0.85)])
    contradictions = detect_contradictions(obs, wm)
    assert len(contradictions) == 1
    assert contradictions[0].severity == "high"


def test_clean_update_no_contradiction():
    wm = WorldModel()
    obs = Observation(signals=[Signal(key="account_balance", value=1005, confidence=0.9)])
    result = orient_from_observation(obs, wm)
    assert not result.contradictions
    assert result.updated_model.known_facts["account_balance"].value == 1005
    assert result.orientation_confidence >= 0.8


def test_numeric_belief_revision_not_contradiction():
    wm = WorldModel(
        known_facts={
            "account_balance": FactWithConfidence(key="account_balance", value=1000, confidence=0.9)
        }
    )
    obs = Observation(signals=[Signal(key="account_balance", value=1005, confidence=0.9)])
    assert not detect_contradictions(obs, wm)
    assert not values_conflict(1000, 1005)
    result = orient_from_observation(obs, wm)
    assert not result.requires_human_review
    assert result.updated_model.known_facts["account_balance"].value == 1005


def test_large_numeric_change_is_contradiction():
    wm = WorldModel(
        known_facts={
            "account_balance": FactWithConfidence(key="account_balance", value=1000, confidence=0.9)
        }
    )
    obs = Observation(signals=[Signal(key="account_balance", value=2000, confidence=0.9)])
    assert len(detect_contradictions(obs, wm)) == 1


def test_contradiction_blocks_overwrite():
    wm = WorldModel(known_facts={"case_status": FactWithConfidence(key="case_status", value="closed", confidence=0.92)})
    obs = Observation(signals=[Signal(key="case_status", value="open", confidence=0.85)])
    result = orient_from_observation(obs, wm)
    assert result.requires_human_review
    assert result.orientation_confidence < 0.5
    assert result.updated_model.known_facts["case_status"].value == "closed"
