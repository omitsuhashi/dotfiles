# Utility and Navigation Components

## Command palette

### Main role

`<el-command-palette>` filters and manages a list of predefined actions, usually inside a dialog.

### Main API

- Attributes:
  - `name`
  - `value`
- Event:
  - `change`
- Methods:
  - `setFilterCallback(cb)`
  - `reset()`

### Related pieces

- `<el-command-list>` contains focusable result items
- `<el-defaults>` holds suggestions shown with an empty query
- `<el-command-group>` groups related items
- `<el-no-results>` shows empty-state content
- `<el-command-preview for="...">` shows preview content for one active item

### Basic example

```html
<el-dialog>
  <dialog>
    <el-command-palette>
      <input autofocus placeholder="Search…" />
      <el-command-list>
        <button hidden type="button">Option #1</button>
        <button hidden type="button">Option #2</button>
      </el-command-list>
      <el-no-results hidden>No results found.</el-no-results>
    </el-command-palette>
  </dialog>
</el-dialog>
```

## Copy button

### Main role

`<el-copyable>` exposes text that a button can copy to the clipboard with the `--copy` command.

### Main API

`<el-copyable>`:

- Command:
  - `--copy`

Trigger button state:

- `data-copied` appears briefly after success
- `data-error` appears when copy fails

### Basic example

```html
<el-copyable id="snippet">npm install @tailwindplus/elements</el-copyable>

<button command="--copy" commandfor="snippet">
  <span class="in-data-copied:hidden">Copy</span>
  <span class="not-in-data-copied:hidden">Copied!</span>
</button>
```

## Tabs

### Main role

`<el-tab-group>` coordinates a keyboard-accessible tab list and its panels.

### Main API

`<el-tab-group>`:

- Method:
  - `setActiveTab(index)`

Related pieces:

- `<el-tab-list>` contains tab buttons
- `<el-tab-panels>` contains panels, with direct children treated as panels

### Basic example

```html
<el-tab-group>
  <el-tab-list>
    <button type="button">Tab 1</button>
    <button type="button">Tab 2</button>
  </el-tab-list>
  <el-tab-panels>
    <div>Content 1</div>
    <div hidden>Content 2</div>
  </el-tab-panels>
</el-tab-group>
```

### Server-rendered default state

The active tab is inferred from the first panel without `hidden`. This makes SSR-friendly markup straightforward.

## Common mistakes

- Forgetting that command palette items are just focusable children; no special item wrapper is required.
- Assuming copy feedback persists until manually reset. `data-copied` is temporary.
- Marking multiple tab panels as visible in the initial markup, which makes the active state ambiguous.
