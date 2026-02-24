# Palette's Journal 🎨

## 2025-05-21 - Accessible Password Toggle
**Learning:** Password visibility toggles are a critical micro-UX win that improves both accessibility (allowing users to verify input) and usability. When implementing them, it is essential to use `type="button"` to prevent accidental form submission and provide clear `aria-label` updates for screen readers. Using decorative icons like `Eye` and `EyeOff` should always be accompanied by `aria-hidden="true"` if they are inside a button with a descriptive label.
**Action:** Always include a password visibility toggle for any password input fields, ensuring full keyboard and screen reader support.

## 2025-05-22 - Testing Labels with Decorative Elements
**Learning:** Testing UI labels that contain decorative elements (like required asterisks in spans) using `getByLabelText` can fail if the match is too strict. Using case-insensitive regex (e.g., `/email/i`) is a more resilient approach that ignores the nested decorative content while still verifying the presence and association of the label.
**Action:** Use regex for `getByLabelText` in Vitest/RTL when labels contain formatting or decorative spans to ensure tests remain robust against minor UI polish changes.

## 2025-05-22 - Scan Progress Visualization
**Learning:** Providing a visual "Overall Progress" bar during long-running async processes (like security scans) significantly reduces user anxiety and improves the perceived speed of the application. Calculating this progress based on the completion of discrete sub-tasks (stages) provides a more accurate representation than a generic indeterminate spinner.
**Action:** Implement progress bars for any multi-stage processes, ensuring they are accessible via proper ARIA roles and attributes.
