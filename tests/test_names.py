from app.names import is_blocked, DAY

NOW = 1_800_000_000


def test_name_used_3_days_ago_is_blocked():
    assert is_blocked("Priya", [{"name": "Priya Sharma", "at": NOW - 3 * DAY}], NOW)


def test_name_used_5_days_ago_is_allowed():
    assert not is_blocked("Priya", [{"name": "Priya", "at": NOW - 5 * DAY}], NOW)
