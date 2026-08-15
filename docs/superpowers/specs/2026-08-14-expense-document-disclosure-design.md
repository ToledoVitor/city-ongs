# Expense document disclosure and unlinking

## Goal

Make mistaken document assignments easy to inspect and reverse without leaving bulk document workspace. Preserve fast drag-and-drop assignment while removing ambiguous expense-card clicks.

## Root cause

Current unlink target depends on `selectedDocumentIds`. After assignment, workspace clears selection and default `Sem despesa` feed hides moved document. Expense rows expose only aggregate count, so user cannot discover or select attached document again. Existing assignment endpoint already accepts `expense_id: null`; failure sits in interaction model, not write API.

## Approved interaction

Expense card becomes expandable disclosure.

- Clicking expense summary always expands or collapses attached documents.
- Only one expense stays expanded at once. Closing and reopening reuses successfully fetched data.
- When documents are selected in left panel, expense card shows explicit pill action `Vincular N`.
- Clicking `Vincular N` assigns selected documents. Clicking summary never assigns.
- Dragging selected documents onto expense card still assigns them.
- Hover never gates functionality; all actions work with pointer, keyboard, and touch.

This replaces ambiguous contextual click behavior and reduces accidental moves.

## Attached document disclosure

First expansion fetches documents on demand. Disclosure shows dense rows with:

- filename and file-type label;
- circular eye action opening file in new tab with `noopener`;
- compact `Remover vínculo` action with accessible document-specific label.

Unlink is immediate because operation is reversible and does not delete file. Successful unlink returns document to `Sem despesa`, refreshes summary counts and document feed, and refreshes expanded expense disclosure. Failure keeps row visible and shows inline error plus workspace alert.

Empty disclosure says `Nenhum documento vinculado`. Loading, retry, pagination, and end states remain inside expanded card.

## Bulk unlink target

Keep top-level `Remover vínculo` target for bulk workflows, but make state explicit:

- disabled when selection contains no linked documents;
- helper text explains `Selecione documentos vinculados em Todos ou remova abaixo`;
- enabled label includes linked selection count;
- action sends only selected linked document IDs with `expense_id: null`;
- unassigned selected documents remain selected.

Client retains document assignment metadata for selected IDs so bulk target stays correct across loaded pages.

## API design

Add authenticated, accountability-scoped endpoint:

```text
GET /accountability/detail/<accountability_id>/documents/expenses/<expense_id>/documents/
```

Named route: `accountability:expense-document-expense-documents`.

Parameters:

- `page`: positive integer, default 1;
- `page_size`: default 20, capped at 50.

Response:

```json
{
  "results": [
    {
      "id": "uuid",
      "name": "nota.pdf",
      "url": "/media/uploads/expenses/nota.pdf",
      "is_image": false
    }
  ],
  "page": 1,
  "has_more": false,
  "total": 1
}
```

Endpoint verifies update permission, accountability execution state, and expense ownership. Query includes only active `ExpenseFile` rows belonging to both accountability and expense, ordered by `-created_at`, then primary key. It reuses workspace page helper.

Expense-list response adds `documents_url` generated through Django `reverse`; client does not construct routes manually.

## Client state and data flow

Maintain disclosure state by expense ID:

```javascript
{
  items: [],
  page: 0,
  hasMore: true,
  loading: false,
  loaded: false,
  controller: null,
  error: null
}
```

Flow:

1. Summary click closes previously expanded expense, opens chosen card, and fetches page 1 only when cache is cold.
2. `Carregar mais` fetches next 20 documents without blocking other expense cards.
3. Successful assignment invalidates source and destination disclosure caches, refreshes both top-level feeds, clears assigned selection, and leaves all disclosures collapsed.
4. Successful per-document unlink invalidates selected expense cache, refreshes document feed and expense feed, then reopens same expense and fetches fresh page 1.
5. Failed or aborted requests never replace successful cached items.

Document metadata map stores ID, expense ID, name, and URL for each loaded document. Selection refresh derives linked selection count from this map.

## Components

Expense card stops being one nested button. Structure uses:

- outer article/drop target;
- summary disclosure button with `aria-expanded` and `aria-controls`;
- sibling `Vincular N` button;
- controlled disclosure region;
- attached-document rows with sibling eye and unlink actions.

This avoids nested interactive elements and keeps keyboard semantics valid.

## Responsive behavior

- Desktop: disclosure opens within expense list; attached rows remain compact and do not widen panel.
- Tablet: filename truncates before actions; assign pill stays visible.
- Mobile: attached row wraps metadata, but eye and unlink retain at least 44 px touch targets. No hover dependency or horizontal scroll.
- Expense panel keeps own scroll container at desktop sizes.

## Error handling

- Expense-document fetch shows inline retry without collapsing card.
- Unlink failure restores interactive state and preserves row.
- Assignment button disables during request to prevent duplicate writes.
- Stale or aborted disclosure response is ignored through request controller and cache version.
- Missing/unauthorized expense returns existing JSON 403/404 behavior.

## Test seams

Django tests cover:

- expense-document endpoint returns only active documents for requested expense/accountability;
- endpoint pagination defaults to 20 and caps at 50;
- expense-list response includes correct `documents_url`;
- assignment endpoint with `expense_id: null` unlinks linked documents;
- cross-accountability expense/document access remains rejected.

Browser checks cover:

- summary expands without assigning current selection;
- first expansion fetches; repeated expansion uses cache;
- explicit `Vincular N` and drag assignment still work;
- per-document unlink returns item to `Sem despesa` and updates counts;
- bulk unlink target disabled/enabled states;
- eye action opens new tab without toggling disclosure;
- loading, empty, retry, pagination, desktop, tablet, and mobile states.

## Out of scope

- Deleting files.
- Document preview modal.
- OCR or document classification.
- Transaction reconciliation changes.
- Multi-expense comparison with several disclosures open simultaneously.
