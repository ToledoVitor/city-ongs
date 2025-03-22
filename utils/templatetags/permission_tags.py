from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter
@stringfilter
def can_edit(user):
    """Check if user can edit content (not a committee member)."""
    return not user.is_committee_member


@register.filter
@stringfilter
def can_create(user):
    """Check if user can create content (not a committee member)."""
    return not user.is_committee_member


@register.filter
@stringfilter
def can_delete(user):
    """Check if user can delete content (not a committee member)."""
    return not user.is_committee_member


@register.filter
@stringfilter
def can_change_status(user):
    """Check if user can change statuses (not a committee member)."""
    return not user.is_committee_member
