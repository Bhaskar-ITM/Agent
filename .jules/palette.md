## 2025-05-15 - Playwright Strict Mode & Label Targeting
**Learning:** When using Playwright's `get_by_label`, it may resolve to multiple elements if interactive elements (like a password toggle button) are nested near or associated with the label. Using specific ID selectors or `page.locator("label[for='...']")` is more robust.
**Action:** Use specific ID selectors for form inputs in Playwright scripts when interactive decorators are present.

## 2025-05-15 - Visual Consistency for Required Fields
**Learning:** Consistently using a red asterisk for required fields across all forms (Login, Create Project) improves user scan-ability and matches existing design patterns in the repo.
**Action:** Always check for `required` attribute and add `<span className="text-red-500 ml-1" aria-hidden="true">*</span>` to the corresponding label.
