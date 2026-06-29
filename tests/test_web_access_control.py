from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_web_ui_defines_logged_out_shell_and_role_navigation() -> None:
    app_js = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
    index_html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")

    assert 'id="logged-out"' in index_html
    assert "ROLE_VIEWS" in app_js
    assert "function applyAuthState" in app_js
    assert 'document.body.classList.toggle("is-authenticated"' in app_js
    assert 'implementer: ["workspace", "sessions", "tasks"]' in app_js
    assert 'admin: ["dashboard", "accounts", "sessions", "admin", "knowledge", "ops", "config", "evaluation", "tasks"]' in app_js


def test_account_management_is_a_dedicated_admin_view() -> None:
    app_js = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
    index_html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")

    assert 'data-view="accounts"' in index_html
    assert 'id="view-accounts"' in index_html
    assert 'id="account-username"' in index_html
    assert 'id="account-password"' in index_html
    assert 'id="account-role"' in index_html
    assert 'if (name === "accounts") loadUsers();' in app_js


def test_web_ui_has_role_specific_workspaces_and_project_switching() -> None:
    app_js = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
    index_html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")

    assert 'data-view="workspace"' in index_html
    assert 'id="view-workspace"' in index_html
    assert 'id="implementer-shell"' in index_html
    assert 'id="management-shell"' in index_html
    assert 'id="project-switcher"' in index_html
    assert 'id="current-project-code"' in index_html
    assert 'id="switch-project"' in index_html
    assert 'function switchProject' in app_js
    assert 'function renderRoleShell' in app_js
    assert 'localStorage.setItem("ops-agent-current-project"' in app_js


def test_web_ui_uses_compact_full_height_workspace_and_admin_layout() -> None:
    styles = (ROOT / "web" / "styles.css").read_text(encoding="utf-8")
    index_html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
    app_js = (ROOT / "web" / "app.js").read_text(encoding="utf-8")

    assert "min-height: 100vh" in styles
    assert ".workspace-layout" in styles
    assert ".workspace-side" in styles
    assert ".chat-panel" in styles
    assert ".composer" in styles
    assert ".dashboard-grid" in styles
    assert ".table" in styles
    assert "view-scroll" in index_html or "view-scroll" in styles
    assert "function updateWorkspaceControls" in app_js
    assert "function renderWorkspaceContext" in app_js
