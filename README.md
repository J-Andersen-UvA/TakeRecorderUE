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

## TODO:
- Currently export paths are hardcoded.
- When running the python file multiple times, multiple instances are opened in UE.
