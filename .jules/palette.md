## 2025-05-15 - [Accessibility of custom checkboxes]
**Learning:** Using `display: none` (Tailwind `hidden`) on an input removes it from the document's tab order, making it inaccessible to keyboard users. Using `sr-only` (screen-reader only) keeps the input in the tab order while hiding it visually.
**Action:** Always use `sr-only` instead of `hidden` for inputs that are visually replaced by custom UI. Add `focus-within` styles to the parent container to provide a visible focus indicator for these inputs.

## 2025-05-16 - [Standard Accessible Modal Pattern]
**Learning:** Modals require more than just a center-aligned `div`. They must have `role="dialog"`, `aria-modal="true"`, and descriptive labels via `aria-labelledby`/`aria-describedby`. Critical interactions include closing via Backdrop click, Escape key, and an explicit close button.
**Action:** Always implement the "holy trinity" of modal dismissal (Backdrop, Escape, Close Button) and ensure correct ARIA roles and labels are present for screen readers.
