from __future__ import annotations

import hashlib
import json
import sqlite3
import zipfile
from datetime import datetime, timezone
from pathlib import Path


MANIFEST_NAME = "backup-manifest.json"


def create_backup(workspace_root: str | Path, backup_dir: str | Path) -> str:
    root = Path(workspace_root).resolve()
    target_dir = Path(backup_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    archive = target_dir / f"ops-agent-backup-{stamp}.zip"
    manifest: dict[str, dict[str, str | int]] = {}
    items = [
        root / "config" / "app.yaml",
        root / "data",
        root / "knowledge-base" / "13-待审核",
    ]
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for item in items:
            if not item.exists():
                continue
            paths = [item] if item.is_file() else [path for path in item.rglob("*") if path.is_file()]
            for path in paths:
                arcname = path.relative_to(root).as_posix()
                data = path.read_bytes()
                zf.write(path, arcname)
                manifest[arcname] = {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
        zf.writestr(
            MANIFEST_NAME,
            json.dumps({"created_at": datetime.now(timezone.utc).isoformat(), "files": manifest}, ensure_ascii=False, indent=2),
        )
    return archive.as_posix()


def list_backups(backup_dir: str | Path) -> list[dict]:
    root = Path(backup_dir)
    root.mkdir(parents=True, exist_ok=True)
    backups = []
    for path in sorted(root.glob("*.zip"), reverse=True):
        stat = path.stat()
        backups.append({"path": path.as_posix(), "bytes": stat.st_size, "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()})
    return backups


def prune_backups(backup_dir: str | Path, retention_count: int) -> list[str]:
    if retention_count <= 0:
        return []
    backups = sorted(Path(backup_dir).glob("*.zip"), key=lambda item: item.stat().st_mtime, reverse=True)
    removed = []
    for path in backups[retention_count:]:
        path.unlink(missing_ok=True)
        removed.append(path.as_posix())
    return removed


def verify_backup(archive_path: str | Path) -> dict:
    archive = Path(archive_path)
    if not archive.exists():
        raise FileNotFoundError(f"Backup not found: {archive}")
    with zipfile.ZipFile(archive, "r") as zf:
        try:
            manifest = json.loads(zf.read(MANIFEST_NAME).decode("utf-8"))
        except KeyError as exc:
            raise ValueError("Backup manifest missing") from exc
        mismatches = []
        for name, expected in manifest.get("files", {}).items():
            data = zf.read(name)
            digest = hashlib.sha256(data).hexdigest()
            if digest != expected.get("sha256") or len(data) != expected.get("bytes"):
                mismatches.append(name)
    return {"ok": not mismatches, "file_count": len(manifest.get("files", {})), "mismatches": mismatches}


def restore_backup(archive_path: str | Path, workspace_root: str | Path) -> list[str]:
    archive = Path(archive_path)
    if not archive.exists():
        raise FileNotFoundError(f"Backup not found: {archive}")
    root = Path(workspace_root).resolve()
    extracted: list[str] = []
    with zipfile.ZipFile(archive, "r") as zf:
        for member in zf.infolist():
            if member.filename == MANIFEST_NAME:
                continue
            destination = (root / member.filename).resolve()
            if root not in destination.parents and destination != root:
                raise ValueError(f"Unsafe backup entry: {member.filename}")
            extracted.append(destination.as_posix())
        zf.extractall(root, members=[item for item in zf.infolist() if item.filename != MANIFEST_NAME])
    return extracted


def sqlite_integrity_check(path: str | Path) -> dict:
    db_path = Path(path)
    if not db_path.exists():
        return {"ok": False, "path": db_path.as_posix(), "message": "SQLite 文件不存在。"}
    with sqlite3.connect(db_path) as conn:
        result = conn.execute("pragma integrity_check").fetchone()
    message = result[0] if result else "unknown"
    return {"ok": message == "ok", "path": db_path.as_posix(), "message": message}
