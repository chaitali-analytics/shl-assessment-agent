from typing import Dict, List, Optional


def compare_items(item_a: Dict, item_b: Dict) -> str:
    differences: List[str] = []
    if item_a.get("test_type") != item_b.get("test_type"):
        differences.append(f"Test type: {item_a['name']} is {item_a['test_type']} while {item_b['name']} is {item_b['test_type']}.")
    if item_a.get("adaptive") != item_b.get("adaptive"):
        differences.append(
            f"Adaptive: {item_a['name']} is {'adaptive' if item_a['adaptive'] else 'not adaptive'}, while {item_b['name']} is {'adaptive' if item_b['adaptive'] else 'not adaptive'}."
        )
    if item_a.get("remote") != item_b.get("remote"):
        differences.append(
            f"Remote: {item_a['name']} is {'remote-friendly' if item_a['remote'] else 'not remote-friendly'} while {item_b['name']} is {'remote-friendly' if item_b['remote'] else 'not remote-friendly'}."
        )
    if item_a.get("languages") != item_b.get("languages"):
        differences.append(
            f"Languages: {item_a['name']} supports {', '.join(item_a.get('languages', []) or ['unspecified'])} while {item_b['name']} supports {', '.join(item_b.get('languages', []) or ['unspecified'])}."
        )
    if item_a.get("description") != item_b.get("description"):
        differences.append(f"Descriptions: {item_a['name']}: {item_a.get('description','')} | {item_b['name']}: {item_b.get('description','')}")
    if not differences:
        return f"Both assessments are listed in the SHL catalog and have similar metadata.\n{item_a.get('url')}\n{item_b.get('url')}"

    return "Here is a comparison based on the SHL catalog data:\n" + "\n".join(differences) + f"\n{item_a.get('url')}\n{item_b.get('url')}"
