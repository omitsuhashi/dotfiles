# Repository Router

- This repository contains a persistent LLM-maintained wiki under `<knowledge-root>/`.
- When bootstrapping, ingesting, querying, or linting the wiki, read `<knowledge-root>/AGENTS.md` first and treat that directory as the knowledge root.
- When another workflow creates durable planning or decision documents, including superpowers outputs such as roadmap, ADR, spec, design doc, or implementation plan, save them under `<knowledge-root>/wiki/...` according to `<knowledge-root>/AGENTS.md` instead of using repo-root `docs/` defaults.
- Keep repo-root guidance here short. Do not duplicate wiki-wide rules in this file.
