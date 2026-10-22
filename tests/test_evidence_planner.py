"""Query planner: deterministic routing, ID/version extraction, preserved uncertainty."""
import pytest

from controlshift.evidence.planner import (
    CONTROL_MAPPING,
    CROSS_VERSION,
    SINGLE_VERSION,
    UNSUPPORTED,
    extract_controls,
    extract_versions,
    plan_query,
)


@pytest.mark.parametrize("text,expected", [
    ("What changed in CSF 2.0?", ["2.0"]),
    ("Compare version 1.1 and v2.0 please", ["1.1", "2.0"]),
    ("csf1.1 vs CSF 2.0", ["1.1", "2.0"]),
    ("see section 1.1 and page 2.0 of the PDF", []),  # section/page numbers are not versions
    ("score of 21.1 or 12.05", []),
    ("What is in 1.1?", ["1.1"]),
    ("no versions here", []),
])
def test_extract_versions(text, expected):
    assert extract_versions(text) == expected


def test_extract_controls_normalizes_and_deduplicates():
    refs, unknown = extract_controls("Does pr.at-1 equal PR.AT-01, and what about GV.SC and GV?")
    assert [(r.raw, r.normalized, r.level) for r in refs] == [
        ("pr.at-1", "PR.AT-01", "subcategory"), ("GV.SC", "GV.SC", "category")]
    assert unknown == []


def test_unknown_function_code_is_reported_not_guessed():
    refs, unknown = extract_controls("What is ZZ.AB-01 and e.g. i.e. things?")
    assert refs == [] and unknown == ["ZZ.AB-01"]
    plan = plan_query("What is ZZ.AB-01?")
    assert plan.controls == [] and any("ZZ.AB-01" in u for u in plan.uncertainties)


@pytest.mark.parametrize("question,qtype", [
    ("What does GV.SC-03 require?", SINGLE_VERSION),
    ("What does CSF 1.1 say about data at rest?", SINGLE_VERSION),
    ("How should we handle logging?", SINGLE_VERSION),
    ("How does GV.SC-03 map to CSF 1.1?", CONTROL_MAPPING),
    ("Which 1.1 subcategories correspond to GV.OC-01?", CONTROL_MAPPING),
    ("Compare PR.AT-1 between versions", CONTROL_MAPPING),
    ("PR.AT-1 in CSF 1.1 and 2.0", CONTROL_MAPPING),
    ("What are the differences between CSF 1.1 and 2.0?", CROSS_VERSION),
    ("What is new in CSF 2.0?", CROSS_VERSION),
    ("How do the crosswalk mappings work?", CROSS_VERSION),
    ("", UNSUPPORTED),
    ("   ?!  ", UNSUPPORTED),
])
def test_routing(question, qtype):
    assert plan_query(question).query_type == qtype


def test_uncertainty_is_preserved():
    p = plan_query("How should we handle logging?")
    assert p.explicit_versions == [] and any("No framework version" in u for u in p.uncertainties)
    p = plan_query("What is new in CSF 2.0?")
    assert p.explicit_versions == ["2.0"] and any("baseline" in u for u in p.uncertainties)
    p = plan_query("What did the previous version require for access control?")
    assert any("relative version wording" in u for u in p.uncertainties)
    p = plan_query("Which controls were removed in 2.0?")
    assert any("no explicit 'removed' status" in u for u in p.uncertainties)
    assert plan_query("What does GV.SC-03 require?").uncertainties == []


def test_planner_is_pure_and_deterministic():
    q = "Compare GV.OC-01 and PR.AT-1 across CSF 1.1 and 2.0"
    assert plan_query(q).to_dict() == plan_query(q).to_dict()


# ---- regression: incidental keywords must not override a clear single-version request -------------
@pytest.mark.parametrize("question", [
    "What new technologies like AI does CSF 2.0 address?",
    "How are changes in the threat landscape handled in CSF 2.0?",
    "How does CSF 1.1 treat newly discovered vulnerabilities?",
    "What is the relationship between risk and governance in CSF 2.0?",
    "Which added protections apply to remote workers in CSF 1.1?",
    "What does GV.SC-03 say about new suppliers?",
    "How should a newly hired administrator be trained?",
])
def test_incidental_words_do_not_trigger_comparison(question):
    plan = plan_query(question)
    assert plan.query_type == SINGLE_VERSION
    assert "change_idiom" not in plan.cues and plan.explicit_versions in ([], ["1.1"], ["2.0"])


@pytest.mark.parametrize("question,qtype", [
    ("Compare CSF 1.1 and 2.0", CROSS_VERSION),
    ("What changed from CSF 1.1 to 2.0?", CROSS_VERSION),
    ("How does GV.SC-03 map to CSF 1.1?", CONTROL_MAPPING),
    ("What is new in CSF 2.0?", CROSS_VERSION),
    ("What's new in version 2.0", CROSS_VERSION),
    ("Which subcategories were added in CSF 2.0?", CROSS_VERSION),
    ("What was removed since CSF 1.1?", CROSS_VERSION),
    ("What changed for PR.AT-1?", CONTROL_MAPPING),
    ("Differences between the two versions for access control", CROSS_VERSION),
    ("CSF 1.1 versus CSF 2.0 governance", CROSS_VERSION),
])
def test_genuine_comparisons_still_detected(question, qtype):
    assert plan_query(question).query_type == qtype


def test_new_cue_is_recorded_only_for_new_style_idioms():
    assert "change:new" in plan_query("What is new in CSF 2.0?").cues
    assert "change:new" not in plan_query("What changed from CSF 1.1 to 2.0?").cues
    assert "change:new" not in plan_query("Compare CSF 1.1 and 2.0 for new suppliers").cues


@pytest.mark.parametrize("question", ["What changed?", "What is new?", "Which controls were added?"])
def test_unanchored_change_wording_is_ambiguous_not_a_guess(question):
    plan = plan_query(question)
    assert plan.query_type == SINGLE_VERSION and plan.explicit_versions == []
    notes = " ".join(plan.uncertainties)
    assert "could ask how the framework changed" in notes and "no comparison was assumed" in notes
    assert "No framework version was named" in notes  # both versions are still searched
