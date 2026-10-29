"""Names must not repeat within 4 days (first name or full name)."""
import time

from .config import NAME_BLOCK_DAYS

DAY = 24 * 60 * 60


def normalize(n: str) -> str:
    return " ".join(n.strip().lower().split())


def is_blocked(name: str, used: list, now: float | None = None) -> bool:
    now = time.time() if now is None else now
    n = normalize(name)
    first = n.split(" ")[0] if n else ""
    for u in used:
        if now - u["at"] >= NAME_BLOCK_DAYS * DAY:
            continue
        un = normalize(u["name"])
        if un == n or un.split(" ")[0] == first:
            return True
    return False


def recent(used: list, now: float | None = None) -> list[str]:
    now = time.time() if now is None else now
    return [u["name"] for u in used if now - u["at"] < NAME_BLOCK_DAYS * DAY]


def prune(used: list, now: float | None = None) -> list:
    now = time.time() if now is None else now
    return [u for u in used if now - u["at"] < NAME_BLOCK_DAYS * DAY]
