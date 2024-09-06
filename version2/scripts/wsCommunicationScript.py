import sys
import json
import requests
import websocket
import time
import threading
import ssl
import scripts.stateManagerScript as stateManagerScript

stateManager = stateManagerScript.StateManager()

class websocketCommunication:
    _instance = None  # Class-level variable to store the singleton instance

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(websocketCommunication, cls).__new__(cls)
        return cls._instance

    def __init__(self, host, takeRecorder):
        if not hasattr(self, 'initialized'):  # Initialize once
            self.host = host  # Store the host for later use
            self.tk = takeRecorder
            self.ws = None  # Initialize with no WebSocket connection
            self.thread = None  # Track the thread for the WebSocket

            # Ensure previous WebSocket connection is closed before starting a new one
            self.close_connection()  # Close any existing connection
            self.open_connection()   # Open a new connection

    def close_connection(self):
        """
        Closes the WebSocket connection if it is open.
        """
        if self.ws is not None and self.ws.sock and self.ws.sock.connected:
            print("Closing existing WebSocket connection...")
            self.ws.close()
            self.thread.join()  # Wait for the WebSocket thread to close cleanly
        else:
            print("No active WebSocket connection to close.")

    def open_connection(self):
        """
        Opens a new WebSocket connection.
        """
        print(f"Opening WebSocket connection to {self.host}...")
        retries = 3  # Number of times to retry connecting
        for attempt in range(retries):
            try:
                self.ws = websocket.WebSocketApp(
                    self.host,
                    on_message=self.on_message,
                    on_close=self.on_close,
                    on_open=self.on_open,
                    on_error=self.on_error,  # Add on_error handler
                    on_ping=self.on_ping    # Add on_ping handler
                )
                self.thread = threading.Thread(
                    target=self.ws.run_forever,
                    kwargs={"sslopt": {"cert_reqs": ssl.CERT_NONE}}
                )
                self.thread.start()
                print("WebSocket connection thread started.")
                break  # Exit loop if connection is successful
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                time.sleep(2 ** attempt)  # Exponential backoff
        else:
            print("Failed to open WebSocket connection after multiple attempts.")

    def setStatus(value=None):
        stateManager.set_recording_status(value)
        return stateManager.get_recording_status()

    def send_fbx_to_url(self, file_path, avatar_name="glassesGuy"):
        """
        Synchronously send a file to a URL.

        Parameters:
        - file_path (str): File path of the file to send.

        Prints the response from the server after sending the file.
        """
        print("Sending file...")
        with open(file_path, "rb") as file:
            files = {"file": (file_path, file, "multipart/form-data")}
            response = requests.post(
                "https://leffe.science.uva.nl:8043/fbx2glb/upload/",
                files=files,
                verify=False  # Skips SSL verification.
            )

            ws_JSON = {
                "handler": "fbxExportNameConfirmed",
                "glosName": stateManager.get_gloss_name(),
                "avatarName": avatar_name
            }
            self.ws.send(json.dumps(ws_JSON))

    def on_error(self, ws, error):
        print(f"WebSocket error: {error}")

    def on_ping(self, ws, message):
        print(f"Received ping: {message}")

    def on_open(self, ws):
        """
        Called when the WebSocket connection is opened.
        """
        print("WebSocket connection opened. Sending initial request...")
        ws_JSON = {"handler": "requestGlos"}
        self.ws.send(json.dumps(ws_JSON))

    def on_close(self, ws, close_status_code, close_msg):
        print("### CLOSED AND KILLED PYTHON PROCESS ###")
        sys.exit()

    def on_message(self, ws, message):
        message = json.loads(message)

        # Setting the status of the recorder lets the unreal tik function know what to do
        if message["set"] == "startRecord":
            print(self.setStatus(stateManagerScript.Status.START))
        
        if message["set"] == "broadcastGlos":
            print(stateManager.set_gloss_name(message["handler"]))
            ws_JSON = {
                "handler": "broadcastGlosConfirmed",
                "glosName": stateManager.get_gloss_name()
            }
            self.ws.send(json.dumps(ws_JSON))
            
        if message["set"] == "ping":
            ws_JSON = {
                "handler": "pong",
            }
            self.ws.send(json.dumps(ws_JSON))
            
        if message["set"] == "stopRecord":
            print(self.setStatus(stateManagerScript.Status.STOP))

        if message["set"] == "fbxExport":
            print(self.setStatus(stateManagerScript.Status.FBX_EXPORT))

        if message["set"] == "replayRecord":
            print(self.setStatus(stateManagerScript.Status.REPLAY_RECORD))

        if message["set"] == "exportLevelSequenceName":
            print(self.setStatus(stateManagerScript.Status.EXPORT_FBX))

        # TODO: I never see this message called, and therefore I have not made a status for it.
        if message["set"] == "fbxExportName":
            print(self.setStatus("fbxExportName"))
            stateManager.set_gloss_name(message["glosName"])
            stateManager.set_level_sequence_name(message["data"])
            ws_JSON = {
                "data": "fbxExportNameConfirmed",
                "glosName": stateManager.get_gloss_name(),
            }

            self.ws.send(json.dumps(ws_JSON))

        if message["set"] == "isRecording":
            print(self.setStatus("recording"))
            ws_JSON = {
                "handler": "isRecordingConfirmed",
                "isRecording": self.tk.is_recording()
            }
            self.ws.send(json.dumps(ws_JSON))
