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
- First block = Epic
- Remaining blocks = sub-issues
- First heading line inside each block becomes the GitHub Issue title and is removed from body.
