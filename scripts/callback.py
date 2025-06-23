import requests
import json
import websockets
import asyncio

class Callback:
    """
    A class to handle callback functionality for various endpoints.
    
    This class allows you to send notifications to specified Flask app endpoints
    when certain events occur.
    """

    def __init__(self, host='localhost', port=5011, endpoint='/convertToGLTF'):
        """
        Initializes the Callback instance with a host, port, and endpoint.
        
        Args:
            host (str): The host where the Flask app is running.
            port (int): The port where the Flask app is listening.
            endpoint (str): The initial endpoint for POST requests.
        """
        self._callback = None
        self.location = {"host": host, "port": port}
        self.endpoint = endpoint
        self.base_url = f"http://{self.location['host']}:{self.location['port']}"

    def change_location(self, host, port):
        """
        Change the host and port of the Flask app location.
        
        Args:
            host (str): New host address.
            port (int): New port number.
        """
        self.location = {"host": host, "port": port}
        self.base_url = f"http://{self.location['host']}:{self.location['port']}"

    def set_endpoint(self, endpoint):
        """
        Change the endpoint for POST requests.
        
        Args:
            endpoint (str): The new endpoint to send requests to.
        """
        self.endpoint = endpoint
        self.base_url = f"http://{self.location['host']}:{self.location['port']}"

    def send_message(self, handler, data, endpoint=None):
        """
        Sends a POST request with JSON data to the Flask app.
        
        Args:
            data (dict): The data to send in the POST request.
            
        Returns:
            response (requests.Response): The response object from the Flask app.
        """
        headers = {'Content-Type': 'application/json'}
        response = requests.post(self.base_url + (self.endpoint if endpoint == None else endpoint), headers=headers, data=json.dumps({handler: data}))
        
        # Print the response status and content for debugging
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")

        return response

    def send_message_to(self, handler, data, endpoint, host, port):
        """
        Sends a POST request with JSON data to a specified endpoint.
        
        Args:
            data (dict): The data to send in the POST request.
            endpoint (str): The endpoint to send the request to.
            host (str): The host address to send the request to.
            port (int): The port number to send the request to.
            
        Returns:
            response (requests.Response): The response object from the Flask app.
        """
        headers = {'Content-Type': 'application/json'}
        response = requests.post(f"http://{host}:{port}{endpoint}", headers=headers, data=json.dumps({handler: data}))
        
        # Print the response status and content for debugging
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")

        return response

    def send_message_to_ws(self, handler, data, ws_host='localhost', ws_port=5001):
        """
        Send a WebSocket message to the frontend.
        """
        asyncio.run(self.send_ws_message({handler: data}, ws_host, ws_port))

    async def send_ws_message(self, data, host, port):
        """
        Open a WebSocket connection to the frontend and send the message.
        """
        ws_url = f"ws://{host}:{port}"
        async with websockets.connect(ws_url) as websocket:
            await websocket.send(json.dumps(data))
            print(f"Sent WebSocket message: {data}")

from flask import Flask, jsonify, request
from flask_cors import CORS
import threading
import time
import os
import signal

class PathFlaskApp:
    def __init__(self, *args):
        """
        Initialize the Flask application and string storage.
        """
        self.app = Flask(__name__)
        CORS(self.app, resources={r"/*": {"origins": "*"}})

        self._path = "Initial String"
        self._thread = None
        self._server = None
        self._is_running = False

        self._port = 5001
        if args:
            self._port = args[0]

        @self.app.route('/get_path', methods=['GET'])
        def get_path():
            """
            Endpoint to return the current path.
            """
            print(f"GET request received for path: {self._path}")
            return jsonify({"path": self._path})
        
        @self.app.route('/turn_off', methods=['POST'])
        def turn_off():
            """
            Endpoint to turn off the server.
            """
            self.close()
            return jsonify({"status": "Server turned off"})
        
        @self.app.route('/set_path', methods=['POST'])
        def set_path():
            """
            Endpoint to set the path.
            """
            data = request.get_json()
            new_path = data.get('path')
            self.change_path(new_path)
            print(f"Path changed to: {new_path}")
            return jsonify({"status": "Path changed"})

    def change_path(self, new_path):
        """
        Change the path that is being served by the Flask app.
        
        Args:
            new_path (str): The new path to store.
        """
        self._path = new_path

    def _run_server(self):
        """
        Private method to run the Flask app in a thread.
        """
        self._is_running = True
        self.app.run(port=self._port, use_reloader=False, debug=True)

    def launch(self):
        """
        Launch the Flask server in a separate thread.
        """
        if not self._is_running:
            self._thread = threading.Thread(target=self._run_server)
            self._thread.start()
            time.sleep(1)  # Wait a second to ensure the server is up

    def close(self):
        """
        Close the Flask server by sending a SIGINT (same as Ctrl+C).
        """
        if self._is_running:
            os.kill(os.getpid(), signal.SIGINT)  # Send interrupt signal to the current process
            self._thread.join()
            self._is_running = False

# # Example usage
# Callback().send_message_to_ws("path", "D:\\RecordingsUE\\glb\\BEETJE.glb", "localhost", 5001)
# server = PathFlaskApp()
# server.launch()  # Launch the Flask server

# time.sleep(2)
# server.change_path("D:\\RecordingsUE\\glb\\BEETJE.glb")


# # Example usage
# if __name__ == "__main__":
#     # Create an instance of Callback
#     notifier = Callback(host='localhost', port=5000, endpoint='/exportCompleted')
    
#     # Send an export completed message
#     notifier.send_message({"handler": "exportCompleted"})
    
#     # Change endpoint and send a message
#     notifier.set_endpoint('/anotherEndpoint')
#     notifier.send_message({"handler": "anotherAction"})
    
#     # Change the Flask app location and endpoint, then send a message
#     notifier.change_location('localhost', 6000)
#     notifier.set_endpoint('/newEndpoint')
#     notifier.send_message({"handler": "newAction"})
