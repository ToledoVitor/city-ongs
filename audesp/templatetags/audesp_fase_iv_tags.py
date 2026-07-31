"""Template helpers for the AUDESP Fase IV contract-detail tab. Kept as
simple_tags (rather than adding context in `ContractsDetailView`) so the
tab stays a self-contained, separately-includable partial that doesn't
touch the shared contract detail view.
"""

from django import template

register = template.Library()


@register.simple_tag
def audesp_fase_iv_submissions_for(contract):
    """AudespFaseIVSubmission history for `contract`, newest build first."""
    return contract.audesp_fase_iv_submissions.filter(deleted_at__isnull=True).order_by(
        "-built_at"
    )


@register.simple_tag
def budget_commitments_for(contract):
    """BudgetCommitment rows available to register an Empenho against."""
    return contract.budget_commitments.filter(deleted_at__isnull=True).order_by(
        "-issue_date"
    )
