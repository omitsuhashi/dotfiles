# Form and Choice Components

## Shared primitives

These primitives appear across Autocomplete and Select.

### `<el-options>`

- Hosts the popover list of choices
- Common attributes:
  - `popover`
  - `anchor`
  - `anchor-strategy`
- Common CSS variables:
  - `--anchor-gap`
  - `--anchor-offset`
- Common methods:
  - `togglePopover()`
  - `showPopover()`
  - `hidePopover()`
- Common transition data attributes:
  - `data-closed`
  - `data-enter`
  - `data-leave`
  - `data-transition`

Use explicit width classes when needed. Width is not automatically assigned.

### `<el-option>`

- Required attribute: `value`
- Optional attribute: `disabled`
- Read-only state: `aria-selected`

### `<el-selectedcontent>`

- Mirrors the content of the selected option automatically
- Most useful inside Select trigger buttons

## Autocomplete

### Main role

`<el-autocomplete>` wraps a text input that can accept freeform values or a selected suggestion.

### Important details

- Works with a native `<input>` and optional `<button>`
- Exposes read-only CSS variables:
  - `--input-width`
  - `--button-width`
- Options usually live in `<el-options popover>`

### Basic example

```html
<el-autocomplete>
  <input name="user" />
  <button type="button">Open</button>
  <el-options popover anchor="bottom start" class="w-(--input-width)">
    <el-option value="Wade Cooper">Wade Cooper</el-option>
    <el-option value="Tom Cooper">Tom Cooper</el-option>
  </el-options>
</el-autocomplete>
```

### Layout rules

- Use `anchor="bottom start"` for typical dropdown positioning.
- Use `w-(--input-width)` when the list should match the input width.
- Add `--anchor-gap` or `--anchor-offset` through utility classes when spacing needs adjustment.
- Disable the control by adding `disabled` to the inner `<input>`.

### Transition pattern

```html
<el-options
  popover
  class="transition transition-discrete data-closed:opacity-0 data-enter:duration-75 data-leave:duration-100"
>
  ...
</el-options>
```

## Select

### Main role

`<el-select>` is a styled alternative to native `<select>` with form integration.

### Main API

- Attributes:
  - `name`
  - `value`
- Events:
  - `input`
  - `change`
- Read-only CSS variable:
  - `--input-width`

### Typical structure

```html
<el-select name="status" value="active">
  <button type="button">
    <el-selectedcontent>Active</el-selectedcontent>
  </button>
  <el-options popover anchor="bottom start" class="w-(--button-width)">
    <el-option value="active">Active</el-option>
    <el-option value="inactive">Inactive</el-option>
  </el-options>
</el-select>
```

### Layout rules

- Use `w-(--button-width)` when the options should align to the trigger width.
- Disable the control by placing `disabled` on the trigger `<button>`.
- Positioning, gap, offset, and transitions use the same `el-options` rules as Autocomplete.

## Quick comparison

| Component | Value source | Freeform input | Trigger element |
| --- | --- | --- | --- |
| Autocomplete | Input text or selected option | Yes | Native `<input>` plus optional button |
| Select | Selected option only | No | Button with `el-selectedcontent` |

## Common mistakes

- Using `w-(--button-width)` for Autocomplete when the desired width is the input width.
- Forgetting `popover` on `el-options`, which disables popover behavior.
- Disabling the outer custom element instead of the inner native control.
