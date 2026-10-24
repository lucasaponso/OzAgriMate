from datetime import datetime, timezone


def utc_now() -> datetime:
    """Single time source so services (and tests) agree on 'now'."""
    return datetime.now(timezone.utc).replace(microsecond=0)
