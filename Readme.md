# Take Recorder Integration for Unreal Engine

A Python-driven toolset that automates the capture, export, and upload of in-editor animation “takes” in Unreal Engine.  

---

## Overview

When you hit **Record**, our Python app hooks into Unreal’s **Tick** loop to:
1. Drive the in-editor take recorder  
2. Track each take’s life-cycle via a state machine  
3. Export the recorded animation to FBX  
4. Fire off an HTTP upload in the background  
5. Confirm completion back to Unreal via WebSocket  

This lets you record, export, and upload animations—all from inside the Unreal Editor—with zero manual file handling.

---

## Technical Highlights

- **Unreal Tick Hook**  
  We register a Python callback on every engine tick. That drives our state machine, which advances through `RECORDING → EXPORT_FBX → UPLOAD → IDLE`.

- **State Machine**  
  A central `StateManager` enumerates and enforces valid transitions (e.g. you can’t start a new take while an export is in‐flight).

- **Asynchronous Uploads**  
  Exports happen synchronously in Unreal, but uploads are spun off on a background thread—so your editor never stalls waiting on network I/O.

---

## Module Breakdown

- **`recorder.py`**  
  Entrypoint & orchestration (hooks into Tick, advances the state machine)  
- **`takeRecorder.py`**  
  Low-level recording logic (start/stop takes, manage subscenes)  
- **`stateManagerScript.py`**  
  Central state machine & status enum (`IDLE`, `RECORDING`, `EXPORT_FBX`, `UPLOAD`, etc.)  
- **`exportAndSend.py`**  
  FBX export wrapper + background HTTP uploader  
- **`wsCommunicationScript.py`**  
  WebSocket client for in-editor callbacks  
- **`editorFuncs.py`**, **`popUp.py`**  
  Unreal Editor utilities (menu hooks, pop-ups)  
- **`extraFuncs.py`**  
  Miscellaneous helpers (e.g. toggling the torch light)  
- **`config.yaml`** / **`params.py`**  
  YAML-based configuration loader (endpoints, paths, flags)  

---

## Getting Started

1. Place the **`scripts/`** folder alongside your Unreal project’s Plugins or Content directory.  
2. Edit **`scripts/config/config.yaml`** to set your export endpoint and other options.  
3. Launch the Unreal Editor—use a plugin to execute the recorder.py script or set as the main execution point in Unreal Engine to make it execute on start up.
4. Start, stop and export the recording using your webserver.  

Happy recording!  
