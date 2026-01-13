# from fastapi import FastAPI, Form, Request
# from fastapi.templating import Jinja2Templates
# from fastapi.responses import HTMLResponse

# import spacy
# from pydantic import BaseModel
# from typing import List
# from fastapi.staticfiles import StaticFiles
from __future__ import annotations

import os
from collections import OrderedDict
from typing import Any, Dict, List, Optional

import spacy
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# # Initialize FastAPI app
# app = FastAPI()

# # Initialize spaCy NLP model
# nlp = spacy.load("en_core_web_trf")

# # Initialize Jinja2 template engine
# templates = Jinja2Templates(directory="templates")

# # Mount the 'static' directory so that files in it can be accessed directly via URL
# app.mount("/static", StaticFiles(directory="static"), name="static")

# -----------------------------
# App and Templates
# -----------------------------
app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


# -----------------------------
# spaCy model loading
# -----------------------------
def load_spacy_model() -> spacy.language.Language:
    """
    Load a spaCy pipeline with a sensible fallback.

    Uses SPACY_MODEL env var if provided; otherwise tries a transformer model
    and falls back to a small model for easy local execution.
    """
    preferred = os.getenv("SPACY_MODEL", "en_core_web_trf")
    fallback = os.getenv("SPACY_FALLBACK_MODEL", "en_core_web_sm")

    try:
        return spacy.load(preferred)
    except OSError:
        return spacy.load(fallback)


nlp = load_spacy_model()


# -----------------------------
# Data model
# -----------------------------
class Event(BaseModel):
    trigger: str
    subject: List[str]
    object: List[str]
    time: List[str]
    location: List[str]
    confidence: float

# -----------------------------
# Helpers
# -----------------------------
def dedupe_preserve_order(items: List[str]) -> List[str]:
    """Deduplicate while preserving order."""
    return list(OrderedDict.fromkeys(items))


def extract_events(text: str, *, include_noun_triggers: bool = False):
    """
    Extract structured “event” records from free text using spaCy dependency parses and Named Entity Recognition.

    The function iterates through each sentence and treats each VERB and NOUN token as a
    potential event trigger. For each trigger, it builds an event dictionary containing:

    - trigger (str): the token text serving as the event trigger
    - subject (List[str]): token children with dependency labels nsubj/nsubjpass
    - object (List[str]): token children with dependency labels dobj/iobj/attr/pobj
    - time (List[str]): temporal expressions captured via NER (DATE, TIME) from both
      trigger-children and the full sentence, excluding common non-time patterns
      (e.g., “zero-day”, “10-year-old”)
    - location (List[str]): location-like entities captured via NER (GPE, LOC, ORG) from
      both trigger-children and the full sentence, plus additional prepositional-object
      heuristics for tokens attached to prepositions such as “in”, “at”, or “on”
    - confidence (float): a simple completeness score computed as the average presence
      of extracted fields:
          (len(subject) + len(object) + len(time) + len(location)) / 4

    Location post-processing attempts to expand partial matches (e.g., a single token
    inside a multi-word place name) by replacing the extracted location list with a
    matching noun chunk that contains the identified location token(s).

    Only events with at least a subject or an object are returned.

    Parameters
    ----------
    text : str
        Input text to process. The function expects that a global spaCy pipeline `nlp`
        is available and initialized with a dependency parser and NER components.

    Returns
    -------
    A list of extracted event dictionaries, one per detected trigger that yields
    at least a subject or an object.

    Notes
    -----
    - This is a heuristic, rule-based extractor; it may produce false positives,
      duplicate time/location entries, and trigger tokens that are not truly “events”.
    - The confidence score is not probabilistic; it is a lightweight completeness
      metric intended for ranking or filtering.
    """

    doc = nlp(text)
    events = []
    EXCLUDED_TIME_PATTERNS = {"zero-day", "zero day", "-year-old", "years old", "aged"}
    PREP_SET = {"in", "at", "on"}

    for sent in doc.sents:
        sent_chunks = list(sent.noun_chunks)

        for token in sent:
            if token.pos_ != "VERB" and not (include_noun_triggers and token.pos_ == "NOUN"):
                continue

            event: Dict[str, Any] = {
                "trigger": token.text,
                "subject": [],
                "object": [],
                "time": [],
                "location": [],
                "confidence": 0.0,
            }

            # Token children heuristics
            for child in token.children:
                if child.dep_ in {"nsubj", "nsubjpass"}:
                    event["subject"].append(child.text)

                if child.dep_ in {"dobj", "iobj", "attr", "pobj"}:
                    event["object"].append(child.text)

                if child.ent_type_ in {"DATE", "TIME"}:
                    if not any(pat in child.text.lower() for pat in EXCLUDED_TIME_PATTERNS):
                        event["time"].append(child.text)

                if child.ent_type_ in {"GPE", "LOC", "ORG"}:
                    event["location"].append(child.text)

                if (child.dep_ in {"pobj", "iobj"}) and any(
                    t.text.lower() in PREP_SET for t in child.head.lefts
                ):
                    event["location"].append(child.text)

            for ent in sent.ents:
                if ent.label_ in {"DATE", "TIME"}:
                    if not any(pat in ent.text.lower() for pat in EXCLUDED_TIME_PATTERNS):
                        event["time"].append(ent.text)

                if ent.label_ in {"GPE", "LOC", "ORG"}:
                    event["location"].append(ent.text)

            if event["location"]:
                loc_tokens = set(event["location"])
                expanded: Optional[str] = None
                for chunk in sent_chunks:
                    if any(tok.text in loc_tokens for tok in chunk):
                        expanded = chunk.text
                        break
                if expanded:
                    event["location"] = [expanded]

            event["subject"] = dedupe_preserve_order(event["subject"])
            event["object"] = dedupe_preserve_order(event["object"])
            event["time"] = dedupe_preserve_order(event["time"])
            event["location"] = dedupe_preserve_order(event["location"])

            filled_fields = sum([
                len(event["subject"]) > 0,
                len(event["object"]) > 0,
                len(event["time"]) > 0,
                len(event["location"]) > 0
            ])

            # Confidence (completeness) - should be between 0 and 1
            event["confidence"] = filled_fields / 4.0

            # Keep only events with at least a subject or object
            if event["subject"] or event["object"]:
                events.append(event)
    
    return events


# -----------------------------
# Routes
# -----------------------------
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/extract")
async def extract(request: Request, text: str = Form(...)):
    if not text.strip(): 
        error_message = "Text cannot be empty. Please enter some text."
        return templates.TemplateResponse(
            "index.html", 
            {"request": request, "events": [], "error_message": error_message}
        )
    
    events = extract_events(text, include_noun_triggers=False)
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "text": text, "events": events}
    )


# FastAPI main entry point to run the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
