# Palette's Journal 🎨

## 2025-05-21 - Accessible Password Toggle
**Learning:** Password visibility toggles are a critical micro-UX win that improves both accessibility (allowing users to verify input) and usability. When implementing them, it is essential to use `type="button"` to prevent accidental form submission and provide clear `aria-label` updates for screen readers. Using decorative icons like `Eye` and `EyeOff` should always be accompanied by `aria-hidden="true"` if they are inside a button with a descriptive label.
**Action:** Always include a password visibility toggle for any password input fields, ensuring full keyboard and screen reader support.

## 2025-05-22 - Feedback for Destructive Actions
**Learning:** Destructive asynchronous actions, like deleting a project, must provide immediate and clear feedback. Relying solely on the UI element disappearing is insufficient as it doesn't confirm success or explain failure. Toast notifications provide a non-intrusive way to confirm these outcomes. Additionally, links in dense lists (like a dashboard) should have project-specific `aria-label` and `title` attributes to ensure they are disambiguated for screen readers and provide context on hover.
**Action:** Implement success and error toast notifications for all destructive operations and ensure list-item links have unique, descriptive labels.
