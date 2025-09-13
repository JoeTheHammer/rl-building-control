from typing import Any, Optional

from wrappers.reporting_wrapper import ReportingWrapper


def find_reporting_wrapper(env: Any) -> Optional[ReportingWrapper]:
    """
    Searches for a ReportingWrapper instance within a potentially nested env or
    a controller/adapter object.
    """
    # Case 1: The object itself is the wrapper
    if isinstance(env, ReportingWrapper):
        return env
    # Case 2: The object is our adapter which has a .reporting_env attribute
    if hasattr(env, "reporting_env") and isinstance(env.reporting_env, ReportingWrapper):
        return env.reporting_env
    # Case 3: Standard gym wrapper, search recursively
    if hasattr(env, "env"):
        return find_reporting_wrapper(env.env)
    return None
