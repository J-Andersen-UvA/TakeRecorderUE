import ctypes
import json
import os
import time
from collections import Counter

import unreal


LOG_DIR = r"D:\MOCAP\Recordings\Logs"
LOG_FILE = "take_recorder_diagnostics.jsonl"

TRACKED_CLASSES = {
    "AnimSequence",
    "LevelSequence",
    "MovieScene",
    "MovieSceneSubSection",
    "MovieSceneSubTrack",
    "TakeMetaData",
    "TakeRecorder",
    "TakeRecorderSources",
    "TakeRecorderActorSource",
    "AssetExportTask",
    "AnimSequenceExporterFBX",
    "FbxExportOption",
    "Package",
}


class _PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
    _fields_ = [
        ("cb", ctypes.c_ulong),
        ("PageFaultCount", ctypes.c_ulong),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
        ("PrivateUsage", ctypes.c_size_t),
    ]


def _now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _memory_snapshot():
    try:
        counters = _PROCESS_MEMORY_COUNTERS_EX()
        counters.cb = ctypes.sizeof(counters)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        kernel32.GetCurrentProcess.restype = ctypes.c_void_p
        psapi.GetProcessMemoryInfo.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(_PROCESS_MEMORY_COUNTERS_EX),
            ctypes.c_ulong,
        ]
        psapi.GetProcessMemoryInfo.restype = ctypes.c_int

        handle = kernel32.GetCurrentProcess()
        ok = psapi.GetProcessMemoryInfo(
            handle,
            ctypes.byref(counters),
            counters.cb,
        )
        if not ok:
            return {"error": f"GetProcessMemoryInfo failed: {ctypes.get_last_error()}"}

        return {
            "working_set_mb": round(counters.WorkingSetSize / 1024 / 1024, 2),
            "private_mb": round(counters.PrivateUsage / 1024 / 1024, 2),
            "pagefile_mb": round(counters.PagefileUsage / 1024 / 1024, 2),
            "peak_working_set_mb": round(counters.PeakWorkingSetSize / 1024 / 1024, 2),
        }
    except Exception as e:
        return {"error": str(e)}


def _object_snapshot():
    if not hasattr(unreal, "ObjectIterator"):
        return {"error": "unreal.ObjectIterator is not available"}

    total = 0
    tracked = Counter()
    loaded_recorded_animations = []

    try:
        try:
            iterator = unreal.ObjectIterator()
        except TypeError:
            iterator = unreal.ObjectIterator(unreal.Object)

        for obj in iterator:
            total += 1
            try:
                class_name = obj.get_class().get_name()
            except Exception:
                class_name = type(obj).__name__

            if class_name in TRACKED_CLASSES:
                tracked[class_name] += 1

            if class_name == "AnimSequence":
                try:
                    path = obj.get_path_name()
                except Exception:
                    path = ""
                if "/Game/Cinematics/Takes/" in path and "/Animation/" in path:
                    loaded_recorded_animations.append(path)

        loaded_recorded_animations.sort()
        return {
            "total_uobjects": total,
            "tracked_counts": dict(sorted(tracked.items())),
            "loaded_recorded_animation_count": len(loaded_recorded_animations),
            "loaded_recorded_animation_samples": loaded_recorded_animations[-12:],
        }
    except Exception as e:
        return {"error": str(e)}


class DiagnosticsLogger:
    def __init__(self, enabled=True, log_dir=LOG_DIR, filename=LOG_FILE):
        self.enabled = enabled
        self.log_dir = log_dir
        self.log_path = os.path.join(log_dir, filename)
        self.session_id = time.strftime("%Y%m%d-%H%M%S", time.localtime())

        if self.enabled:
            os.makedirs(self.log_dir, exist_ok=True)
            unreal.log(f"[Diagnostics] Writing Take Recorder diagnostics to: {self.log_path}")

    def sample(self, label, state=None, gloss=None, extra=None):
        if not self.enabled:
            return

        entry = {
            "time": _now_iso(),
            "session_id": self.session_id,
            "label": label,
            "state": str(state) if state is not None else None,
            "gloss": gloss,
            "memory": _memory_snapshot(),
            "objects": _object_snapshot(),
            "extra": extra or {},
        }

        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
        except Exception as e:
            unreal.log_warning(f"[Diagnostics] Failed to write diagnostics sample '{label}': {e}")
