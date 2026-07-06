import re
from typing import Dict, List, Optional

ROLE_SYNONYMS = {
    "software engineer": ["developer", "software engineer", "programmer", "coder", "software developer", "rust engineer", "backend engineer", "full-stack engineer", "full stack engineer"],
    "business analyst": ["business analyst", "analyst", "data analyst", "business analytics", "financial analyst"],
    "project manager": ["project manager", "pm", "manager", "program manager", "people manager"],
    "data scientist": ["data scientist", "data engineer", "machine learning engineer"],
    "customer service agent": ["customer service agent", "contact center agent", "contact centre agent", "call centre agent", "call center agent"],
    "healthcare administrator": ["healthcare admin", "healthcare administrator", "medical admin", "clinical admin"],
    "graduate management trainee": ["management trainee", "graduate management trainee", "management trainee scheme", "graduate trainee"],
}

KEYWORD_MAP = {
    "personality": ["personality", "behavior", "behaviour", "opq", "gsa"],
    "cognitive": ["cognitive", "aptitude", "ability", "numerical", "verbal", "reasoning", "logical", "analytical", "analysis"],
    "simulation": ["simulation", "situational", "situational judgement", "situational judgment", "scenario", "scenarios"],
    "communication": ["communication", "stakeholder", "leadership", "team", "interpersonal", "influencing"],
    "sales": ["sales", "reskill", "re-skill", "transformation"],
    "safety": ["safety", "dependability", "reliability", "compliance"],
    "healthcare": ["hipaa", "medical", "healthcare", "patient"],
    "contact_center": ["contact center", "contact centre", "call center", "call centre", "customer service", "svar"],
    "graduate": ["graduate", "management trainee", "entry-level", "final-year", "final year"],
}

SKILL_KEYWORDS = {
    "java": ["java", "spring", "spring boot", "sql", "aws", "docker", "python", "rust"],
    "spring": ["spring", "spring boot"],
    "sql": ["sql"],
    "aws": ["aws", "amazon web services"],
    "docker": ["docker"],
    "python": ["python"],
    "rust": ["rust"],
}

SENIORITY_PATTERNS = {
    "entry": ["entry-level", "entry level", "junior", "graduate"],
    "mid": ["mid-level", "mid level", "mid professional", "experienced", "3 years", "4 years", "5 years"],
    "senior": ["senior", "lead", "principal"],
    "manager": ["manager", "management", "people manager"],
    "director": ["director", "executive"],
}

COMPARISON_MARKERS = ["compare", "comparison", "difference between", "versus", "vs", "vs."]


def normalize_text(text: Optional[str]) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", str(text).strip().lower())


def extract_role(text: str) -> Optional[str]:
    normalized = normalize_text(text)
    for canonical, synonyms in ROLE_SYNONYMS.items():
        for synonym in synonyms:
            if synonym in normalized:
                return canonical
    role_patterns = [
        r"hiring a ([a-z0-9 \-]+?)(?: for| with| who| around| at|$)",
        r"looking for (?:an? )?([a-z0-9 \-]+?)(?: for| with| who| around| at|$)",
        r"need(?: an)? assessment for ([a-z0-9 \-]+?)(?: for| with| who| around| at|$)",
    ]
    for pattern in role_patterns:
        match = re.search(pattern, normalized)
        if match:
            candidate = match.group(1).strip()
            if candidate and len(candidate.split()) <= 4:
                return "software engineer" if any(term in candidate for term in ["developer", "engineer", "programmer", "coder"]) else candidate
    return None


def extract_seniority(text: str) -> Optional[str]:
    normalized = normalize_text(text)
    for seniority, patterns in SENIORITY_PATTERNS.items():
        for pattern in patterns:
            if pattern in normalized:
                return seniority
    return None


def extract_domains(text: str) -> List[str]:
    normalized = normalize_text(text)
    domains = []
    for domain, keywords in KEYWORD_MAP.items():
        if any(keyword in normalized for keyword in keywords):
            domains.append(domain)
    for skill in extract_skills(text):
        if skill not in domains:
            domains.append(skill)
    return domains


def extract_skills(text: str) -> List[str]:
    normalized = normalize_text(text)
    skills = []
    for skill, keywords in SKILL_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            if skill not in skills:
                skills.append(skill)
    return skills


def detect_comparison_query(text: str) -> Optional[List[str]]:
    normalized = normalize_text(text)
    match = re.search(r"difference between\s+(.+?)\s+and\s+(.+)", normalized)
    if match:
        return [match.group(1).strip(), match.group(2).strip()]
    if not any(marker in normalized for marker in COMPARISON_MARKERS):
        return None
    candidates = re.split(r"\s+(?:and|with|against|versus|vs\.?|compare|difference between)\s+", normalized)
    parsed = [
        re.sub(r"[^\w\s]", "", candidate).strip()
        for candidate in candidates
        if candidate.strip()
    ]

    if len(parsed) >= 2:
        return parsed[:2]
    return None


def extract_state(messages: List[Dict]) -> Dict:
    state = {
        "role": None,
        "seniority": None,
        "skills": [],
        "domains": [],
        "remote": None,
        "adaptive": None,
        "requested_products": [],
        "excluded_products": [],
        "comparison": None,
        "query_text": "",
    }
    for message in messages:
        if message.get("role") != "user":
            continue
        content = normalize_text(message.get("content", ""))
        
        if "personality" in content or "behavior" in content or "behaviour" in content or "opq" in content:
            if "personality" not in state["requested_products"]:
                state["requested_products"].append("personality")

        if "cognitive" in content or "aptitude" in content or "ability" in content:
            if "cognitive" not in state["requested_products"]:
                state["requested_products"].append("cognitive")

        if "simulation" in content or "situational" in content:
            if "simulation" not in state["requested_products"]:
                state["requested_products"].append("simulation")
                
        if not content:
            continue
        state["query_text"] = f"{state['query_text']} {content}".strip()

        role = extract_role(content)
        if role and not state["role"]:
            state["role"] = role

        seniority = extract_seniority(content)
        if seniority and not state["seniority"]:
            state["seniority"] = seniority

        for domain in extract_domains(content):
            if domain not in state["domains"]:
                state["domains"].append(domain)

        for skill in extract_skills(content):
            if skill not in state["skills"]:
                state["skills"].append(skill)
        if "personality" in content:
            if "personality" not in state["requested_products"]:
                state["requested_products"].append("personality")

        if "cognitive" in content:
            if "cognitive" not in state["requested_products"]:
                state["requested_products"].append("cognitive")

        if "simulation" in content:
            if "simulation" not in state["requested_products"]:
                state["requested_products"].append("simulation")

        if "remote" in content or "work from home" in content:
            state["remote"] = True
        if "onsite" in content or "in person" in content:
            state["remote"] = False
        if "adaptive" in content:
            state["adaptive"] = True
        if "non-adaptive" in content or "not adaptive" in content:
            state["adaptive"] = False

        comparison = detect_comparison_query(content)
        if comparison and not state["comparison"]:
            state["comparison"] = comparison

    state["query_text"] = state["query_text"].strip()
    return state
