"""Smoke tests to verify modules are importable."""


def test_import_check_credentials():
    import check_credentials

    assert hasattr(check_credentials, "check_credentials")


def test_import_ixl_skills_parse():
    import ixl_skills_parse

    assert hasattr(ixl_skills_parse, "get_codes_from_ixl")


def test_import_get_stats():
    import get_stats

    assert hasattr(get_stats, "setup_driver")
    assert hasattr(get_stats, "send_email")
