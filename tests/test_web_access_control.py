from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_web_ui_defines_logged_out_shell_and_role_navigation() -> None:
    app_js = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
    index_html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")

    assert 'id="logged-out"' in index_html
    assert "ROLE_VIEWS" in app_js
    assert "function applyAuthState" in app_js
    assert "document.body.classList.toggle(\"is-authenticated\"" in app_js
    assert "implementer: [\"chat\", \"sessions\", \"tasks\"]" in app_js
    assert "admin: [\"chat\", \"sessions\", \"admin\", \"knowledge\", \"ops\", \"accounts\", \"config\", \"evaluation\", \"tasks\"]" in app_js


def test_account_management_is_a_dedicated_admin_view() -> None:
    app_js = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
    index_html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")

    assert 'data-view="accounts">账号管理' in index_html
    assert 'id="view-accounts"' in index_html
    assert 'id="account-username"' in index_html
    assert 'id="account-password"' in index_html
    assert 'id="account-role"' in index_html
    assert "if (name === \"accounts\") loadUsers();" in app_js
    assert 'data-view="accounts"' in app_js or '"accounts"' in app_js
