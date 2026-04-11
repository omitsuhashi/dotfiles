---
name: tailwindplus-elements
description: Use when working with @tailwindplus/elements, Tailwind Plus HTML snippets, or el-* custom elements and you need installation guidance, React integration details, component API lookup, anchoring and transition behavior, or examples for autocomplete, dialog, disclosure, dropdown, popover, select, tabs, command palette, or copy button.
---

# Tailwind Plus Elements

## Overview

Use this skill to orient around Tailwind Plus Elements quickly without loading the full component reference into context. Keep this file lean, then read only the reference file that matches the component or integration question.

## When to Use

- Installing `@tailwindplus/elements` with CDN or npm
- Using Tailwind Plus HTML snippets that depend on `el-*` components
- Checking React-specific exports to avoid custom-element hydration issues
- Looking up component APIs, commands, events, anchoring, or transition hooks
- Comparing related primitives such as `el-options`, `el-option`, and `el-selectedcontent`

Do not use this skill for generic Tailwind CSS questions that do not involve Tailwind Plus Elements.

## Quick Workflow

1. Decide the integration mode first: CDN, npm, or React.
2. Identify the target component or primitive before loading references.
3. Read only the matching file in `references/`.
4. In React, prefer the React exports from `@tailwindplus/elements/react` over raw custom elements.
5. If adding DOM behavior around these components, wait for `elements:ready` unless the custom element is already registered.

## Reference Map

- `references/getting-started.md`
  Covers installation, browser support, React usage, and `elements:ready`.
- `references/form-and-choice-components.md`
  Covers Autocomplete, Select, and shared choice primitives.
- `references/overlay-and-disclosure-components.md`
  Covers Dialog, Disclosure, Dropdown menu, and Popover.
- `references/utility-and-navigation-components.md`
  Covers Command palette, Copy button, and Tabs.

## Common Mistakes

- Using raw `<el-*>` tags in React when React exports exist. Prefer the React wrapper components.
- Reading every reference file up front. Load only the component group you need.
- Adding custom DOM logic before Elements is ready. Check `customElements.get(...)` or wait for `elements:ready`.
- Treating `el-options` width or anchor behavior as automatic. Many layouts still need explicit classes or CSS variables.
- Mixing up similar primitives. `el-options` serves Autocomplete and Select, while `el-menu` belongs to Dropdown.
