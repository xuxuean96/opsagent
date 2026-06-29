let sessionId = localStorage.getItem("ops-agent-session") || "";
let csrfToken = localStorage.getItem("ops-agent-csrf") || "";
let currentProject = localStorage.getItem("ops-agent-current-project") || "";
let currentImplementer = localStorage.getItem("ops-agent-current-implementer") || "";
let currentComponent = localStorage.getItem("ops-agent-current-component") || "";
let lastQuestion = "";
let lastAnswer = "";
let currentUser = null;

const ROLE_VIEWS = {
  admin: ["dashboard", "accounts", "sessions", "admin", "knowledge", "ops", "config", "evaluation", "tasks"],
  reviewer: ["dashboard", "sessions", "admin", "knowledge", "ops", "evaluation", "tasks"],
  implementer: ["workspace", "sessions", "tasks"],
  auditor: ["sessions", "ops", "evaluation", "tasks"],
};

const $ = (id) => document.getElementById(id);
const RECENT_PROJECTS_KEY = "ops-agent-recent-projects";

function jsonBody(payload) {
  return {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload)};
}

function text(value) {
  return String(value ?? "");
}

function formatApiError(status, payload) {
  const detail = payload && payload.detail;
  if (detail && detail.message) return `${detail.message}${detail.hint ? "\n\n" + detail.hint : ""}`;
  if (typeof detail === "string") return `请求失败（${status}）：${detail}`;
  return `请求失败（${status}）`;
}

async function parseJsonSafely(response) {
  try {
    return await response.json();
  } catch {
    return {};
  }
}

async function requestJson(url, options = {}) {
  const method = (options.method || "GET").toUpperCase();
  const headers = new Headers(options.headers || {});
  if (csrfToken && method !== "GET" && !headers.has("x-csrf-token")) headers.set("x-csrf-token", csrfToken);
  options.headers = headers;
  const response = await fetch(url, options);
  const data = await parseJsonSafely(response);
  if (!response.ok) throw new Error(formatApiError(response.status, data));
  if (data.csrf_token) {
    csrfToken = data.csrf_token;
    localStorage.setItem("ops-agent-csrf", csrfToken);
  }
  return data;
}

function visibleViews() {
  if (!currentUser) return [];
  return ROLE_VIEWS[currentUser.role] || ROLE_VIEWS.implementer;
}

function canView(name) {
  return visibleViews().includes(name);
}

function defaultView() {
  return visibleViews()[0] || "workspace";
}

function addMessage(role, body, sources = []) {
  const item = document.createElement("div");
  item.className = `message ${role}`;
  item.textContent = body;
  if (sources.length) {
    const sourceBox = document.createElement("div");
    sourceBox.className = "sources";
    sources.forEach((source, index) => {
      const sourceItem = document.createElement("div");
      sourceItem.className = "source";
      sourceItem.textContent = `[${index + 1}] ${source.title} | ${source.path} | score=${source.score}`;
      sourceBox.appendChild(sourceItem);
    });
    item.appendChild(sourceBox);
  }
  $("messages").appendChild(item);
  $("messages").scrollTop = $("messages").scrollHeight;
  return item;
}

function readRecentProjects() {
  try {
    return JSON.parse(localStorage.getItem(RECENT_PROJECTS_KEY) || "[]").filter(Boolean);
  } catch {
    return [];
  }
}

function writeRecentProjects(projects) {
  localStorage.setItem(RECENT_PROJECTS_KEY, JSON.stringify(projects.slice(0, 8)));
}

function pushRecentProject(project) {
  if (!project) return;
  const projects = [project, ...readRecentProjects().filter((item) => item !== project)];
  writeRecentProjects(projects);
}

function populateProjectSelect() {
  const select = $("project-code");
  if (!select) return;
  const projects = [...new Set([
    ...(currentUser?.projects || []),
    ...readRecentProjects(),
    currentProject,
  ].filter(Boolean))];
  select.innerHTML = [
    '<option value="">请选择项目</option>',
    ...projects.map((project) => `<option value="${project}">${project}</option>`),
    '<option value="__custom__">自定义项目...</option>',
  ].join("");
  if (currentProject && projects.includes(currentProject)) {
    select.value = currentProject;
  } else if (currentProject) {
    select.value = "__custom__";
    $("project-custom").value = currentProject;
  }
  toggleCustomProjectInput();
}

function toggleCustomProjectInput() {
  const select = $("project-code");
  const custom = $("project-custom");
  if (!select || !custom) return;
  const showCustom = select.value === "__custom__";
  custom.hidden = !showCustom;
  custom.required = showCustom;
}

function renderWorkspaceContext() {
  $("current-project-code").textContent = currentProject || "未选择项目";
  $("current-implementer-display").textContent = currentImplementer || "未设置";
  $("current-component-display").textContent = currentComponent || "未设置";
  $("project-implementer").value = currentImplementer || "";
  $("project-component").value = currentComponent || "";
  $("workspace-status").textContent = sessionId
    ? `当前会话已创建，绑定项目 ${currentProject || "未选择"}`
    : currentProject
      ? `已选择项目 ${currentProject}，点击新建会话生效`
      : "请选择项目后新建会话";
  populateProjectSelect();
}

function updateWorkspaceControls() {
  const hasSession = Boolean(sessionId);
  $("message").disabled = !hasSession;
  $("chat-send").disabled = !hasSession;
  $("upload-attachment").disabled = !hasSession;
  $("attachment-file").disabled = !hasSession;
  $("candidate-draft").disabled = !hasSession;
  $("request-admin").disabled = !hasSession;
  document.querySelectorAll(".feedback-btn").forEach((btn) => {
    btn.disabled = !hasSession;
  });
}

function loadWorkspaceState() {
  renderWorkspaceContext();
  updateWorkspaceControls();
}

function switchProject() {
  const select = $("project-code");
  const custom = $("project-custom");
  const selected = select?.value || "";
  const project = selected === "__custom__" ? custom?.value.trim().toUpperCase() : selected.trim().toUpperCase();
  if (!/^[A-Z0-9]{2,16}$/.test(project)) {
    throw new Error("项目必须使用拼音首字母缩写，如 ZJDL");
  }
  currentProject = project;
  currentImplementer = currentUser?.username || currentImplementer || "";
  currentComponent = currentComponent || "";
  localStorage.setItem("ops-agent-current-project", currentProject);
  localStorage.setItem("ops-agent-current-implementer", currentImplementer);
  localStorage.setItem("ops-agent-current-component", currentComponent);
  pushRecentProject(currentProject);
  renderWorkspaceContext();
  updateWorkspaceControls();
  addMessage("assistant", `已选择项目 ${currentProject}，请新建会话后开始提问。`);
}

function showView(name) {
  if (!canView(name)) name = defaultView();
  document.querySelectorAll(".view").forEach((view) => view.classList.remove("active"));
  document.querySelectorAll(".nav-item").forEach((item) => item.classList.remove("active"));
  const view = $(`view-${name}`);
  const nav = document.querySelector(`[data-view="${name}"]`);
  if (!view || !nav) return;
  view.classList.add("active");
  nav.classList.add("active");
  if (name === "workspace") loadTrialEntry();
  if (name === "dashboard") loadDashboard();
  if (name === "sessions") loadSessions(false);
  if (name === "admin") loadAdminCases();
  if (name === "knowledge") loadDrafts();
  if (name === "accounts") loadUsers();
  if (name === "ops") {
    loadAlerts();
    loadJobs();
    loadBackups();
  }
  if (name === "config") loadUsers();
  if (name === "evaluation") loadEvaluationHistory();
  if (name === "tasks") loadTasks();
}

function renderRoleShell() {
  const implementerShell = $("implementer-shell");
  const managementShell = $("management-shell");
  const isImplementer = currentUser && currentUser.role === "implementer";
  implementerShell.hidden = !isImplementer;
  managementShell.hidden = !currentUser || isImplementer;
  loadWorkspaceState();
}

function applyAuthState(user) {
  currentUser = user;
  const authenticated = Boolean(user);
  document.body.classList.toggle("is-authenticated", authenticated);
  document.body.classList.toggle("is-guest", !authenticated);
  $("auth-state").textContent = authenticated ? `已登录：${user.username}（${user.role}）` : "未登录";
  $("current-user").textContent = authenticated ? `${user.username}（${user.role}）` : "未登录";
  document.querySelectorAll(".nav-item").forEach((item) => {
    item.hidden = !authenticated || !canView(item.dataset.view);
  });
  document.querySelectorAll(".view").forEach((view) => view.classList.remove("active"));
  renderRoleShell();
  updateWorkspaceControls();
}

function requireSession() {
  if (!sessionId) throw new Error("请先创建会话");
}

async function login() {
  const data = await requestJson("/api/auth/login", jsonBody({
    username: $("login-username").value.trim(),
    password: $("login-password").value,
  }));
  applyAuthState(data.user);
  await loadStatus();
  showView(defaultView());
}

async function logout() {
  await requestJson("/api/auth/logout", {method: "POST"});
  localStorage.removeItem("ops-agent-session");
  localStorage.removeItem("ops-agent-csrf");
  sessionId = "";
  csrfToken = "";
  currentUser = null;
  applyAuthState(null);
  $("messages").innerHTML = "";
}

async function loadAuthState() {
  try {
    const data = await requestJson("/api/auth/me");
    applyAuthState(data.user);
    await loadStatus();
    showView(defaultView());
  } catch {
    applyAuthState(null);
  }
}

async function loadTrialEntry() {
  try {
    const data = await requestJson("/api/trial/entry");
    $("trial-guide").textContent = data.entry.chat_placeholder;
  } catch (error) {
    $("trial-guide").textContent = error.message;
  }
}

async function loadStatus() {
  try {
    const data = await requestJson("/api/config");
    $("status").innerHTML = `
      <dt>LLM</dt><dd>${data.config.llm.provider} / ${data.config.llm.model}</dd>
      <dt>向量库</dt><dd>${data.config.vector_store.provider}</dd>
      <dt>知识切片</dt><dd>${data.chunks}</dd>
      <dt>当前会话</dt><dd>${sessionId ? "已创建" : "未创建"}</dd>
    `;
    fillConfigForm(data.config);
  } catch (error) {
    $("status").innerHTML = `<dt>服务</dt><dd>不可用</dd><dt>错误</dt><dd>${error.message}</dd>`;
  }
}

function fillConfigForm(config) {
  $("llm-base-url").value = config.llm?.base_url || "";
  $("llm-model").value = config.llm?.model || "";
  $("embedding-provider").value = config.embedding?.provider || "";
  $("embedding-model").value = config.embedding?.model || "";
  $("vector-path").value = config.vector_store?.path || "";
  $("backup-dir").value = config.backup?.dir || "data/backups";
}

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(",")[1] || "");
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

async function loadTasks() {
  try {
    const data = await requestJson("/api/tasks");
    $("task-list").innerHTML = data.tasks.map((task) => `
      <div class="row">
        <div><strong>${task.status}</strong><span>${text(task.question)}${task.error ? " | " + task.error : ""}</span></div>
        <small>${task.updated_at}</small>
      </div>
    `).join("") || "<p>暂无任务。</p>";
  } catch (error) {
    $("task-list").textContent = error.message;
  }
}

async function loadDrafts() {
  try {
    const data = await requestJson("/api/knowledge/drafts");
    $("draft-list").innerHTML = data.drafts.map((item) => `
      <div class="row" data-path="${item.path}">
        <div><strong>${item.title}</strong><span>${item.status} | ${item.path}</span></div>
        <small>${item.modified_at}</small>
      </div>
    `).join("") || "<p>暂无草稿。</p>";
    document.querySelectorAll("#draft-list .row").forEach((row) => {
      row.addEventListener("click", () => $("draft-path").value = row.dataset.path);
    });
  } catch (error) {
    $("draft-list").textContent = error.message;
  }
}

async function reviewDraft(action) {
  try {
    const data = await requestJson(`/api/knowledge/drafts/${action}`, jsonBody({
      draft_path: $("draft-path").value.trim(),
      note: $("review-note").value.trim(),
    }));
    $("knowledge-output").textContent = JSON.stringify(data, null, 2);
    await loadDrafts();
  } catch (error) {
    $("knowledge-output").textContent = error.message;
  }
}

async function loadSessions(pendingOnly) {
  try {
    const summary = await requestJson("/api/sessions/analytics");
    $("feedback-summary").innerHTML = `
      <div class="metric"><span>待反馈</span><strong>${summary.pending_feedback || 0}</strong></div>
      <div class="metric"><span>已解决</span><strong>${summary.resolved || 0}</strong></div>
      <div class="metric"><span>未解决</span><strong>${summary.unresolved || 0}</strong></div>
      <div class="metric"><span>管理员介入</span><strong>${summary.admin_requested || 0}</strong></div>
    `;
    const data = await requestJson(`/api/sessions${pendingOnly ? "?pending_feedback=true" : ""}`);
    $("session-list").innerHTML = data.sessions.map((session) => `
      <div class="row">
        <div><strong>${session.project_code} / ${session.implementer}</strong><span>${session.component || "未填组件"} | ${session.feedback_status} | 介入=${session.admin_requested}</span></div>
        <small>${session.updated_at}</small>
      </div>
    `).join("") || "<p>暂无会话。</p>";
  } catch (error) {
    $("session-list").textContent = error.message;
  }
}

async function loadAdminCases() {
  try {
    const data = await requestJson("/api/admin/cases");
    $("admin-list").innerHTML = data.cases.map((item) => `
      <div class="row" data-id="${item.id}">
        <div><strong>${item.status} | ${item.id}</strong><span>${item.reason}${item.draft_path ? " | 草稿：" + item.draft_path : ""}</span></div>
        <small>${item.updated_at}</small>
      </div>
    `).join("") || "<p>暂无介入单。</p>";
    document.querySelectorAll("#admin-list .row").forEach((row) => row.addEventListener("click", () => $("admin-case-id").value = row.dataset.id));
  } catch (error) {
    $("admin-list").textContent = error.message;
  }
}

async function loadDashboard() {
  await Promise.allSettled([
    loadSessions(false),
    loadAdminCases(),
    loadAlerts(),
    loadJobs(),
  ]);
  $("feedback-summary-dashboard").innerHTML = $("feedback-summary").innerHTML;
  $("admin-list-dashboard").innerHTML = $("admin-list").innerHTML;
  $("alert-list-dashboard").innerHTML = $("alert-list").innerHTML;
  $("job-list-dashboard").innerHTML = $("job-list").innerHTML;
}

async function loadBackups() {
  try {
    const data = await requestJson("/api/backup");
    $("backup-list").innerHTML = data.backups.map((item) => `
      <div class="row"><div><strong>${item.path}</strong><span>${item.bytes} bytes</span></div><small>${item.modified_at}</small></div>
    `).join("") || "<p>暂无备份。</p>";
  } catch (error) {
    $("backup-list").textContent = error.message;
  }
}

async function loadAlerts() {
  try {
    const data = await requestJson("/api/alerts");
    $("alert-list").innerHTML = data.alerts.map((item) => `
      <div class="row alert-${item.severity}">
        <div><strong>${item.severity} | ${item.code}</strong><span>${item.message}${item.source_id ? " | " + item.source_id : ""}</span></div>
        <small>${item.status || "open"}</small>
      </div>
    `).join("") || "<p>暂无告警。</p>";
  } catch (error) {
    $("alert-list").textContent = error.message;
  }
}

async function loadJobs() {
  try {
    const data = await requestJson("/api/jobs");
    $("job-list").innerHTML = data.jobs.map((job) => `
      <div class="row">
        <div><strong>${job.kind} | ${job.status}</strong><span>${job.id}${job.error ? " | " + job.error : ""}</span></div>
        <small>${job.updated_at}</small>
      </div>
    `).join("") || "<p>暂无后台作业。</p>";
  } catch (error) {
    $("job-list").textContent = error.message;
  }
}

async function loadAudit() {
  try {
    const data = await requestJson("/api/audit");
    $("ops-output").textContent = JSON.stringify(data.logs, null, 2);
  } catch (error) {
    $("ops-output").textContent = error.message;
  }
}

async function loadUsers() {
  try {
    const data = await requestJson("/api/users");
    $("user-list").innerHTML = data.users.map((user) => `
      <div class="row" data-username="${user.username}">
        <div><strong>${user.username}</strong><span>${user.role} | ${user.enabled ? "启用" : "禁用"} | ${(user.projects || []).join(", ") || "全部项目"} | ${(user.components || []).join(", ") || "全部组件"}</span></div>
      </div>
    `).join("") || "<p>暂无账号。</p>";
    document.querySelectorAll("#user-list .row").forEach((row) => {
      row.addEventListener("click", () => {
        const user = data.users.find((item) => item.username === row.dataset.username);
        if (!user) return;
        $("account-username").value = user.username;
        $("account-password").value = "";
        $("account-role").value = user.role || "implementer";
        $("account-enabled").checked = Boolean(user.enabled);
        $("account-projects").value = (user.projects || []).join(", ");
        $("account-components").value = (user.components || []).join(", ");
      });
    });
  } catch (error) {
    $("user-list").textContent = error.message;
  }
}

async function saveUser() {
  const payload = {
    username: $("account-username").value.trim(),
    role: $("account-role").value.trim() || null,
    enabled: $("account-enabled").checked,
    projects: $("account-projects").value.split(",").map((item) => item.trim()).filter(Boolean),
    components: $("account-components").value.split(",").map((item) => item.trim()).filter(Boolean),
  };
  if ($("account-password").value.trim()) payload.password = $("account-password").value.trim();
  const data = await requestJson("/api/users", jsonBody(payload));
  $("account-result").textContent = `已保存账号：${data.user.username}`;
  $("account-password").value = "";
  await loadUsers();
}

async function loadEvaluationHistory() {
  try {
    const data = await requestJson("/api/evaluation/history");
    $("eval-output").textContent = JSON.stringify(data.history, null, 2);
    if (data.history[0]) renderEvalSummary(data.history[0]);
  } catch (error) {
    $("eval-output").textContent = error.message;
  }
}

function renderEvalSummary(data) {
  $("eval-summary").innerHTML = `
    <div class="metric"><span>用例数</span><strong>${data.case_count || 0}</strong></div>
    <div class="metric"><span>来源命中</span><strong>${Math.round((data.source_hit_rate || 0) * 100)}%</strong></div>
    <div class="metric"><span>关键词命中</span><strong>${Math.round((data.keyword_hit_rate || 0) * 100)}%</strong></div>
    <div class="metric"><span>兜底率</span><strong>${Math.round((data.fallback_rate || 0) * 100)}%</strong></div>
  `;
}

async function submitJob(kind) {
  const endpoints = {
    reindex: "/api/jobs/reindex",
    governance: "/api/jobs/governance",
    evaluation: "/api/jobs/evaluation",
  };
  const data = await requestJson(endpoints[kind], {method: "POST"});
  $("ops-output").textContent = JSON.stringify(data.job, null, 2);
  await loadJobs();
}

document.querySelectorAll(".nav-item").forEach((btn) => btn.addEventListener("click", () => showView(btn.dataset.view)));

$("login-btn").addEventListener("click", async () => {
  try { await login(); } catch (error) { $("auth-state").textContent = error.message; }
});

$("logout-btn").addEventListener("click", async () => {
  try { await logout(); } catch (error) { $("auth-state").textContent = error.message; }
});

$("refresh-entry").addEventListener("click", loadTrialEntry);

$("project-code").addEventListener("change", toggleCustomProjectInput);

$("switch-project").addEventListener("click", () => {
  try {
    switchProject();
  } catch (error) {
    addMessage("assistant error", error.message);
  }
});

$("start-session").addEventListener("click", async () => {
  try {
    if (!currentProject) switchProject();
    const data = await requestJson("/api/sessions", jsonBody({
      project_code: currentProject,
      implementer: currentImplementer || currentUser?.username || "",
      component: currentComponent || null,
    }));
    sessionId = data.session.id;
    localStorage.setItem("ops-agent-session", sessionId);
    addMessage("assistant", `会话已创建：${data.session.project_code} / ${data.session.implementer}`);
    renderWorkspaceContext();
    updateWorkspaceControls();
    await loadStatus();
  } catch (error) {
    addMessage("assistant error", error.message);
  }
});

$("chat-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = $("message").value.trim();
  if (!message) return;
  try {
    requireSession();
  } catch (error) {
    addMessage("assistant error", error.message);
    return;
  }
  $("message").value = "";
  lastQuestion = message;
  addMessage("user", message);
  const pending = addMessage("assistant", "正在检索知识并调用 LLM 生成回答...");
  try {
    const data = await requestJson("/api/chat", jsonBody({message, session_id: sessionId}));
    pending.remove();
    lastAnswer = data.answer;
    addMessage("assistant", data.answer, data.sources || []);
    await loadTasks();
  } catch (error) {
    pending.remove();
    addMessage("assistant error", error.message);
  }
});

$("upload-attachment").addEventListener("click", async () => {
  try {
    requireSession();
    const file = $("attachment-file").files[0];
    if (!file) throw new Error("请选择要上传的日志或图片");
    const content = await fileToBase64(file);
    const data = await requestJson(`/api/sessions/${sessionId}/attachments`, jsonBody({
      filename: file.name,
      content_type: file.type || "application/octet-stream",
      content_base64: content,
    }));
    addMessage("assistant", `附件已上传，摘要：\n${data.attachment.extracted_text.slice(0, 1200)}`);
  } catch (error) {
    addMessage("assistant error", error.message);
  }
});

document.querySelectorAll(".feedback-btn").forEach((btn) => {
  btn.addEventListener("click", async () => {
    try {
      requireSession();
      await requestJson(`/api/sessions/${sessionId}/feedback`, jsonBody({status: btn.dataset.feedback, note: ""}));
      addMessage("assistant", `已记录反馈：${btn.textContent}`);
    } catch (error) {
      addMessage("assistant error", error.message);
    }
  });
});

$("candidate-draft").addEventListener("click", async () => {
  try {
    requireSession();
    if (!lastQuestion || !lastAnswer) throw new Error("当前会话还没有可沉淀的问答");
    const data = await requestJson(`/api/sessions/${sessionId}/candidate-draft`, jsonBody({question: lastQuestion, answer: lastAnswer}));
    $("draft-path").value = data.draft_path;
    addMessage("assistant", `已生成候选知识草稿：${data.draft_path}`);
  } catch (error) {
    addMessage("assistant error", error.message);
  }
});

$("request-admin").addEventListener("click", async () => {
  try {
    requireSession();
    const reason = $("message").value.trim() || "当前会话多轮排查后仍无法解决，需要管理员介入。";
    const data = await requestJson(`/api/sessions/${sessionId}/admin-request`, jsonBody({reason}));
    addMessage("assistant", `已申请管理员介入，介入单 ID：${data.case.id}`);
  } catch (error) {
    addMessage("assistant error", error.message);
  }
});

$("save-config").addEventListener("click", async () => {
  const payload = {
    llm: {provider: "openai-compatible", base_url: $("llm-base-url").value.trim(), model: $("llm-model").value.trim()},
    embedding: {provider: $("embedding-provider").value.trim(), model: $("embedding-model").value.trim()},
    vector_store: {path: $("vector-path").value.trim()},
    auth: {},
    backup: {dir: $("backup-dir").value.trim()},
  };
  if ($("llm-api-key").value.trim()) payload.llm.api_key = $("llm-api-key").value.trim();
  if ($("admin-password").value.trim()) payload.auth.password = $("admin-password").value.trim();
  if ($("secret-key").value.trim()) payload.auth.secret_key = $("secret-key").value.trim();
  try {
    const data = await requestJson("/api/config", jsonBody(payload));
    $("config-result").textContent = data.message;
  } catch (error) {
    $("config-result").textContent = error.message;
  }
});

$("test-llm").addEventListener("click", async () => {
  try {
    await requestJson("/api/config/test-llm", jsonBody({
      llm: {
        provider: "openai-compatible",
        base_url: $("llm-base-url").value.trim(),
        api_key: $("llm-api-key").value.trim() || undefined,
        model: $("llm-model").value.trim(),
      },
    }));
    $("config-result").textContent = "LLM 连接测试通过。";
  } catch (error) {
    $("config-result").textContent = error.message;
  }
});

$("refresh-drafts").addEventListener("click", loadDrafts);
$("approve-draft").addEventListener("click", () => reviewDraft("approve"));
$("reject-draft").addEventListener("click", () => reviewDraft("reject"));
$("publish-draft").addEventListener("click", async () => {
  try {
    const data = await requestJson("/api/knowledge/publish", jsonBody({
      draft_path: $("draft-path").value.trim(),
      target_dir: $("publish-target").value.trim(),
    }));
    $("knowledge-output").textContent = `已发布到：${data.path}\n索引切片：${data.chunks}\n评测用例：${data.evaluation.case_count}`;
    await loadDrafts();
  } catch (error) {
    $("knowledge-output").textContent = error.message;
  }
});

$("run-governance").addEventListener("click", async () => {
  $("knowledge-output").textContent = "正在生成治理报告...";
  try {
    const data = await requestJson("/api/governance/run", {method: "POST"});
    $("knowledge-output").textContent = JSON.stringify({score: data.score, files: data.file_count, errors: data.error_count, warnings: data.warning_count}, null, 2);
  } catch (error) {
    $("knowledge-output").textContent = error.message;
  }
});

$("reindex").addEventListener("click", () => submitJob("reindex"));
$("run-evaluation").addEventListener("click", () => submitJob("evaluation"));
$("refresh-eval-history").addEventListener("click", loadEvaluationHistory);
$("refresh-sessions").addEventListener("click", () => loadSessions(false));
$("pending-feedback").addEventListener("click", () => loadSessions(true));
$("refresh-sessions-dashboard").addEventListener("click", loadDashboard);
$("refresh-alerts-dashboard").addEventListener("click", loadDashboard);
$("refresh-admin").addEventListener("click", loadAdminCases);
$("refresh-tasks").addEventListener("click", loadTasks);
$("refresh-backups").addEventListener("click", loadBackups);
$("refresh-alerts").addEventListener("click", loadAlerts);
$("refresh-audit").addEventListener("click", loadAudit);
$("refresh-users").addEventListener("click", loadUsers);
$("refresh-jobs").addEventListener("click", loadJobs);

$("save-user").addEventListener("click", async () => {
  try { await saveUser(); } catch (error) { $("account-result").textContent = error.message; }
});

$("resolve-admin").addEventListener("click", async () => {
  try {
    const data = await requestJson(`/api/admin/cases/${$("admin-case-id").value.trim()}/resolve`, jsonBody({
      root_cause: $("admin-root-cause").value.trim(),
      solution: $("admin-solution").value.trim(),
      create_draft: true,
    }));
    $("admin-list").textContent = `已处理，知识草稿：${data.case.draft_path || "未生成"}`;
    await loadAdminCases();
    await loadDrafts();
  } catch (error) {
    $("admin-list").textContent = error.message;
  }
});

$("create-backup").addEventListener("click", async () => {
  try {
    const data = await requestJson("/api/backup/create", jsonBody({backup_dir: $("backup-dir").value.trim() || undefined}));
    $("ops-output").textContent = `备份已创建：${data.path}`;
    await loadBackups();
    await loadAlerts();
  } catch (error) {
    $("ops-output").textContent = error.message;
  }
});

$("verify-backup").addEventListener("click", async () => {
  try {
    const data = await requestJson("/api/backup/verify", jsonBody({archive_path: $("restore-archive").value.trim()}));
    $("ops-output").textContent = JSON.stringify(data, null, 2);
    await loadAlerts();
  } catch (error) {
    $("ops-output").textContent = error.message;
    await loadAlerts();
  }
});

$("restore-backup").addEventListener("click", async () => {
  try {
    const data = await requestJson("/api/backup/restore", jsonBody({archive_path: $("restore-archive").value.trim()}));
    $("ops-output").textContent = `恢复完成：${data.restored.length} 个文件`;
    await loadStatus();
    await loadAlerts();
  } catch (error) {
    $("ops-output").textContent = error.message;
    await loadAlerts();
  }
});

$("storage-check").addEventListener("click", async () => {
  try {
    const data = await requestJson("/api/storage/check");
    $("ops-output").textContent = JSON.stringify(data, null, 2);
  } catch (error) {
    $("ops-output").textContent = error.message;
  }
});

applyAuthState(null);
loadAuthState();
