from __future__ import annotations

import json
import subprocess
from pathlib import Path


def test_filter_sessions_matches_core_fields(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    script = """
const { filterSessions } = require('./web/session-helpers.js');
const sessions = [
  { id: '1', project_code: 'ZJDL', implementer: '张三', component: 'DDB', feedback_status: 'resolved', updated_at: '2026-06-29T10:00:00' },
  { id: '2', project_code: 'HNDL', implementer: '李四', component: 'KMVue', feedback_status: 'pending_feedback', updated_at: '2026-06-29T11:00:00' },
];
process.stdout.write(JSON.stringify(filterSessions(sessions, 'kmvue')));
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == [
        {"id": "2", "project_code": "HNDL", "implementer": "李四", "component": "KMVue", "feedback_status": "pending_feedback", "updated_at": "2026-06-29T11:00:00"}
    ]
