"""
Cache keys for the system.
"""

# Cache times (in seconds)
CACHE_TIMES = {
    "STATS": 300,  # 5 minutes
    "DETAIL": 600,  # 10 minutes
    "LIST": 60,  # 1 minute
}


def get_contract_stats_key(contract_id: str) -> str:
    """Key for contract statistics."""
    return f"contract_stats_{contract_id}"


def get_accountability_stats_key(accountability_id: str) -> str:
    """Key for accountability statistics."""
    return f"accountability_stats_{accountability_id}"


def get_contract_detail_key(contract_id: str) -> str:
    """Key for contract details."""
    return f"contract_detail_{contract_id}"


def get_accountability_detail_key(accountability_id: str) -> str:
    """Key for accountability details."""
    return f"accountability_detail_{accountability_id}"


def get_accountability_list_key(organization_id: str, query: str = "") -> str:
    """Key for list of accountabilities."""
    if query:
        return f"accountability_list_{organization_id}_{query}"
    return f"accountability_list_{organization_id}"
