"""
Utilities for cache invalidation.
"""

from functools import wraps

from django.core.cache import cache
from django.db import models

from utils.cache_keys import (
    get_accountability_detail_key,
    get_accountability_list_key,
    get_accountability_stats_key,
    get_contract_detail_key,
    get_contract_stats_key,
)


class CacheInvalidationMixin(models.Model):
    """
    Mixin to automatically invalidate cache on model save.
    """

    class Meta:
        abstract = True

    def invalidate_cache(self):
        """
        Override this method to implement cache invalidation logic.
        """
        pass

    def save(self, *args, **kwargs):
        """
        Override save method to invalidate cache.
        """
        super().save(*args, **kwargs)
        self.invalidate_cache()


def invalidate_contract_cache(contract_id):
    """
    Invalidate all cache related to a contract.
    """
    cache.delete(get_contract_stats_key(contract_id))
    cache.delete(get_contract_detail_key(contract_id))


def invalidate_accountability_cache(accountability_id, organization_id=None):
    """
    Invalidate all cache related to an accountability.
    """
    cache.delete(get_accountability_stats_key(accountability_id))
    cache.delete(get_accountability_detail_key(accountability_id))
    if organization_id:
        cache.delete(get_accountability_list_key(organization_id))


def invalidate_cache_on_update(view_func):
    """
    Decorator to invalidate cache after a successful view update.
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        response = view_func(request, *args, **kwargs)

        # Get relevant IDs from kwargs
        contract_id = kwargs.get("pk")
        accountability_id = kwargs.get("accountability_id")
        organization_id = getattr(request.user, "organization_id", None)

        # Invalidate relevant caches
        if contract_id:
            invalidate_contract_cache(contract_id)

        if accountability_id:
            invalidate_accountability_cache(accountability_id, organization_id)

        return response

    return wrapper
