# UE Take Recorder Control
This project provides a simple interface to control the Take Recorder within Unreal Engine for live recordings of motion capture data. It allows users to start and stop recordings programmatically, facilitating control over the Take Recorder through a TCP setup.

## Requirements
- Unreal Engine 
- Python integration enabled in Unreal Engine (we are using a vscode plugin https://marketplace.visualstudio.com/items?itemName=NilsSoderman.ue-python)

## Usage
- Set the actor to be recorded in the takerecorder within Unreal Engine.
- Either run the script on startup through Unreal Engine's Python integration or use the VSCode Plugin.
- Communicate with the websocket with the following messages: "startRecord", "broadcastGlos", "ping", "stopRecord", "fbxExport", "replayRecord", "exportLevelSequenceName", "isRecording", "close".

Here are some examples on how to communicate using Javascript:
```
  function startCapture() {
    sendMessage(JSON.stringify({ handler: "startCapture", data: "startCapture" }));
  }

  function stopCapture() {
    sendMessage(JSON.stringify({ handler: "stopCapture", data: "stopCapture" }));
  }

  function exportLevelSequenceName() {
    sendMessage(JSON.stringify({ handler: "exportLevelSequenceName", data: "exportLevelSequenceName" }));
  }

  function broadcastGlos(glosText) {
    sendMessage(JSON.stringify({ data: "broadcastGlos", glos: glosText }));
  }
  function isRecording() {
    sendMessage(JSON.stringify({ handler: "isRecording", data: "isRecording" }));
  }
```

## Why hook into the tick?
In Unreal Engine, manyAPI calls, especially those related to the game world, UI updates, and editor functions, must be called from the main thread. This makes it difficult to use a waiting/listening Python program. If we let the socket listen and wait on the main thread, the entire engine stalls. The workaround: in Unreal Engine Python scripting, especially in editor contexts, hooking into the tick method (such as using register_slate_post_tick_callback) is a common approach for executing continuous or periodic tasks.
Creating a new Python thread to handle functionality might seem like a simpler solution, but it poses several issues in the Unreal Engine environment:
- Thread safety: Unreal Engine is not thread-safe by default. Many of its APIs cannot be called safely from a separate thread. This includes accessing game objects, modifying the world, and interacting with the editor UI.
- Blocking operations: If you use blocking calls (e.g., waiting for a network response) on the main thread, it would freeze the UI and the entire editor/game. Conversely, if you use a new thread for non-blocking operations, you still need a way to synchronize the results back to the main thread.


## TODO:
- When running the python file multiple times, multiple instances are opened in UE.
