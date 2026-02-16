## 2025-05-15 - [Accessibility of custom checkboxes]
**Learning:** Using `display: none` (Tailwind `hidden`) on an input removes it from the document's tab order, making it inaccessible to keyboard users. Using `sr-only` (screen-reader only) keeps the input in the tab order while hiding it visually.
**Action:** Always use `sr-only` instead of `hidden` for inputs that are visually replaced by custom UI. Add `focus-within` styles to the parent container to provide a visible focus indicator for these inputs.
