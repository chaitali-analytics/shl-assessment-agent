from project.comparison import compare_items


def make_item(name, test_type, adaptive, remote, languages, description):
    return {
        "name": name,
        "test_type": test_type,
        "adaptive": adaptive,
        "remote": remote,
        "languages": languages,
        "description": description,
        "url": f"https://example.com/{name.replace(' ','-').lower()}"
    }


def test_compare_items_differs_by_type():
    item_a = make_item("OPQ32r", "P", False, True, ["English (USA)"], "Personality test")
    item_b = make_item("GSA", "K", False, True, ["English (USA)"], "Skills test")
    text = compare_items(item_a, item_b)
    assert "Test type" in text
    assert "OPQ32r" in text


def test_compare_items_same_type():
    item_a = make_item("OPQ32r", "P", False, True, ["English (USA)"], "Personality test")
    item_b = make_item("OPQ Leadership Report", "P", False, True, ["English (USA)"], "Leadership report")
    text = compare_items(item_a, item_b)
    assert "Here is a comparison" in text
