import json
import re
from pathlib import Path
from typing import List, Optional

import faiss
from sentence_transformers import SentenceTransformer


DATA_PATH = Path(__file__).resolve().parent.parent / "shl_product_catalog_clean.json"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
COMPATIBLE_DOMAIN_TERMS = {
    "personality",
    "cognitive",
    "simulation",
    "communication",
    "sales",
    "safety",
    "healthcare",
    "contact_center",
    "graduate",
    "finance",
}

def normalize_text(text: Optional[str]) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", str(text).strip().lower())

class CatalogRetriever:
    def __init__(self, model_name: str = MODEL_NAME):
        self.model = SentenceTransformer(model_name)
        self.catalog = self._load_catalog()
        self.index = self._build_index()

    def _load_catalog(self) -> List[dict]:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def _build_index(self) -> faiss.IndexFlatIP:
        texts = [f"{item.get('name','')} {item.get('description','')}" for item in self.catalog]
        embeddings = self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(embeddings)
        self.embeddings = embeddings
        return index

    def retrieve(self, query: str, top_k: int = 10) -> List[dict]:
        query_emb = self.model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
        scores, ids = self.index.search(query_emb, top_k)
        results = []
        for score, idx in zip(scores[0], ids[0]):
            if idx < 0:
                continue
            item = self.catalog[idx].copy()
            item["score"] = float(score)
            results.append(item)
        return results
    def find_by_name(self, text):
        if not text:
            return None

        alias_map = {
            "gsa": "global skills assessment",
            "gsa?": "global skills assessment",
            "opq": "occupational personality questionnaire",
            "opq32r": "occupational personality questionnaire opq32r",
            "mq": "motivation questionnaire",
            "verify g+": "verify g+",
            "verifyg+": "verify g+",
            "verify g": "verify g+",
        }

        normalized_text = normalize_text(text)
        candidate_texts = []
        if normalized_text in alias_map:
            candidate_texts.append(alias_map[normalized_text])
        else:
            candidate_texts.append(normalized_text)

        cleaned_text = re.sub(r"[^a-z0-9]+", " ", normalized_text).strip()
        if cleaned_text:
            candidate_texts.append(cleaned_text)

        if normalized_text.startswith("opq"):
            candidate_texts.append("occupational personality questionnaire")
        if normalized_text.startswith("gsa"):
            candidate_texts.append("global skills assessment")

        candidate_texts = list(dict.fromkeys(candidate_texts))
        print("[DEBUG] lookup text:", candidate_texts)

        for item in self.catalog:
            name = normalize_text(item.get("name", ""))
            for candidate in candidate_texts:
                if candidate in name or name in candidate:
                    return item

        return None

    def metadata_filter(self, items: List[dict], domains: List[str], languages: Optional[List[str]] = None, remote: Optional[bool] = None, adaptive: Optional[bool] = None) -> List[dict]:
        filtered = []
        
        for item in items:
            print(
            item.get("name"),
            "remote =", item.get("remote"),
            "adaptive =", item.get("adaptive")
            )
            reasons = []
            if languages:
                item_languages = [lang.lower() for lang in item.get("languages", [])]
                if not any(lang.lower() in item_languages for lang in languages):
                    reasons.append("language")

            if remote is not None:
                item_remote = str(item.get("remote", "")).strip().lower()
                if item_remote in ("yes", "no"):
                    item_remote = (item_remote == "yes")
                if item_remote != remote:
                     reasons.append("remote")

            if adaptive is not None:
                item_adaptive = str(item.get("adaptive", "")).strip().lower()
                if item_adaptive in ("yes", "no"):
                    item_adaptive = (item_adaptive == "yes")
                if item_adaptive != adaptive:
                     reasons.append("adaptive")
            if reasons:
                print("[DEBUG] filtered out:", item.get("name"), "because", ", ".join(reasons))
                continue
            filtered.append(item)
        print("[DEBUG] metadata_filter kept:", len(filtered), "of", len(items), "candidates")
        return filtered
