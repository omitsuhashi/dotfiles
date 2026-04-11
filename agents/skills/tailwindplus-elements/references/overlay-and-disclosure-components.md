# Overlay and Disclosure Components

## Dialog

### Main role

`<el-dialog>` wraps native `<dialog>` and adds consistent modal behavior, outside-click dismissal, scroll locking, and reliable exit transitions.

### Main API

- Attribute: `open`
- Events:
  - `open`
  - `close`
  - `cancel`
- Methods:
  - `show()`
  - `hide()`
- Transition data attributes:
  - `data-closed`
  - `data-enter`
  - `data-leave`
  - `data-transition`

### Related pieces

- `<dialog>` still handles `show-modal` and `close` commands
- `<el-dialog-backdrop>` is the transition-friendly backdrop
- `<el-dialog-panel>` is the click-inside safe area

### Basic example

```html
<button command="show-modal" commandfor="delete-profile" type="button">
  Delete profile
</button>

<el-dialog>
  <dialog id="delete-profile" class="backdrop:bg-transparent">
    <el-dialog-backdrop class="pointer-events-none bg-black/50 transition data-closed:opacity-0" />
    <el-dialog-panel class="bg-white transition data-closed:opacity-0 data-closed:scale-95">
      <form method="dialog">
        <button command="close" commandfor="delete-profile" type="button">Cancel</button>
      </form>
    </el-dialog-panel>
  </dialog>
</el-dialog>
```

## Disclosure

### Main role

`<el-disclosure>` toggles inline content such as accordions and expandable sections.

### Main API

- Attributes:
  - `hidden`
  - `open`
- Methods:
  - `show()`
  - `hide()`
  - `toggle()`
- Commands:
  - `--show`
  - `--hide`
  - `--toggle`
- Transition data attributes:
  - `data-closed`
  - `data-enter`
  - `data-leave`
  - `data-transition`

### Basic example

```html
<button command="--toggle" commandfor="faq-1" type="button">
  Toggle answer
</button>

<el-disclosure id="faq-1" hidden class="transition data-closed:opacity-0">
  Hidden content
</el-disclosure>
```

## Dropdown menu

### Main role

`<el-dropdown>` wires a trigger button to an anchored `<el-menu>`.

### Main API

`<el-menu>` supports:

- Attributes:
  - `popover`
  - `open`
  - `anchor`
  - `anchor-strategy`
- CSS variables:
  - `--anchor-gap`
  - `--anchor-offset`
- Methods:
  - `togglePopover()`
  - `showPopover()`
  - `hidePopover()`
- Transition data attributes:
  - `data-closed`
  - `data-enter`
  - `data-leave`
  - `data-transition`

### Basic example

```html
<el-dropdown>
  <button type="button">Options</button>
  <el-menu popover anchor="bottom start">
    <button type="button">Edit</button>
    <button type="button">Duplicate</button>
  </el-menu>
</el-dropdown>
```

All focusable children inside `el-menu` are treated as menu options.

## Popover

### Main role

`<el-popover>` is for anchored floating panels with arbitrary content.

### Main API

- Attributes:
  - `anchor`
  - `anchor-strategy`
- Event:
  - `toggle`
- Methods:
  - `togglePopover()`
  - `showPopover()`
  - `hidePopover()`
- Transition data attributes:
  - `data-closed`
  - `data-enter`
  - `data-leave`
  - `data-transition`

`<el-popover-group>` keeps related popovers open when focus moves between them.

### Basic example

```html
<el-popover-group>
  <button popovertarget="menu-a" type="button">Menu A</button>
  <el-popover id="menu-a" popover anchor="bottom start">
    Content A
  </el-popover>
</el-popover-group>
```

## Common mistakes

- Styling native `::backdrop` when a transitionable `el-dialog-backdrop` is the better fit.
- Forgetting that Dialog close prevention belongs on the `cancel` event.
- Using `el-menu` outside Dropdown terminology and assuming it behaves like `el-options`.
- Forgetting `popover` on Popover or Dropdown panel elements.
