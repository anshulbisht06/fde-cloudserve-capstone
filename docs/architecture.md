# Architecture

To be written as the components are built.

The planned flow: **ingest → classify → retrieve → route → generate → validate**, with three concerns that
run across all of them: the decision log, monitoring, and a feedback loop for human corrections. Design
choices, and the alternatives considered, are recorded in `docs/decisions.md`.
