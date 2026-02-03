# Input format (publish-chat-epic)

## Minimal example
~~~markdown
# Epic: Improve idempotency contract

## Goal
- Align behavior and docs
~~~

~~~markdown
# ISSUE-1: Update middleware
## Tasks
- ...
~~~

~~~markdown
# ISSUE-2: Update docs
## Tasks
- ...
~~~

Rules:
- Blocks with headings containing "Epic" are treated as Epics (case-insensitive).
- Each Epic groups following blocks until the next Epic.
- If no Epic is found, the first block is treated as the Epic (backward compatible).
- First heading line inside each block becomes the GitHub Issue title and is removed from body.
