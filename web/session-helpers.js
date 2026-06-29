function normalize(value) {
  return String(value ?? "").trim().toLowerCase();
}

function filterSessions(sessions, term) {
  const query = normalize(term);
  if (!query) return sessions.slice();
  return sessions.filter((session) => {
    return [session.id, session.project_code, session.implementer, session.component, session.feedback_status, session.updated_at]
      .filter(Boolean)
      .some((value) => normalize(value).includes(query));
  });
}

if (typeof module !== "undefined") {
  module.exports = { filterSessions };
}

if (typeof window !== "undefined") {
  window.filterSessions = filterSessions;
}
