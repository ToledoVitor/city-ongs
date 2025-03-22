from easy_tenants import tenant_context_disabled
from IPython import embed

with tenant_context_disabled():
    embed()
