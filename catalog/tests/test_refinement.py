from project.state_extractor import extract_state


def test_seniority_extraction():
    messages = [{"role": "user", "content": "Need an adaptive test for a graduate hire."}]
    state = extract_state(messages)
    assert state["seniority"] == "entry"
    assert state["adaptive"] is True


def test_domain_extraction_sales():
    messages = [{"role": "user", "content": "We need a sales transformation assessment for reskilling."}]
    state = extract_state(messages)
    assert "sales" in state["domains"]
