# Document Workspace Refinement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add server-filtered infinite lists and clearer, brand-consistent document-to-expense assignment UI.

**Architecture:** Keep Django server-rendered workspace as shell and add two accountability-scoped JSON endpoints. Browser owns independent document and expense feed state, uses debounced requests plus `IntersectionObserver`, and keeps assignment optimistic while server remains authoritative after refresh.

**Tech Stack:** Python 3.12, Django, Django TestCase, Django templates, vanilla JavaScript, existing SITTS UI tokens.

## Global Constraints

- Preserve existing accountability records, permissions, upload validation, assignment endpoint, and transaction reconciliation.
- Document and expense endpoints default to 20 items and cap `page_size` at 50.
- Document workspace defaults to `Sem despesa`.
- Cards use 16 px radius; actions use pill geometry; compact inputs use 8–12 px radius.
- Desktop must fit 1366×768 without body scrolling; mobile must avoid horizontal scrolling.
- Do not add dependencies or migrations.
- Do not stage `AGENTS.md`, `docs/agents/`, temporary files, or unrelated user changes.

---

### Task 1: Paginated document feed

**Files:**
- Modify: `accountability/tests.py`
- Modify: `accountability/views.py`
- Modify: `accountability/urls.py`

**Interfaces:**
- Consumes: `ExpenseFile`, `Accountability`, authenticated request, `q`, `scope`, `page`, and `page_size`.
- Produces: `expense_document_list_view(request, pk)` returning `{results, has_more, page, total, unassigned_total}`.
- Produces: `_workspace_page(request, queryset) -> tuple[list, bool, int]` with default size 20 and maximum 50.

- [ ] **Step 1: Write failing endpoint tests**

Add tests that create 21 unassigned and one assigned document, request `expense-document-list`, and assert:

```python
self.assertEqual(response.status_code, 200)
self.assertEqual(len(response.json()["results"]), 20)
self.assertTrue(response.json()["has_more"])
self.assertTrue(all(item["expense_id"] is None for item in response.json()["results"]))
```

Add separate assertions for `scope=all`, `q=target`, page 2, `page_size=999` capped at 50, and exclusion of documents belonging to another accountability.

- [ ] **Step 2: Run document endpoint tests red**

Run:

```bash
uv run python manage.py test accountability.tests.ExpenseDocumentWorkspaceTests.test_document_list_defaults_to_unassigned_and_paginates accountability.tests.ExpenseDocumentWorkspaceTests.test_document_list_filters_and_stays_scoped
```

Expected: reverse lookup or endpoint assertions fail because route does not exist.

- [ ] **Step 3: Add pagination helper and document endpoint**

Implement request parsing without a count query for pages:

```python
EXPENSE_DOCUMENT_PAGE_SIZE = 20
EXPENSE_DOCUMENT_MAX_PAGE_SIZE = 50


def _workspace_page(request, queryset):
    try:
        page = max(1, int(request.GET.get("page") or 1))
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = int(request.GET.get("page_size") or EXPENSE_DOCUMENT_PAGE_SIZE)
    except (TypeError, ValueError):
        page_size = EXPENSE_DOCUMENT_PAGE_SIZE
    page_size = max(1, min(page_size, EXPENSE_DOCUMENT_MAX_PAGE_SIZE))
    offset = (page - 1) * page_size
    rows = list(queryset[offset : offset + page_size + 1])
    return rows[:page_size], len(rows) > page_size, page
```

Build endpoint queryset from active documents belonging to requested accountability. Default `scope` to `unassigned`; accept only `all` as alternate. Apply `name__icontains` for `q`, select expense, and order by `-created_at`, then `pk`. Serialize ID, name, URL, image flag, expense ID, and expense identification. Query total and unassigned summary counts outside page slice.

Register:

```python
path(
    "detail/<uuid:pk>/documents/list/",
    expense_document_list_view,
    name="expense-document-list",
)
```

- [ ] **Step 4: Run document endpoint tests green**

Run focused class:

```bash
uv run python manage.py test accountability.tests.ExpenseDocumentWorkspaceTests
```

Expected: all document workspace tests pass.

### Task 2: Paginated expense feed

**Files:**
- Modify: `accountability/tests.py`
- Modify: `accountability/views.py`
- Modify: `accountability/urls.py`

**Interfaces:**
- Consumes: `Expense`, authenticated request, `q`, `without_documents`, `page`, and `page_size`.
- Produces: `expense_document_expense_list_view(request, pk)` returning `{results, has_more, page}`.
- Reuses: `_workspace_page(request, queryset)` from Task 1.

- [ ] **Step 1: Write failing expense endpoint tests**

Create one expense with a document and one without. Assert `without_documents=true` returns only missing-document expense. Assert `q` matches identification and favored name. Create enough scoped rows to assert 20-item first page, `has_more`, page 2, and exclusion of another accountability.

Expected serialized item shape:

```python
{
    "id": str(expense.id),
    "identification": expense.identification,
    "favored_name": expense.favored.name,
    "nature_label": expense.nature_label,
    "document_type_label": expense.document_type_label,
    "due_date": "14/08/2026",
    "value": "32000.00",
    "document_count": 0,
}
```

- [ ] **Step 2: Run expense endpoint tests red**

Run:

```bash
uv run python manage.py test accountability.tests.ExpenseDocumentWorkspaceTests.test_expense_list_filters_missing_documents accountability.tests.ExpenseDocumentWorkspaceTests.test_expense_list_searches_and_paginates
```

Expected: reverse lookup or endpoint assertions fail because route does not exist.

- [ ] **Step 3: Add expense endpoint**

Filter active expenses by accountability, annotate active `document_count`, and search with:

```python
Q(identification__icontains=query) | Q(favored__name__icontains=query)
```

When `without_documents` equals `true`, filter `document_count=0`. Order by `document_count`, `-value`, `identification`, and `pk`. Serialize human-facing values listed in Step 1. Register route named `expense-document-expense-list` at `detail/<uuid:pk>/documents/expenses/`.

- [ ] **Step 4: Run expense endpoint tests green**

Run:

```bash
uv run python manage.py test accountability.tests.ExpenseDocumentWorkspaceTests
```

Expected: all workspace endpoint tests pass.

### Task 3: API-backed workspace UI

**Files:**
- Modify: `accountability/tests.py`
- Modify: `accountability/views.py`
- Modify: `templates/accountability/expenses/document-workspace.html`

**Interfaces:**
- Consumes: document-list URL, expense-list URL, upload URL, assignment URL, API response shapes from Tasks 1–2.
- Produces: responsive workspace with independent `documentFeed` and `expenseFeed` browser states.
- Produces: `loadDocuments({reset})`, `loadExpenses({reset})`, `assignDocuments(ids, expenseId, expenseName)`, and DOM card factories.

- [ ] **Step 1: Write failing shell-render test**

Assert workspace response contains both API URLs, `Sem despesa` before `Todos`, active unassigned filter, hide-expenses toggle, document and expense sentinels, and no document-name anchor around card body.

- [ ] **Step 2: Run shell-render test red**

Run:

```bash
uv run python manage.py test accountability.tests.ExpenseDocumentWorkspaceTests.test_workspace_renders_api_backed_controls
```

Expected: missing data attributes and controls fail assertions.

- [ ] **Step 3: Reduce workspace view to shell context**

Remove eager document and expense list materialization from `expense_document_workspace_view`. Render accountability plus endpoint URLs through named Django routes in template data attributes.

- [ ] **Step 4: Rebuild panel markup and visual hierarchy**

Use empty list containers populated by JavaScript. Keep upload zone. Add:

- `Sem despesa` active chip before `Todos`.
- Rounded search fields.
- Document loading, empty, error, and sentinel nodes.
- `Ocultar com documentos` pill checkbox.
- One-column expense list plus loading, empty, error, and sentinel nodes.
- Separate unassign target.
- Compact selection bar with count, assignment instruction, clear action, and mobile jump-to-expenses action.

Reuse repository eye path from `templates/accountability/accountability/expenses-table.html` inside circular icon action; do not introduce icon dependency.

- [ ] **Step 5: Implement independent feed state**

Each feed stores:

```javascript
{
  page: 1,
  hasMore: true,
  loading: false,
  controller: null,
  query: '',
}
```

Build `URLSearchParams`, abort prior reset requests, fetch 20 results, append or replace cards, and update contained states. Debounce search by 250 ms. Observe separate sentinels with list containers as roots and load next pages only when `hasMore && !loading`.

- [ ] **Step 6: Implement selection, eye action, and assignment refresh**

Keep `selectedDocumentIds` as `Set`. Card click and keyboard toggle selection. Checkbox mirrors Set. Eye anchor stops propagation and opens `target="_blank" rel="noopener"`. Drag start includes all selected IDs. Expense row drop or click calls existing assignment endpoint.

On assignment success, clear assigned IDs and reset both feeds. On failure, preserve selection and show alert. On upload success, reset document feed rather than inserting client-only cards.

- [ ] **Step 7: Implement expense status and context**

Render each expense as one row with identification, favored party, value, due date, nature/document-type neutral pills, and semantic document status:

- `document_count === 0`: `ui-status ui-status--warning`, label `Sem documento`.
- `document_count > 0`: `ui-status ui-status--success`, singular/plural document count.

Use warning/success border and soft background only as semantic signal. Keep card radius at `var(--rounded-xl)`.

- [ ] **Step 8: Make layouts responsive**

Keep desktop panels within viewport height and internally scrollable. At ≤1100 px maintain single expense column. At ≤760 px stack panels, preserve 44 px touch targets, show mobile jump action, hide decorative drag handle, and prevent horizontal overflow.

- [ ] **Step 9: Run workspace tests green**

Run:

```bash
uv run python manage.py test accountability.tests.ExpenseDocumentWorkspaceTests
```

Expected: endpoint and shell tests pass.

### Task 4: Verification, review, delivery, and durable note

**Files:**
- Modify only if review finds defects: files from Tasks 1–3.
- Create outside repository: Obsidian session note selected by `tldr` skill.

**Interfaces:**
- Consumes: completed workspace and approved design note.
- Produces: verified PR update and Obsidian record linking design, implementation, tests, and PR.

- [ ] **Step 1: Run static and migration checks**

Run:

```bash
uv run ruff check accountability/views.py accountability/tests.py
uv run python manage.py check
uv run python manage.py makemigrations --check
git diff --check
```

Expected: all commands exit 0 and no migration is generated.

- [ ] **Step 2: Run focused and full tests**

Run:

```bash
uv run python manage.py test accountability.tests.ExpenseDocumentWorkspaceTests
uv run python manage.py test
```

Expected: focused tests pass. Full suite passes or only pre-existing, reproduced failures are reported.

- [ ] **Step 3: Seed and verify browser flow**

Run existing seed command and local server. In in-app browser, verify:

- 1366×768: no body scroll, two contained feeds, one expense per row.
- Tablet: readable one-column expense rows.
- Mobile: stacked panels, no horizontal scroll, tap assignment works.
- Default unassigned filter, both API searches, hide toggle, infinite loading, selection-only card click, eye new-tab action, drag assignment, click assignment, unassign, upload refresh, and error state.

- [ ] **Step 4: Review diff against repository standards and design spec**

Use `code-review` skill against merge base and fix P0–P2 findings. Confirm no unrelated files or temporary artifacts are staged.

- [ ] **Step 5: Commit and push implementation**

Stage exact implementation files only and commit:

```bash
git add accountability/views.py accountability/urls.py accountability/tests.py templates/accountability/expenses/document-workspace.html docs/superpowers/plans/2026-08-14-document-workspace-refinement.md
git commit -m "feat(accountability): refine document workspace"
git push
```

- [ ] **Step 6: Save Obsidian note**

Use `tldr` skill after implementation is pushed. Include design-note path, implementation summary, endpoint contract, test results, commit hash, and PR #79 URL. Do not add vault artifacts to repository.
