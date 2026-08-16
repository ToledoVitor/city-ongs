# Document workspace refinement

## Goal

Make bulk document reconciliation faster and clearer when an accountability has dozens of documents and expenses. Preserve existing accountability records, permissions, assignment endpoint, and SITTS visual language.

## User flow

1. User opens an accountability and selects **Organizar documentos**.
2. Workspace opens with **Sem despesa** active, showing unassigned documents first.
3. User uploads up to 50 PDF, JPG, or PNG files, searches documents, and loads more results by scrolling.
4. Clicking a document card selects it. Only its eye button opens the file in a new tab.
5. User searches or scrolls expenses, optionally hiding expenses that already have documents.
6. User drags selected documents onto an expense or clicks an expense row to assign them.
7. Successful assignments update document and expense states immediately. Failed assignments restore prior state and show an error.

## Interface

### Documents panel

- Order filter chips as **Sem despesa**, then **Todos**.
- Default to **Sem despesa**.
- Use rounded cards and controls matching `DESIGN.md`: 16 px cards, pill actions, and compact 8–12 px input radii.
- Card click toggles selection without opening the document.
- Add a circular eye action with an accessible label. It opens the file in a new tab with `noopener`.
- Keep selected document IDs independently from rendered pages so selection survives infinite-scroll loads.
- Search uses a 250 ms debounce and resets pagination.

### Expenses panel

- Render one expense per row.
- Show identification, favored party, nature or document type, due date, and formatted value.
- Show a warning status pill for **Sem documento** and a success status pill with document count otherwise.
- Add a pill toggle named **Ocultar com documentos**. Filtering runs on the server.
- Keep the unassign target visually separate from expense results.
- Expense row click assigns current selection; drag-and-drop remains available on pointer devices.

### Responsive behavior

- Desktop keeps two independently scrolling panels and fits 1366×768 without body scrolling.
- Tablet reduces panel proportions while preserving one expense per row.
- Mobile stacks panels, keeps tap-based selection and assignment available, and avoids horizontal scrolling.

## API design

Add two authenticated, accountability-scoped JSON endpoints.

### Document list

Parameters:

- `q`: case-insensitive filename search.
- `scope`: `unassigned` or `all`; defaults to `unassigned`.
- `page`: positive integer; defaults to 1.
- `page_size`: defaults to 20 and is capped at 50.

Response includes serialized documents, `page`, `has_more`, and current total and unassigned counts. Ordering is stable and includes primary key as final tie-breaker.

### Expense list

Parameters:

- `q`: case-insensitive search across identification and favored-party name.
- `without_documents`: boolean; defaults to false.
- `page`: positive integer; defaults to 1.
- `page_size`: defaults to 20 and is capped at 50.

Response includes serialized expenses, `page`, and `has_more`. Each item includes display labels and document count. Ordering is stable and prioritizes expenses without documents, then value and identification.

Both endpoints apply same permission and execution-state checks as workspace. Pagination fetches one extra row instead of issuing a total-count query.

## Client data flow

- Workspace renders shell only; each panel requests its first API page.
- Each panel owns query, filters, page number, loading state, `has_more`, and request cancellation.
- `IntersectionObserver` loads next page near list end.
- New searches and filters cancel stale requests, clear current results, and restart at page 1.
- Upload success refreshes document page 1 and summary counts.
- Assignment uses optimistic state. On success, affected lists restart from page 1 so server filters and counts remain authoritative. On failure, prior state returns.
- Empty, loading, end-of-results, and API-error states remain contained inside their panel.

## Error handling

- Invalid pagination or filter input falls back to safe defaults.
- Missing or unauthorized accountability returns existing redirect/403 behavior consistently.
- Network errors keep loaded rows visible and offer retry through continued scrolling or a retry action.
- Eye action stops card-selection propagation.

## Test seams

Tests exercise public Django endpoints and browser-visible behavior:

- Document endpoint defaults to unassigned documents, filters by query, paginates, and stays accountability-scoped.
- Expense endpoint filters by query and missing-document state, paginates, and stays accountability-scoped.
- Page-size cap and stable `has_more` contract work for both endpoints.
- Existing bulk upload and assignment endpoints remain valid.
- Browser checks cover selection versus preview, filtering, infinite scroll, assignment, hide toggle, and responsive layouts at 1366×768, tablet, and mobile sizes.

## Out of scope

- Changing transaction reconciliation.
- Replacing storage or upload validation.
- Adding document classification or OCR.
- Changing accountability lifecycle or permissions.
