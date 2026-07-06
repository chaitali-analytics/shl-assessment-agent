import pytest
from fastapi.testclient import TestClient
from project.app import app
from project.state_extractor import extract_state
from project.retriever import CatalogRetriever

client = TestClient(app)


def test_extract_state_basic_role():
    messages = [{"role": "user", "content": "Hiring a Java developer who works with stakeholders."}]
    state = extract_state(messages)
    assert state["role"] == "software engineer"
    assert "java" in state["domains"]


def test_retriever_returns_items():
    retriever = CatalogRetriever()
    results = retriever.retrieve("Java developer assessment")
    assert len(results) > 0
    assert all("name" in item for item in results)


def test_metadata_filter_remote():
    retriever = CatalogRetriever()
    results = retriever.retrieve("remote assessment")
    filtered = retriever.metadata_filter(results, domains=[], remote=True)
    assert all(item["remote"] for item in filtered)


def test_extract_state_classifies_skills_and_comparison():
    messages = [
        {
            "role": "user",
            "content": "Compare OPQ and Verify G+ for a Java developer with Spring Boot and SQL skills.",
        }
    ]
    state = extract_state(messages)
    assert state["role"] == "software engineer"
    assert "java" in state["skills"]
    assert "spring" in state["skills"]
    assert "sql" in state["skills"]
    assert state["comparison"] is not None


def test_follow_up_conversation_accumulates_context():
    messages = [
        {"role": "user", "content": "Recommend assessments for a Business Analyst."},
        {"role": "assistant", "content": "What capabilities are important?"},
        {"role": "user", "content": "Strong communication and analytical skills."},
    ]
    state = extract_state(messages)
    assert state["role"] == "business analyst"
    assert "communication" in state["domains"]
    assert "cognitive" in state["domains"]


def test_java_query_returns_recommendations():
    response = client.post(
        "/chat",
        json={"messages": [{"role": "user", "content": "I am hiring a Java Developer with Spring Boot and SQL experience."}]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["recommendations"], data
    assert data["reply"], data


def test_opq_vs_gsa_comparison_returns_comparison_reply():
    response = client.post(
        "/chat",
        json={"messages": [{"role": "user", "content": "What is the difference between OPQ and GSA?"}]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["recommendations"] == []
    assert "comparison" in data["reply"].lower() or "descriptions" in data["reply"].lower()


def test_end_of_conversation_is_detected():
    response = client.post(
        "/chat",
        json={"messages": [{"role": "user", "content": "Thanks for your help."}]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["end_of_conversation"] is True
    assert "welcome" in data["reply"].lower()
