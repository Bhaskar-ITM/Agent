## 2025-05-15 - [Accessibility of custom checkboxes]
**Learning:** Using `display: none` (Tailwind `hidden`) on an input removes it from the document's tab order, making it inaccessible to keyboard users. Using `sr-only` (screen-reader only) keeps the input in the tab order while hiding it visually.
**Action:** Always use `sr-only` instead of `hidden` for inputs that are visually replaced by custom UI. Add `focus-within` styles to the parent container to provide a visible focus indicator for these inputs.

## 2025-05-16 - [Standard Accessible Modal Pattern]
**Learning:** Modals require more than just a center-aligned `div`. They must have `role="dialog"`, `aria-modal="true"`, and descriptive labels via `aria-labelledby`/`aria-describedby`. Critical interactions include closing via Backdrop click, Escape key, and an explicit close button.
**Action:** Always implement the "holy trinity" of modal dismissal (Backdrop, Escape, Close Button) and ensure correct ARIA roles and labels are present for screen readers.

## 2025-05-17 - [Interactive Feedback and Form Accessibility]
**Learning:** Micro-interactions like "Copy to Clipboard" need immediate visual feedback (e.g., icon swap) to confirm success to the user. Additionally, standardizing form accessibility by using explicit `id` and `htmlFor` mappings is critical for screen reader compatibility and better tap targets on mobile.
**Action:** Use a temporary state (e.g., `copiedField`) to toggle between `Copy` and `Check` icons for 2 seconds after a successful copy. Always ensure every form input has a unique `id` linked to its label's `htmlFor`.
