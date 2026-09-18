# ChatGPT Raw Dataset Inbox

This folder is only for raw candidate JSONL files supplied by ChatGPT.

The Claude/Nextora pipeline validates every file placed here before any row can be promoted into the clean dataset.

Expected raw file name for the current pilot:

```text
chatgpt_step_by_step_0001_0100_raw.jsonl
```

Current target: a 100-row pilot batch.

Files in this folder are not clean data. They are raw candidates only.

Before any row may enter the clean dataset, every line must pass schema validation, dedupe, cross-dedupe, scoring, safety/firewall checks, and reporting.
