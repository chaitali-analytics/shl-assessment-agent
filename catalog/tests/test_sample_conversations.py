import pytest
from fastapi.testclient import TestClient
from project.app import app
from tests.sample_conversations import SAMPLE_CONVERSATIONS

client = TestClient(app)

@pytest.mark.parametrize("conversation", SAMPLE_CONVERSATIONS)
def test_sample_conversations(conversation):
    response = client.post("/chat", json={"messages": conversation["messages"]})
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "recommendations" in data
    assert "end_of_conversation" in data
    for keyword in conversation["expected_keywords"]:
        assert keyword.lower() in data["reply"].lower() or any(keyword.lower() in rec["name"].lower() for rec in data["recommendations"])
