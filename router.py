"""
router.py
---------
Parses intent.markdown files and routes user messages to the right tool.

An intent.markdown file looks like:

    ## calculator
    keywords: calculate, math, plus, times, +, -, *, /
    examples:
      - what is 5 + 3
    tool: calculator
    extract: expression

The parser reads every `## section` as one intent. `match_intent` picks
the intent with the most keyword hits for a given user message.
"""

import re
from pathlib import Path


def load_intents(path: str = "intents/intents.md") -> list:
    """Read the intents markdown file and return a list of intent dicts."""
    text = Path(path).read_text(encoding="utf-8")
    intents = []
    # Split on "\n## " — each chunk after the first is one intent block.
    blocks = re.split(r"\n## ", text)
    for block in blocks[1:]:
        lines = block.strip().split("\n")
        name = lines[0].strip()
        keywords, tool_name, extract = [], None, None
        for line in lines[1:]:
            stripped = line.strip()
            if stripped.startswith("keywords:"):
                raw = stripped.split(":", 1)[1]
                keywords = [k.strip().lower() for k in raw.split(",") if k.strip()]
            elif stripped.startswith("tool:"):
                tool_name = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("extract:"):
                extract = stripped.split(":", 1)[1].strip()
        if tool_name:
            intents.append({
                "name": name,
                "keywords": keywords,
                "tool": tool_name,
                "extract": extract,
            })
    return intents


def match_intent(message: str, intents: list):
    """Score each intent by keyword overlap with the message. Best wins."""
    msg = message.lower()
    best, best_score = None, 0
    for intent in intents:
        score = sum(1 for kw in intent["keywords"] if kw in msg)
        if score > best_score:
            best, best_score = intent, score
    return best


# Common filler phrases we want to strip before passing text to a tool.
_FILLER = re.compile(
    r"\b(what\s+is|whats|what's|tell\s+me|please|the|can\s+you|could\s+you|"
    r"would\s+you|say|to|of|a|an)\b",
    flags=re.IGNORECASE,
)


def extract_argument(message: str, intent: dict) -> dict:
    """
    Very simple arg-extraction: strip the intent's keywords out of the
    message, strip common filler words, and return whatever's left as
    the value for the intent's `extract` parameter.

    This is deliberately dumb — it's enough for a demo and easy to explain.
    """
    if not intent.get("extract"):
        return {}
    msg = message
    # Strip keywords (longest first, so we remove "+" last)
    for kw in sorted(intent["keywords"], key=len, reverse=True):
        msg = re.sub(re.escape(kw), " ", msg, flags=re.IGNORECASE)
    msg = _FILLER.sub(" ", msg)
    msg = re.sub(r"\s+", " ", msg).strip(" ?.!,")
    return {intent["extract"]: msg}
