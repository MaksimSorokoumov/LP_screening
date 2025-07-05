"""OpenAI GPT client wrapper.

Handles calling ChatCompletion API to get readability and recommendations.
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import List, Optional

import openai

from app.parsers.html_parser import ParsedPage

logger = logging.getLogger(__name__)

__all__ = ["AIResult", "analyze_with_gpt"]

# Configure OpenAI key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")


@dataclass
class AIResult:
    readability: str
    recommendations: List[str] = field(default_factory=list)
    raw: Optional[str] = None  # raw response for debugging


_SYSTEM_PROMPT = (
    "You are an expert landing page optimization assistant. "
    "Return JSON only. Keys: readability (easy/medium/hard), recommendations (list of 5 short strings)."
)


def _build_user_prompt(parsed: ParsedPage) -> str:
    headings = []
    for lvl, lst in parsed.headings.items():
        for h in lst:
            headings.append(f"H{lvl}: {h}")
    headings_text = " | ".join(headings[:10])  # limit to 10 headings to save tokens

    prompt = (
        "Landing page snapshot:\n"
        f"Title: {parsed.title or 'N/A'}\n"
        f"Meta description present: {bool(parsed.meta_description)}\n"
        f"Word count: {parsed.word_count}\n"
        f"Headings: {headings_text}\n"
        f"Forms: {parsed.forms_count}\n"
        f"Images missing alt: {parsed.images_without_alt}/{parsed.images_total}\n"
        "Provide evaluation."
    )
    return prompt


def analyze_with_gpt(parsed: ParsedPage, model: str = "gpt-3.5-turbo") -> AIResult | None:
    """Call OpenAI and get AIResult. Returns None on failure."""
    if not openai.api_key:
        logger.warning("OPENAI_API_KEY is not set. Skipping AI analysis.")
        return None

    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": _build_user_prompt(parsed)},
    ]

    try:
        response = openai.ChatCompletion.create(model=model, messages=messages)
        content = response.choices[0].message.content.strip()
        # Attempt to parse JSON
        try:
            data = json.loads(content)
            readability = str(data.get("readability", "unknown"))
            recs = [str(r) for r in data.get("recommendations", [])][:5]
        except json.JSONDecodeError:
            readability = "unknown"
            recs = content.split("\n")[:5]
        return AIResult(readability=readability, recommendations=recs, raw=content)
    except Exception as exc:  # noqa: BLE001
        logger.exception("OpenAI call failed: %s", exc)
        return None 