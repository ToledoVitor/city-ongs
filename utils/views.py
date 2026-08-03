import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, QuerySet
from django.http import JsonResponse
from django.views import View

logger = logging.getLogger(__name__)


class ComboboxSearchView(LoginRequiredMixin, View):
    """Paginated JSON option source for the `ui/combobox.html` component.

    Subclasses declare the queryset and which fields are searchable; the view
    handles the `?q=`, `?page=` and `?page_size=` contract the client runtime
    expects:

        {"results": [{"id": ..., "text": ..., "subtext": ...}],
         "has_more": bool, "page": int}

    Access control lives entirely in `get_queryset()` — the endpoint is only as
    scoped as the queryset it returns, so subclasses must apply the same
    filtering the corresponding form field uses.
    """

    search_fields: tuple[str, ...] = ()
    numeric_search_fields: tuple[str, ...] = ()
    ordering: tuple[str, ...] = ()
    page_size = 10
    max_page_size = 50
    # Accent-insensitive matching, so "saude" finds "Saúde" and "convenio"
    # finds "Convênio". Set False for numeric-only fields, where unaccent is
    # wasted work and blocks any index on the column.
    unaccent_search = True

    def get_queryset(self) -> QuerySet:
        raise NotImplementedError

    def serialize(self, obj) -> dict:
        """Map a model instance to an option dict."""
        return {"id": str(obj.pk), "text": str(obj)}

    def get_ordering(self) -> tuple[str, ...]:
        """Ordering must be total, or offset pages repeat and skip rows."""
        ordering = tuple(self.ordering)
        return ordering + ("pk",) if "pk" not in ordering else ordering

    def _resolve_page_size(self, raw: str | None) -> int:
        try:
            requested = int(raw) if raw else self.page_size
        except (TypeError, ValueError):
            requested = self.page_size
        return max(1, min(requested, self.max_page_size))

    def filter_queryset(self, queryset: QuerySet, query: str) -> QuerySet:
        if not query or not (self.search_fields or self.numeric_search_fields):
            return queryset

        condition = Q()
        lookup = "unaccent__icontains" if self.unaccent_search else "icontains"
        for field in self.search_fields:
            condition |= Q(**{f"{field}__{lookup}": query})
        # unaccent() is a text function — casting a numeric column through it
        # errors out, so codes and ids match with a plain icontains.
        for field in self.numeric_search_fields:
            condition |= Q(**{f"{field}__icontains": query})
        return queryset.filter(condition)

    def get(self, request, *args, **kwargs):
        query = (request.GET.get("q") or "").strip()
        page_size = self._resolve_page_size(request.GET.get("page_size"))
        try:
            page = max(1, int(request.GET.get("page") or 1))
        except (TypeError, ValueError):
            page = 1

        queryset = self.filter_queryset(self.get_queryset(), query)
        queryset = queryset.order_by(*self.get_ordering())

        offset = (page - 1) * page_size
        # One extra row tells us whether another page exists without a COUNT.
        rows = list(queryset[offset : offset + page_size + 1])

        return JsonResponse(
            {
                "results": [self.serialize(obj) for obj in rows[:page_size]],
                "has_more": len(rows) > page_size,
                "page": page,
            }
        )
