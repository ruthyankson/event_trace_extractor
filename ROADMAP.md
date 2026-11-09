# Roadmap

**Goal:** turn Event Trace Extractor into an open-source tool that converts free-text
incident reports (workplace safety, clinical, and disaster reports) into structured,
searchable event timelines: who did what, when, where, and how complete each record is.

The extractor is rule-based (spaCy dependency parsing and named entity recognition).
All examples and test data are synthetic or public; the project does not process
real people's personal data.

## Milestone 1: Solid foundation

- [ ] Unit tests for `extract_events` (triggers, subjects, objects, time, location, confidence)
- [ ] GitHub Actions CI running tests on every push
- [ ] Move extraction logic into its own module, separate from the web app
- [ ] Type hints and linting

## Milestone 2: Use it anywhere

- [ ] Command-line tool: `event-trace report.txt --format json`
- [ ] Package for `pip install`
- [ ] JSON API endpoint alongside the web interface

## Milestone 3: More inputs

- [ ] Batch processing for folders of text files
- [ ] CSV input (one report per row)
- [ ] PDF text extraction

## Milestone 4: Better outputs

- [ ] Export to JSON and CSV
- [ ] Timeline view in the web interface
- [ ] Filter events by confidence and field
- [ ] Keep the submitted text in the input box after extraction

## Milestone 5: Domain rule packs

- [ ] Configurable YAML rules for triggers, time and location patterns
- [ ] Starter packs for workplace safety, clinical, and disaster reports
- [ ] Attach times and locations to the right event instead of the whole sentence
- [ ] Recognise more location prepositions (for example "to", "near", "from")
- [ ] Return full noun phrases for subjects and objects (for example "first aid", "wrong dose")

## Milestone 6: Launch v1.0

- [ ] Documentation and worked examples with synthetic incident reports
- [ ] Hosted demo
- [ ] Tagged v1.0 release
