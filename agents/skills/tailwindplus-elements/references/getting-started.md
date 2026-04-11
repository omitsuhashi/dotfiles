# Getting Started

## Library model

Tailwind Plus Elements is the JavaScript layer behind the interactive behavior in Tailwind Plus HTML snippets. It is framework-agnostic and targets modern browsers supported by Tailwind CSS v4.

Minimum browser versions from the source material:

- Chrome 111
- Safari 16.4
- Firefox 128

## Installation modes

### CDN

Use this when the project does not have a build pipeline:

```html
<script src="https://cdn.jsdelivr.net/npm/@tailwindplus/elements@1" type="module"></script>
```

### npm

Use this when the project already bundles JavaScript:

```bash
npm install @tailwindplus/elements
```

Then import it once from a root entry point:

```js
import '@tailwindplus/elements'
```

### React

For React or Next.js, install with npm and prefer the React wrappers:

```bash
npm install @tailwindplus/elements
```

```jsx
import { ElDisclosure } from '@tailwindplus/elements/react'
import { useId } from 'react'

export default function Example() {
  const id = useId()

  return (
    <>
      <button command="--toggle" commandfor={id}>
        Toggle
      </button>
      <ElDisclosure id={id} hidden>
        Content
      </ElDisclosure>
    </>
  )
}
```

### React rule of thumb

- Prefer React exports over raw custom elements.
- Keep the command and `commandfor` wiring the same as in the HTML examples.
- Reach for raw custom elements only when there is no React wrapper for the target component.

## Detecting readiness

If you need to attach custom DOM behavior, wait until Elements is ready:

```js
function enhance() {
  const autocomplete = document.getElementById('autocomplete')
  // add custom behavior here
}

if (customElements.get('el-autocomplete')) {
  enhance()
} else {
  window.addEventListener('elements:ready', enhance)
}
```

Use this pattern whenever your code needs to call methods on an element instance or inspect upgraded custom elements.

## Component groups

- Form and choice: Autocomplete, Select
- Overlay and disclosure: Dialog, Disclosure, Dropdown menu, Popover
- Utility and navigation: Command palette, Copy button, Tabs

Load the matching reference file instead of carrying the full catalog into context.
