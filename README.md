# Event Trace Extractor

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Turn free text into structured events: **what happened, who was involved, when, and where**.

Event Trace Extractor is a rule-based NLP web app built with Python, FastAPI, and spaCy.
Paste in a narrative and it returns a list of events, each with its trigger, subject,
object, time, location, and a completeness score.

![Event Trace Extractor web interface](assets/imgs/event_extractor.jpg)

## Why

Many important records are written as free text: workplace incident reports, clinical
incident notes, and disaster reports. They are easy to write but hard to search,
compare, or analyze. The long-term goal of this project is to turn reports like these
into structured, searchable event timelines. See the [roadmap](ROADMAP.md).

## Features

- **Event detection:** identifies action verbs that trigger events
- **Entity extraction:** captures subjects and objects using dependency parsing
- **Time tagging:** extracts dates and times, ignoring look-alikes such as "10-year-old"
- **Location detection:** finds places using named entities and prepositional phrases
  ("in", "at", "on"), expanded to full noun phrases
- **Completeness score:** rates how complete each event record is, from 0.0 to 1.0
- **Web interface:** paste text and see results instantly

## Quick start

```bash
# Clone the repository
git clone https://github.com/ruthyankson/event_trace_extractor.git
cd event_trace_extractor

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies and a spaCy model
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Start the app, then open http://localhost:8000
uvicorn main:app --reload
```

### Choosing a spaCy model

The app tries the more accurate transformer model (`en_core_web_trf`) first and falls
back to the small model (`en_core_web_sm`). You can choose explicitly with environment
variables:

```bash
export SPACY_MODEL=en_core_web_trf          # Windows PowerShell: $env:SPACY_MODEL="en_core_web_trf"
export SPACY_FALLBACK_MODEL=en_core_web_sm
```

## Example

**Input:**

```text
John walked to the park yesterday. He met Sarah at noon.
```

**Output:**

```json
[
  {
    "trigger": "walked",
    "subject": ["John"],
    "object": [],
    "time": ["yesterday"],
    "location": ["park"],
    "confidence": 0.75
  },
  {
    "trigger": "met",
    "subject": ["He"],
    "object": ["Sarah"],
    "time": ["noon"],
    "location": [],
    "confidence": 0.75
  }
]
```

## How it works

1. spaCy splits the text into sentences and parses each one.
2. Every verb is treated as a potential event trigger.
3. Subjects and objects come from the trigger's grammatical dependents
   (`nsubj`, `nsubjpass`, `dobj`, `iobj`, `attr`, `pobj`).
4. Times come from `DATE` and `TIME` entities; locations from `GPE`, `LOC`, and `ORG`
   entities plus prepositional phrases.
5. Duplicates are removed and each event gets a completeness score.
6. Only events with at least a subject or an object are kept.

### Completeness score

The score is the share of the four fields (subject, object, time, location) that
contain data:

| Fields filled | Score |
| --- | --- |
| 4 of 4 | 1.0 |
| 3 of 4 | 0.75 |
| 2 of 4 | 0.5 |
| 1 of 4 | 0.25 |

It measures how complete a record is, not how likely it is to be correct.

## Known limitations

- Times and locations are taken from the whole sentence, so events in the same sentence
  share them.
- As a rule-based tool, it can produce false positives and miss events phrased unusually.
- English only for now.

These are tracked in the [roadmap](ROADMAP.md).

## Project structure

```text
main.py            FastAPI app and extraction logic
templates/         HTML template for the web interface
static/styles/     CSS
assets/imgs/       Screenshots
ROADMAP.md         Planned work
```

## Data and privacy

All examples and test data in this repository are synthetic or public. The project is
not designed to process real people's personal data.

## Contributing

Issues and suggestions are welcome. Please open an issue to discuss a change before
submitting a pull request.

## License

Released under the [MIT License](LICENSE).
