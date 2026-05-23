import pytest

import get_stats


def _set_required_env(
    monkeypatch, *, student_ids="student-1", recipient_emails="parent@example.com"
):
    monkeypatch.setenv("IXL_USERNAME", "ixl-user")
    monkeypatch.setenv("IXL_PASSWORD", "ixl-password")
    monkeypatch.setenv("MATHACADEMY_USERNAME", "ma-user")
    monkeypatch.setenv("MATHACADEMY_PASSWORD", "ma-password")
    monkeypatch.setenv("MATHACADEMY_STUDENT_IDS", student_ids)
    monkeypatch.setenv("GMAIL_USER", "sender@example.com")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "gmail-password")
    monkeypatch.setenv("RECIPIENT_EMAILS", recipient_emails)


def _fail_if_browser_launches(monkeypatch):
    def fail_setup_driver():
        pytest.fail("setup_driver should not be called before env validation completes")

    monkeypatch.setattr(get_stats, "setup_driver", fail_setup_driver)


@pytest.mark.parametrize(
    "env_name",
    [
        "IXL_USERNAME",
        "IXL_PASSWORD",
        "MATHACADEMY_USERNAME",
        "MATHACADEMY_PASSWORD",
        "MATHACADEMY_STUDENT_IDS",
        "GMAIL_USER",
        "GMAIL_APP_PASSWORD",
        "RECIPIENT_EMAILS",
    ],
)
def test_missing_required_env_var_fails_before_browser_launch(monkeypatch, env_name):
    _set_required_env(monkeypatch)
    monkeypatch.delenv(env_name)
    _fail_if_browser_launches(monkeypatch)

    with pytest.raises(ValueError, match=f"{env_name} not set in environment variables"):
        get_stats.main()


def test_blank_only_math_academy_student_ids_fail_before_browser_launch(monkeypatch):
    _set_required_env(monkeypatch, student_ids=" , ")
    _fail_if_browser_launches(monkeypatch)

    with pytest.raises(ValueError, match="MATHACADEMY_STUDENT_IDS must contain at least one ID"):
        get_stats.main()


def test_blank_only_recipient_email_list_fails_before_browser_launch(monkeypatch):
    _set_required_env(monkeypatch, recipient_emails=" , ")
    _fail_if_browser_launches(monkeypatch)

    with pytest.raises(ValueError, match="RECIPIENT_EMAILS must contain at least one address"):
        get_stats.main()
