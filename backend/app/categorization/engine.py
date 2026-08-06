"""Ren logikk for å foreslå kategori ut fra en transaksjonsbeskrivelse.

Ingen databaseavhengighet - tar en streng inn, returnerer et forslag (eller
None hvis ingenting treffer, som mappes til "Ukategorisert" lenger opp).
"""

import re
from dataclasses import dataclass

from app.categorization.rules import RULES, Rule


@dataclass(frozen=True)
class CategoryMatch:
    parent: str
    child: str
    matched_keyword: str
    rule: Rule


def _normalize(description: str) -> str:
    collapsed = re.sub(r"\s+", " ", description.upper()).strip()
    return f" {collapsed} "


def categorize(description: str) -> CategoryMatch | None:
    """Returner det mest spesifikke regeltreffet for beskrivelsen, eller None."""
    normalized = _normalize(description)

    best: CategoryMatch | None = None
    for rule in RULES:
        for keyword in rule.keywords:
            if keyword.strip() and keyword.strip() in normalized:
                candidate = CategoryMatch(rule.parent, rule.child, keyword.strip(), rule)
                if best is None or len(candidate.matched_keyword) > len(best.matched_keyword):
                    best = candidate

    return best
