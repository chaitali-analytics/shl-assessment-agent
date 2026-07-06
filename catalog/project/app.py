from pyexpat.errors import messages
import re
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

from project.comparison import compare_items
from project.guardrails import is_off_topic, is_prompt_injection
from project.retriever import CatalogRetriever
from project.state_extractor import extract_state

app = FastAPI(title="SHL Catalog Agent")

retriever: Optional[CatalogRetriever] = None


class ChatMessage(BaseModel):
    role: str = Field(...)
    content: str = Field(...)


class ChatRequest(BaseModel):
    messages: List[ChatMessage]


class Recommendation(BaseModel):
    name: str
    url: str
    test_type: str


class ChatResponse(BaseModel):
    reply: str
    recommendations: List[Recommendation]
    end_of_conversation: bool


class HealthResponse(BaseModel):
    status: str = "ok"


def get_retriever() -> CatalogRetriever:
    global retriever
    if retriever is None:
        retriever = CatalogRetriever()
    return retriever


def normalize_text(text: Optional[str]) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", str(text).strip().lower())

def merge_state(current: Dict[str, Any], previous: Dict[str, Any]) -> Dict[str, Any]:
    for key in ["role", "seniority", "remote", "adaptive"]:
        if current.get(key) is None:
            current[key] = previous.get(key)

    for key in [
        "skills",
        "domains",
        "requested_products",
        "excluded_products",
    ]:
        if not current.get(key):
            current[key] = previous.get(key, [])

    return current

def should_clarify(state: Dict[str, Any]) -> bool:
    if state.get("comparison"):
        return False

    query_text = state.get("query_text", "")
    if is_prompt_injection(query_text) or is_off_topic(query_text):
        return False

    role_present = bool(state.get("role"))
    seniority_present = bool(state.get("seniority"))
    skills_present = bool(state.get("skills"))
    domains_present = bool(state.get("domains"))
    remote_present = state.get("remote") is not None
    adaptive_present = state.get("adaptive") is not None

    # Search whenever we have ANY meaningful hiring information.
    if (
        role_present
        or seniority_present
        or skills_present
        or domains_present
        or remote_present
        or adaptive_present
    ):
        return False

    # Only clarify if the request contains no useful information.
    return True


def rank_item(item: Dict[str, Any], context: Dict[str, Any]) -> float:
    score = 0.0

    search_text = " ".join(
        [
            str(item.get("name", "")),
            str(item.get("description", "")),
            str(item.get("search_text", "")),
        ]
    ).lower()

    role = normalize_text(context.get("role"))

    if role:
        if role in search_text:
            score += 40.0
    
    role_words = role.split()

    for word in role_words:
        if len(word) > 3 and word in search_text:
            score += 8.0

    for skill in context.get("skills", []):
        normalized_skill = normalize_text(skill)
        if normalized_skill and normalized_skill in search_text:
            score += 10.0

    seniority = context.get("seniority")
    if seniority:
        job_levels = item.get("job_levels", []) or []
        if any(seniority in str(level).lower() for level in job_levels):
            score += 8.0

    if context.get("remote") is not None:
        if item.get("remote") == context.get("remote"):
            score += 5.0
        else:
            score -= 2.0

    if context.get("adaptive") is not None:
        if item.get("adaptive") == context.get("adaptive"):
            score += 5.0
        else:
            score -= 2.0

    for domain in context.get("domains", []):
        if domain and domain in search_text:
            score += 20.0

    if item.get("status") != "ok":
        score -= 20.0

    #if context.get("requested_products") and any(str(product).lower() in search_text for product in context.get("requested_products", [])):
     #   score += 20.0
    
    for product in context.get("requested_products", []):

        if product == "personality":
            if (
                "personality" in search_text
                or "behavior" in search_text
                or "behaviour" in search_text
                or "opq" in search_text
            ):
                score += 25

        elif product == "cognitive":
            if any(
                word in search_text
                for word in [
                    "ability",
                    "aptitude",
                    "reasoning",
                    "numerical",
                    "verbal",
                    "deductive",
                    "inductive",
                ]
            ):
                score += 25

        elif product == "simulation":
            if any(
                word in search_text
                for word in [
                    "simulation",
                    "situational",
                    "scenario",
                ]
            ):
                score += 25

    if context.get("query_text"):
        query_terms = set(normalize_text(context.get("query_text", "")).split())
        score += 2 * min(sum(1 for term in query_terms if term and term in search_text),6)

    return score


def compose_reply(state: Dict[str, Any], recommendations: List[Dict[str, Any]]) -> str:
    if is_prompt_injection(state.get("query_text", "")):
        return "I cannot follow that request. I only provide SHL assessment guidance from the SHL catalog."
    if is_off_topic(state.get("query_text", "")):
        return "I can only discuss SHL assessments from the SHL catalog. Please keep the request focused on SHL products."
    if state.get("comparison"):
        item_a, item_b = state["comparison"]
        return compare_items(item_a, item_b)
    if should_clarify(state):
        return "Could you tell me the role or key skills you're hiring for? For example: Java Developer, Sales Executive, Graduate, or Project Manager."
    if recommendations:
        role = state.get("role")
        seniority = state.get("seniority")
        skills = ", ".join(state.get("skills", []))
        domains = ", ".join(state.get("domains", []))

        if seniority and skills:
            return f"For a {seniority} {role}, I found {len(recommendations)} SHL assessments that align with {skills} and {domains or 'the requirements you shared'}."
        if skills:
            return f"I found {len(recommendations)} SHL assessments that align with your {skills} requirements."
        if seniority:
            return f"I found {len(recommendations)} SHL assessments that fit a {seniority} {role}."
        return f"I found {len(recommendations)} SHL assessments that fit the requirements you shared."
    return "I could not identify matching SHL assessments from the catalog yet. Please share more detail such as the role, seniority, or capabilities you need."


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    messages = [
        m.model_dump() if hasattr(m, "model_dump") else m.dict()
        for m in request.messages
    ]
    user_text = " ".join(m["content"] for m in messages if m["role"] == "user")

    if is_prompt_injection(user_text):
        return ChatResponse(
            reply="I couldn't find assessments matching all of the requested constraints. Try relaxing one of the requirements such as adaptive or remote.",
            recommendations=[],
            end_of_conversation=False,
        )

    if any(
        phrase in normalize_text(user_text)
        for phrase in [
            "thank you",
            "thanks",
            "that is all",
            "that's all",
            "thats all",
            "bye",
            "goodbye",
            "appreciate it",
            "see you",
            "i'm done",
            "im done",
        ]
    ):
        return ChatResponse(
            reply="You're welcome! Glad I could help. If you need more SHL assessment recommendations later, feel free to ask.",
            recommendations=[],
            end_of_conversation=True,
        )

    if is_off_topic(user_text):
        return ChatResponse(
            reply="I can only discuss SHL assessments from the SHL catalog. Please keep the request focused on SHL products.",
            recommendations=[],
            end_of_conversation=False,
        )

    state = extract_state(messages)

    # Merge information from previous user turns
    history_text = " ".join(
        m["content"]
        for m in messages[:-1]
        if m["role"] == "user"
    )

    if history_text:
        history_state = extract_state([
            {
                "role": "user",
                "content": history_text
            }
        ])

        # Fill missing single-value fields
        for key in [
            "role",
            "seniority",
            "remote",
            "adaptive"
        ]:
            if state.get(key) is None:
                state[key] = history_state.get(key)

        # Fill missing list fields
        for key in [
            "skills",
            "domains",
            "requested_products",
            "excluded_products"
        ]:
            if not state.get(key):
                state[key] = history_state.get(key, [])

    # Debug prints
    print("[DEBUG] extracted role:", state.get("role"))
    print("[DEBUG] extracted skills:", state.get("skills"))
    print("[DEBUG] extracted domains:", state.get("domains"))
    print("[DEBUG] seniority:", state.get("seniority"))
    print("[DEBUG] remote:", state.get("remote"))
    print("[DEBUG] adaptive:", state.get("adaptive"))
    print("[DEBUG] query_text:", state.get("query_text"))

    if state.get("comparison"):
        print("[DEBUG] comparison:", state["comparison"])

        name1, name2 = state["comparison"]

        retriever_client = get_retriever()

        item1 = retriever_client.find_by_name(name1)
        item2 = retriever_client.find_by_name(name2)

        print("[DEBUG] item1:", item1)
        print("[DEBUG] item2:", item2)

        if not item1 or not item2:
            return ChatResponse(
                reply="I couldn't find one or both SHL assessments in the catalog.",
                recommendations=[],
                end_of_conversation=False,
            )

        return ChatResponse(
            reply=compare_items(item1, item2),
            recommendations=[],
            end_of_conversation=False,
        )
    
    print("[DEBUG] should_clarify =", should_clarify(state))

    if should_clarify(state):
        return ChatResponse(
            reply="I need more detail on the role, seniority, or capabilities you are hiring for before recommending SHL assessments.",
            recommendations=[],
            end_of_conversation=False,
        )

    retriever_client = get_retriever()
    retrieved = retriever_client.retrieve(state.get("query_text", ""), top_k=50)
    print("Retrieved:", len(retrieved))
    print("[DEBUG] retrieved candidates:", len(retrieved))
    for item in retrieved[:3]:
        print("[DEBUG] retrieved candidate:", item.get("name"), "score=", item.get("score"))

    filtered = retriever_client.metadata_filter(
        retrieved,
        domains=state.get("domains", []),
        languages=state.get("languages"),
        remote=state.get("remote"),
        adaptive=state.get("adaptive"),
    )
    print("Filtered:", len(filtered))

    reranked = sorted(filtered, key=lambda item: rank_item(item, state), reverse=True)[:10]
    print("Reranked:", len(reranked))
    print("[DEBUG] metadata-filtered candidates:", len(filtered))
    for item in reranked[:10]:
        print("[DEBUG] ranked candidate:", item.get("name"), "score=", rank_item(item, state))

    recommendations = [
        Recommendation(
            name=item.get("name", "Unknown assessment"),
            url=item.get("link", ""),
            test_type=item.get("test_type", "U"),
        )
        for item in reranked
    ]

    if not recommendations:
        return ChatResponse(
            reply="I could not identify matching SHL assessments from the catalog. Please share more specifics such as required capabilities or role.",
            recommendations=[],
            end_of_conversation=False,
        )

    reply = compose_reply(state, reranked)
    return ChatResponse(
        reply=reply,
        recommendations=recommendations,
        end_of_conversation=False,
    )