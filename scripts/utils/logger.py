# logger.py
from __future__ import annotations
import os, json, datetime, re
import socket
from typing import Dict, List, Any, Optional
import threading
_METADATA_LOCK = threading.Lock()
from scripts.export.endpointSender import send

LOG_DIR = r"D:\MOCAP\Recordings\Logs"   # local
LOG_FILE = "recordings.jsonl"

def _utc_now_iso():
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def _new_recording_id():
    return _utc_now_iso().replace(":", "-")

def _ensure_dir(p: str):
    os.makedirs(p, exist_ok=True)

def _basename_no_ext(p: str) -> str:
    return os.path.splitext(os.path.basename(p))[0]

def guess_gloss_from_filename(name: str) -> str:
    base = _basename_no_ext(name)
    base = re.sub(r"_actor\d+_markers$", "", base, flags=re.IGNORECASE)
    return base

def guess_gloss_from_filename_csv(path: str):
    base = os.path.basename(path)
    name, _ = os.path.splitext(base)

    # ActivePhone.csv -> gloss is before "_ActivePhone"
    if "_ActivePhone" in name:
        return name.split("_ActivePhone")[0]

    # Device_xxx => gloss is before "_Device_"
    if "_Device_" in name:
        return name.split("_Device_")[0]

    # fallback: first chunk
    return name.split("_")[0]


class RecordingLog:
    """Single-line-per-recording JSONL writer (replace-latest)."""
    def __init__(self, log_dir: str = LOG_DIR, filename: str = LOG_FILE):
        self.log_dir = os.path.abspath(log_dir)
        _ensure_dir(self.log_dir)
        self.log_path = os.path.join(self.log_dir, filename)
        if not os.path.exists(self.log_path):
            open(self.log_path, "w", encoding="utf-8").close()

    # ---------- read/scan ----------
    def _read_all(self) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        with open(self.log_path, "r", encoding="utf-8") as f:
            for raw in f:
                s = raw.strip()
                if not s:
                    continue
                try:
                    out.append(json.loads(s))
                except json.JSONDecodeError:
                    # try to split glued entries defensively
                    for part in s.replace("}{", "}\n{").splitlines():
                        part = part.strip()
                        if not part:
                            continue
                        try:
                            out.append(json.loads(part))
                        except json.JSONDecodeError:
                            pass
        return out

    def _write_all(self, records: List[Dict[str, Any]]) -> None:
        tmp = self.log_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        os.replace(tmp, self.log_path)

    # ---------- core ops ----------
    def _append_or_replace_latest(self, obj: Dict[str, Any]) -> None:
        rid = obj.get("recording_id")
        lines = self._read_all()

        obj = dict(obj)
        obj["updated_at"] = _utc_now_iso()
        if "created_at" not in obj:
            obj["created_at"] = obj["updated_at"]

        if not rid:
            # append safely (newline guard)
            need_leading_nl = False
            try:
                if os.path.getsize(self.log_path) > 0:
                    with open(self.log_path, "rb") as rf:
                        rf.seek(-1, os.SEEK_END)
                        need_leading_nl = rf.read(1) != b"\n"
            except Exception:
                pass
            with open(self.log_path, "a", encoding="utf-8") as f:
                if need_leading_nl:
                    f.write("\n")
                f.write(json.dumps(obj, ensure_ascii=False) + "\n")
            return

        last_idx = -1
        for i, r in enumerate(lines):
            if isinstance(r, dict) and r.get("recording_id") == rid:
                last_idx = i

        if last_idx >= 0:
            lines[last_idx] = obj
            self._write_all(lines)
        else:
            # append if not found
            need_leading_nl = False
            try:
                if os.path.getsize(self.log_path) > 0:
                    with open(self.log_path, "rb") as rf:
                        rf.seek(-1, os.SEEK_END)
                        need_leading_nl = rf.read(1) != b"\n"
            except Exception:
                pass
            with open(self.log_path, "a", encoding="utf-8") as f:
                if need_leading_nl:
                    f.write("\n")
                f.write(json.dumps(obj, ensure_ascii=False) + "\n")

    def _assets_empty(self) -> Dict[str, List[Dict[str, Any]]]:
        return {
            "blendshape_csv": [],
            "retargeted_animation_fbx": [],
            "original_mocap_mcp": [],
            "video_mkv": [],
            "original_animation_fbx": [],
            "mocap_marker_csv": [],
        }

    def _upsert_by_gloss(self, gloss: str) -> Dict[str, Any]:
        # Find latest by gloss (scan from end)
        recs = self._read_all()
        for rec in reversed(recs):
            if rec.get("gloss") == gloss:
                return rec
        # create minimal record
        rid = _new_recording_id()
        now = _utc_now_iso()
        return {
            "version": "1.0",
            "recording_id": rid,
            "gloss": gloss,
            "capture_start": now,
            "capture_end": None,
            "assets": self._assets_empty(),
            "created_at": now,
            "updated_at": now,
        }

    def add_asset(self, gloss_or_path: str, asset_type: str, path: str, machine="UE",
                  status="ready", mtime: Optional[str] = None) -> Dict[str, Any]:
        gloss = guess_gloss_from_filename(gloss_or_path)
        rec = self._upsert_by_gloss(gloss)

        if "assets" not in rec or not isinstance(rec["assets"], dict):
            rec["assets"] = self._assets_empty()
        if asset_type not in rec["assets"]:
            rec["assets"][asset_type] = []

        abspath = os.path.abspath(path)
        for it in rec["assets"][asset_type]:
            existing = it.get("path")
            if existing and os.path.abspath(existing) == abspath:
                it["status"]  = status or it.get("status", "ready")
                it["mtime"]   = mtime or it.get("mtime") or _utc_now_iso()
                it["machine"] = machine or it.get("machine")
                self._append_or_replace_latest(rec)
                return rec

        rec["assets"][asset_type].append({
            "path": abspath,
            "machine": machine,
            "status": status,
            "mtime": mtime or _utc_now_iso(),
            "quality": {},
        })
        self._append_or_replace_latest(rec)
        return rec

class RecordingLogSingleAnim:
    def __init__(self):
        pass

    @staticmethod
    def _isoformat_utc(ts: float) -> str:
        return datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    @staticmethod
    def _find_metadata_json(file_path: str) -> str:
        unreal_dir = os.path.dirname(file_path)
        anim_dir = os.path.dirname(unreal_dir)  # up from Unreal/
        metadata_dir = os.path.join(anim_dir, "metadata")

        if not os.path.isdir(metadata_dir):
            raise FileNotFoundError(f"Metadata folder not found: {metadata_dir}")

        json_files = [f for f in os.listdir(metadata_dir) if f.lower().endswith(".json")]
        if not json_files:
            raise FileNotFoundError(f"No metadata JSON in: {metadata_dir}")
        # pick the first (or latest if you prefer)
        json_files.sort(key=lambda f: os.path.getmtime(os.path.join(metadata_dir, f)), reverse=True)
        return os.path.join(metadata_dir, json_files[0])

    @staticmethod
    def _update_metadata(file_path: str, machine: str):
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".csv":
            asset_key = "blendshape_csv"
        elif ext == ".fbx":
            asset_key = "retargeted_animation_fbx"
        else:
            return  # ignore unsupported

        metadata_json_path = RecordingLogSingleAnim._find_metadata_json(file_path)
        metadata_dir = os.path.dirname(metadata_json_path)

        rel_path = os.path.relpath(file_path, start=metadata_dir).replace("\\", "/")
        mtime = os.path.getmtime(file_path)
        entry = {
            "path": rel_path,
            "machine": machine or socket.gethostname(),
            "status": "ready",
            "mtime": RecordingLogSingleAnim._isoformat_utc(mtime),
            "quality": {}
        }

        # Lock that helps with our own threads
        with _METADATA_LOCK:
            # Retry logic for file access, in case another process is writing on main machine (we cannot circumvent that with METADATA_LOCK)
            for attempt in range(5):
                try:
                    with open(metadata_json_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    break
                except (IOError, json.JSONDecodeError):
                    if attempt == 4:
                        # last attempt: fallback to new file
                        fallback_path = os.path.join(
                            failed_dir,
                            f"failed_read_{int(time.time())}.json"
                        )
                        with open(fallback_path, "w", encoding="utf-8") as ff:
                            json.dump(entry, ff, indent=2)
                        print(f"[Exporter] FAILED to read metadata, wrote fallback: {fallback_path}")
                        return
                    else:
                        import time
                        time.sleep(0.3)

        items = data.setdefault("assets", {}).setdefault(asset_key, [])
        for i, it in enumerate(items):
            if isinstance(it, dict) and it.get("path") == entry["path"]:
                items[i] = entry
                break
        else:
            items.append(entry)

        data["updated_at"] = datetime.datetime.now(tz=datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # atomic write
        tmp = metadata_json_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        os.replace(tmp, metadata_json_path)

        print(f"Updated metadata: {metadata_json_path}")
        send(data)
