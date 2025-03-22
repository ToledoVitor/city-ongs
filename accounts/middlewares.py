from easy_tenants import tenant_context, tenant_context_disabled


class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            with tenant_context_disabled():
                return self.get_response(request)

        if request.path.startswith("/admin") and request.user.is_superuser:
            with tenant_context_disabled():
                return self.get_response(request)

        with tenant_context(request.user.organization):
            return self.get_response(request)
